import re
import math
import requests
import time

import numpy as np
from collections import Counter
from difflib import SequenceMatcher

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Variable global para el indexador
_indexador_global = None

def set_indexador(indexador):
    global _indexador_global
    _indexador_global = indexador


def calcular_similitud_textual(texto1, texto2):
    if not texto1 or not texto2:
        return 0
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()


def buscar_canciones_avanzado(query, min_score=5, modo="auto"):
    global _indexador_global
    
    if not query.strip():
        return []
    
    query = query.lower().strip()
    resultados = []
    
    # ===== 1. PREPROCESAMIENTO DE LA QUERY =====
    palabras_query = set(query.split())
    query_len = len(palabras_query)
    
    # Determinar automáticamente el tipo de query
    es_query_semantica = False
    if modo == "auto":
        # Heurísticas para identificar query semántica
        palabras_semanticas = {'canciones', 'temas', 'sobre', 'about',
                               'songs', 'de', 'acerca'}
        
        es_query_semantica = (
            len(palabras_semanticas & palabras_query) > 1
        )
    elif modo == "semantico":
        es_query_semantica = True
    else:  # modo == "lexico"
        es_query_semantica = False
    
    # ===== 2. CÁLCULO DE EMBEDDINGS SEMÁNTICOS =====
    semantic_scores = {}
    query_vec = None
    
    if _indexador_global and getattr(_indexador_global, 'document_embeddings', None) is not None:
        query_vec = _indexador_global.obtener_embedding(query)
        if query_vec is not None:
            # Búsqueda semántica vectorial
            for idx, doc_id in enumerate(_indexador_global.document_ids_order or _indexador_global.documentos.keys()):
                if idx < len(_indexador_global.document_embeddings):
                    # Similitud coseno (valores entre -1 y 1, normalmente 0-1 para textos)
                    similarity = float(np.dot(_indexador_global.document_embeddings[idx], query_vec))
                    # Normalizar a [0, 1] si es necesario (valores negativos son raros en este contexto)
                    semantic_scores[doc_id] = max(0.0, similarity)
    
    # ===== 3. PREPARAR MÉTRICAS GLOBALES PARA BM25 =====
    if _indexador_global:
        doc_lengths = [len(doc['letra'].split()) + len(doc['titulo'].split()) + len(doc['artista'].split()) 
                       for doc in _indexador_global.documentos.values()]
        avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 100
    
    # ===== 4. ITERAR SOBRE DOCUMENTOS =====
    for doc_id, cancion in (_indexador_global.documentos.items() if _indexador_global else info_completa.items()):
        # Inicializar scores
        score_lexico = 0.0
        score_semantico = semantic_scores.get(doc_id, 0.0)
        razones_lexico = []
        razones_semantico = []
        
        titulo_lower = cancion['titulo'].lower()
        artista_lower = cancion['artista'].lower()
        
        # ===== 4.1 PUNTUACIÓN LÉXICA =====
        
        # a) Coincidencia exacta de la consulta completa (máxima relevancia)
        if query == titulo_lower:
            score_lexico += 15.0
            razones_lexico.append("título exacto (+15)")
        elif query == artista_lower:
            score_lexico += 12.0
            razones_lexico.append("artista exacto (+12)")
        # Frase completa en título (sin ser exacta)
        elif query in titulo_lower:
            score_lexico += 8.0
            razones_lexico.append("frase en título (+8)")
        elif query in artista_lower:
            score_lexico += 6.0
            razones_lexico.append("frase en artista (+6)")
        
        # b) Jaccard similarity para título (mejor que contar coincidencias)
        palabras_titulo = set(titulo_lower.split())
        if palabras_query and palabras_titulo:
            interseccion = len(palabras_query & palabras_titulo)
            union = len(palabras_query | palabras_titulo)
            jaccard_titulo = interseccion / union if union > 0 else 0
            
            if jaccard_titulo > 0:
                puntaje_jaccard = jaccard_titulo * 8.0
                score_lexico += puntaje_jaccard
                if jaccard_titulo > 0.3:
                    razones_lexico.append(f"título (Jaccard={jaccard_titulo:.2f}, +{puntaje_jaccard:.1f})")
        
        # c) Jaccard similarity para artista
        palabras_artista = set(artista_lower.split())
        if palabras_query and palabras_artista:
            interseccion = len(palabras_query & palabras_artista)
            union = len(palabras_query | palabras_artista)
            jaccard_artista = interseccion / union if union > 0 else 0
            
            if jaccard_artista > 0:
                puntaje_jaccard = jaccard_artista * 6.0
                score_lexico += puntaje_jaccard
                if jaccard_artista > 0.3:
                    razones_lexico.append(f"artista (Jaccard={jaccard_artista:.2f}, +{puntaje_jaccard:.1f})")
        
        # d) BM25 para letra (solo si hay términos significativos)
        if _indexador_global and len(palabras_query) > 1:
            texto_completo = f"{cancion['titulo']} {cancion['artista']} {cancion['letra']}"
            tokens_doc = _indexador_global.procesador.limpiar_texto(texto_completo)
            tokens_query_proc = _indexador_global.procesador.limpiar_texto(query)
            
            if tokens_query_proc:
                doc_len = len(texto_completo.split())
                puntuacion_bm25 = calcular_puntuacion_bm25(tokens_query_proc, tokens_doc, doc_len, avg_doc_len)
                
                # Normalizar BM25 (máximo +5)
                puntuacion_bm25_norm = min(puntuacion_bm25 / 10.0, 5.0)
                if puntuacion_bm25_norm > 0.5:
                    score_lexico += puntuacion_bm25_norm
                    razones_lexico.append(f"BM25 ({puntuacion_bm25:.2f} → +{puntuacion_bm25_norm:.1f})")
        
        # e) Bonus por palabra inicial (sutil)
        if palabras_query:
            primera_palabra = list(palabras_query)[0]
            if titulo_lower.startswith(primera_palabra):
                score_lexico += 2.0
                razones_lexico.append(f"título comienza con '{primera_palabra}' (+2)")
        
        # ===== 4.2 CÁLCULO DEL FACTOR SEMÁNTICO MULTIPLICATIVO =====
        
        # Calcular factor semántico basado en el score de similitud
        # Rango: 0.1 a 2.0 (penaliza baja semántica, bonifica alta)
        if score_semantico > 0:
            if score_semantico < 0.3:
                # Semántica mala: factor entre 0.1 y 0.5
                factor_semantico = 0.1 + (score_semantico / 0.3) * 0.4
            elif score_semantico < 0.7:
                # Semántica media: factor entre 0.5 y 1.0
                factor_semantico = 0.5 + ((score_semantico - 0.3) / 0.4) * 0.5
            else:
                # Semántica buena: factor entre 1.0 y 2.0
                factor_semantico = 1.0 + ((score_semantico - 0.7) / 0.3) * 1.0
        else:
            # Sin coincidencia semántica: penalización fuerte
            factor_semantico = 0.1
        
        razones_semantico.append(f"sim={score_semantico:.2f} → factor={factor_semantico:.2f}")
        
        # ===== 4.3 PUNTUACIÓN FINAL SEGÚN TIPO DE QUERY =====
        
        if es_query_semantica:
            # Para queries semánticas: filtro más estricto y dominancia semántica
            if score_semantico < 0.25:
                # Ignorar resultados con muy baja semántica en queries semánticas
                continue
            
            # Fórmula: priorizar semántica, léxico como apoyo
            if score_semantico > 0.75:
                # Alta semántica: bonificación adicional
                puntuacion_total = (score_semantico * 40) + (score_lexico * 0.5)
                razones_semantico.append("bonus: alta semántica")
            else:
                # Semántica media
                puntuacion_total = (score_semantico * 30) + (score_lexico * 0.3)
        else:
            # Para queries léxicas (títulos/artistas): dominancia léxica
            if score_lexico < 3 and score_semantico < 0.3:
                # Muy poco relevante
                continue
            
            # Bonus multicampo para queries léxicas
            campos_coincidentes = 0
            if jaccard_titulo > 0.2 if 'jaccard_titulo' in locals() else False:
                campos_coincidentes += 1
            if jaccard_artista > 0.2 if 'jaccard_artista' in locals() else False:
                campos_coincidentes += 1
            if score_semantico > 0.5:
                campos_coincidentes += 1
            
            # Fórmula: priorizar léxico, semántica como apoyo
            puntuacion_total = score_lexico + (score_semantico * 10.0)
            
            if campos_coincidentes >= 2:
                bonus_multicampo = 3.0
                puntuacion_total += bonus_multicampo
                razones_lexico.append(f"multicampo ({campos_coincidentes} campos, +{bonus_multicampo})")
        
        # Aplicar factor semántico multiplicativo (ajuste fino)
        puntuacion_total = puntuacion_total * factor_semantico
        
        # Combinar razones
        razones = razones_lexico + razones_semantico
        
        # Añadir información de diagnóstico si está disponible
        if score_semantico > 0:
            razones.append(f"puntaje_final={puntuacion_total:.1f}")
        
        # ===== 5. FILTRAR POR PUNTUACIÓN MÍNIMA =====
        if puntuacion_total >= min_score:
            resultados.append((doc_id, puntuacion_total, razones))
    
    # Ordenar por puntuación descendente
    resultados.sort(key=lambda x: x[1], reverse=True)
    
    # Logging para depuración (opcional)
    if resultados and len(resultados) > 0:
        print(f"📊 Búsqueda | tipo={'semántica' if es_query_semantica else 'léxica'} | "
              f"min_score={min_score} | resultados={len(resultados)} | "
              f"top_score={resultados[0][1]:.2f}")
    
    return resultados


def calcular_puntuacion_bm25(tokens_query, doc_tokens, doc_len, avg_doc_len, k1=1.5, b=0.75):
    if not tokens_query or not doc_tokens:
        return 0.0
    
    score = 0.0
    doc_freq = Counter(doc_tokens)
    
    for termino in set(tokens_query):
        if termino in doc_freq:
            tf = doc_freq[termino]
            
            # Componente TF con normalización por longitud
            tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
            
            # IDF (evitar división por cero)
            df = _indexador_global.frecuencia_documentos.get(termino, 0)
            idf = math.log((_indexador_global.num_documentos - df + 0.5) / (df + 0.5) + 1)
            
            score += tf_component * idf
    
    return score


def buscar_en_genius(query, max_intentos=10, genius_token=None):
    global _indexador_global
    
    canciones_encontradas = []
    
    try:
        if genius_token:
            url_search = "https://api.genius.com/search"
            params = {'q': query}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Authorization': f'Bearer {genius_token}'
            }
        else:
            url_search = "https://genius.com/api/search/multi"
            params = {'q': query}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        
        print(f"🔍 Buscando en Genius.com: {query}")
        response = requests.get(url_search, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        datos = response.json()
        
        # Procesar resultados de búsqueda
        if 'response' in datos and 'hits' in datos['response']:
            hits = datos['response']['hits'][:max_intentos]
            
            for hit in hits:
                if 'result' in hit:
                    resultado = hit['result']
                    titulo = resultado.get('title', '')
                    artista = resultado.get('primary_artist', {}).get('name', '')
                    url_cancion = resultado.get('url', '')
                    
                    if titulo and artista and url_cancion:
                        print(f"   📍 Encontrado: {titulo} - {artista}")
                        
                        # Intentar obtener la letra
                        try:
                            letra = _scrape_letra_genius(url_cancion)
                        except:
                            letra = f"[Letra disponible en {url_cancion}]"
                        
                        cancion_data = {
                            'titulo': titulo,
                            'artista': artista,
                            'letra': letra,
                            'album': resultado.get('album', {}).get('name', '') if resultado.get('album') else '',
                            'generos': [],
                            'tags': ['genius', 'web-scraping'],
                            'url': url_cancion
                        }
                        
                        canciones_encontradas.append(cancion_data)
                        
                        # Pequeño delay para no sobrecargar Genius
                        time.sleep(0.5)
    
    except Exception as e:
        print(f"⚠️  Error buscando en Genius: {e}")
    
    return canciones_encontradas


def _scrape_letra_genius(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, 'html.parser')
            lyrics_nodes = soup.find_all('div', {'data-lyrics-container': 'true'})
            if not lyrics_nodes:
                lyrics_nodes = soup.select('div[class*="Lyrics__Container"]')

            if lyrics_nodes:
                fragments = []
                for node in lyrics_nodes:
                    for br in node.find_all('br'):
                        br.replace_with('\n')
                    fragments.append(node.get_text(separator='\n'))
                letra = '\n'.join([fragment.strip() for fragment in fragments if fragment.strip()])
                return letra.strip() if letra.strip() else "[Letra no disponible]"
        else:
            # Fallback simple si no está instalado beautifulsoup4
            matches = re.findall(r'<div[^>]*data-lyrics-container=["\"]true["\"][^>]*>(.*?)</div>', html, flags=re.S | re.I)
            if not matches:
                matches = re.findall(r'<div[^>]*class=["\"][^"\"]*Lyrics__Container[^"\"]*["\"][^>]*>(.*?)</div>', html, flags=re.S | re.I)

            if matches:
                fragments = []
                for match in matches:
                    texto = re.sub(r'<br\s*/?>', '\n', match, flags=re.I)
                    texto = re.sub(r'<.*?>', '', texto)
                    texto = texto.strip()
                    if texto:
                        fragments.append(texto)
                letra = '\n'.join(fragments)
                return letra.strip() if letra.strip() else "[Letra no disponible]"

        return "[Letra no disponible]"
    except Exception as e:
        print(f"⚠️  Error extrayendo letra de Genius: {e}")
        return "[Letra no disponible]"


def es_cancion_duplicada(cancion_data):
    global _indexador_global
    if not _indexador_global:
        return False

    titulo_nuevo = cancion_data.get('titulo', '').strip().lower()
    artista_nuevo = cancion_data.get('artista', '').strip().lower()
    url_nuevo = cancion_data.get('url', '').strip().lower()

    for documento in _indexador_global.documentos.values():
        titulo_existente = documento.get('titulo', '').strip().lower()
        artista_existente = documento.get('artista', '').strip().lower()
        url_existente = documento.get('url', '').strip().lower()

        if url_nuevo and url_nuevo == url_existente:
            return True
        if titulo_nuevo and artista_nuevo and titulo_nuevo == titulo_existente and artista_nuevo == artista_existente:
            return True

    return False


def agregar_canciones_encontradas(canciones_nuevas):
    global _indexador_global
    
    if not _indexador_global:
        print("❌ Indexador no inicializado")
        return 0, []
    
    canciones_agregadas = 0
    ids_nuevos = []
    
    for cancion in canciones_nuevas:
        if es_cancion_duplicada(cancion):
            print(f"⚠️ Canción duplicada omitida: {cancion.get('titulo', 'UNKNOWN')} - {cancion.get('artista', 'UNKNOWN')}")
            continue

        try:
            doc_id = _indexador_global.agregar_documento(cancion)
            ids_nuevos.append(doc_id)
            canciones_agregadas += 1
            print(f"✅ Agregada: {cancion['titulo']} - {cancion['artista']}")
        except Exception as e:
            print(f"❌ Error agregando canción: {e}")
    
    return canciones_agregadas, ids_nuevos


def buscar_canciones_avanzado_con_web(query, min_score=5, usar_genius=False, genius_token=None):
    # Búsqueda local primero
    resultados_locales = buscar_canciones_avanzado(query, min_score)
    
    print(f"📊 Resultados locales: {len(resultados_locales)}")
    
    if usar_genius and len(resultados_locales) < 5:
        print(f"🌐 Buscando en Genius.com para complementar resultados...")
        canciones_genius = buscar_en_genius(query, max_intentos=10 - len(resultados_locales), genius_token=genius_token)

        if canciones_genius:
            # Filtrar duplicados antes de agregar
            canciones_unicas = [c for c in canciones_genius if not es_cancion_duplicada(c)]
            if canciones_unicas:
                agregadas, ids_nuevos = agregar_canciones_encontradas(canciones_unicas)
                
                # Procesar SOLO los nuevos documentos para mayor eficiencia
                if agregadas > 0 and ids_nuevos:
                    try:
                        print(f"🔄 Re-vectorizando {agregadas} documentos nuevos...")
                        _indexador_global.procesar_documentos_incrementales(ids_nuevos)
                        _indexador_global.guardar_indice('indice_musica.json')  # Guardar cambios
                        print(f"✅ Documentos re-vectorizados y guardados")
                        
                        try:
                            _indexador_global.cargar_indice('indice_musica.json')
                            print("✅ Índice recargado desde indice_musica.json")
                        except Exception as e:
                            print(f"⚠️ Error recargando índice desde archivo: {e}")
                        
                        # Buscar nuevamente con los datos actualizados
                        resultados_locales = buscar_canciones_avanzado(query, min_score)
                        print(f"📊 Resultados después de Genius: {len(resultados_locales)}")
                        
                        if ids_nuevos:
                            resultados_ids = {doc_id for doc_id, _, _ in resultados_locales}
                            for nuevo_id in ids_nuevos:
                                if nuevo_id not in resultados_ids:
                                    cancion = _indexador_global.obtener_documento(nuevo_id)
                                    if cancion:
                                        resultados_locales.append((nuevo_id, min_score + 5.0, ['nuevo desde Genius']))
                            resultados_locales.sort(key=lambda x: x[1], reverse=True)
                    except Exception as e:
                        import traceback
                        print(f"⚠️  Error re-procesando documentos: {e}")
                        traceback.print_exc()
            else:
                print("⚠️ No se encontraron canciones nuevas para agregar desde Genius.")

    return resultados_locales