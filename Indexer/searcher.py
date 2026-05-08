import re
import math
import requests
import json
import time
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

# Variable global para el indexador
_indexador_global = None

def set_indexador(indexador):
    global _indexador_global
    _indexador_global = indexador


def calcular_similitud_textual(texto1, texto2):
    if not texto1 or not texto2:
        return 0
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()


def calcular_puntuacion_bm25(tokens_query, doc_tokens, doc_len, avg_doc_len, k1=1.5, b=0.75):
    score = 0
    doc_freq = Counter(doc_tokens)
    
    for termino in set(tokens_query):
        if termino in doc_freq:
            tf = doc_freq[termino]
            # Frecuencia del término en el documento
            tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
            
            # IDF (ya lo tenemos del indexador)
            idf = math.log((_indexador_global.num_documentos - _indexador_global.frecuencia_documentos.get(termino, 0) + 0.5) / 
                          (_indexador_global.frecuencia_documentos.get(termino, 0) + 0.5) + 1)
            
            score += tf_component * idf
    
    return score


def buscar_canciones_avanzado(query, min_score=20):
    global _indexador_global
    
    if not query.strip():
        return []
    
    query = query.lower().strip()
    resultados = []
    
    # Calcular longitud promedio de documentos para BM25
    if _indexador_global:
        doc_lengths = [len(doc['letra'].split()) + len(doc['titulo'].split()) + len(doc['artista'].split()) 
                       for doc in _indexador_global.documentos.values()]
        avg_doc_len = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 100
    
    for doc_id, cancion in (_indexador_global.documentos.items() if _indexador_global else info_completa.items()):
        puntuacion = 0
        razones = []
        
        # 1. Similitud en título (muy importante)
        similitud_titulo = calcular_similitud_textual(query, cancion['titulo'])
        if similitud_titulo > 0.3:
            puntuacion += similitud_titulo * 5.0
            razones.append(f"título ({similitud_titulo:.2f})")
        
        # 2. Similitud en artista
        similitud_artista = calcular_similitud_textual(query, cancion['artista'])
        if similitud_artista > 0.3:
            puntuacion += similitud_artista * 3.0
            razones.append(f"artista ({similitud_artista:.2f})")
        
        # 3. Búsqueda por palabras clave en título y artista
        palabras_query = set(query.split())
        palabras_titulo = set(cancion['titulo'].lower().split())
        palabras_artista = set(cancion['artista'].lower().split())
        
        coincidencias_titulo = len(palabras_query & palabras_titulo)
        coincidencias_artista = len(palabras_query & palabras_artista)
        
        if coincidencias_titulo > 0:
            puntuacion += coincidencias_titulo * 2.0
            razones.append(f"{coincidencias_titulo} palabras en título")
        if coincidencias_artista > 0:
            puntuacion += coincidencias_artista * 1.0
            razones.append(f"{coincidencias_artista} palabras en artista")
        
        # 4. Búsqueda en letra usando BM25 (parte del método híbrido)
        if _indexador_global:
            texto_completo = f"{cancion['titulo']} {cancion['artista']} {cancion['letra']}"
            tokens_doc = _indexador_global.procesador.limpiar_texto(texto_completo)
            tokens_query_proc = _indexador_global.procesador.limpiar_texto(query)
            
            doc_len = len(texto_completo.split())
            puntuacion_bm25 = calcular_puntuacion_bm25(tokens_query_proc, tokens_doc, doc_len, avg_doc_len)
            puntuacion += puntuacion_bm25 * 1.5
            if puntuacion_bm25 > 0:
                razones.append(f"BM25 ({puntuacion_bm25:.3f})")
        
        # 5. Bonus por coincidencia exacta de frase
        if query in cancion['titulo'].lower():
            puntuacion += 8.0
            razones.append("frase exacta en título")
        elif query in cancion['artista'].lower():
            puntuacion += 4.0
            razones.append("frase exacta en artista")
        
        # 6. Bonus por palabras iniciales
        palabras_query_lista = query.split()
        if palabras_query_lista:
            primera_palabra = palabras_query_lista[0]
            if cancion['titulo'].lower().startswith(primera_palabra):
                puntuacion += 3.0
                razones.append(f"título comienza con '{primera_palabra}'")
        
        # FILTRO DE RELEVANCIA MÍNIMA
        if puntuacion >= min_score:
            resultados.append((doc_id, puntuacion, razones))
    
    # Ordenar por puntuación (mayor a menor)
    resultados.sort(key=lambda x: x[1], reverse=True)
    
    return resultados

def buscar_canciones(query, info_completa=None, min_score=20):
    resultados = buscar_canciones_avanzado(query, info_completa, min_score)
    return [doc_id for doc_id, score, razones in resultados]


def mostrar_resultados(ids=None, info_completa=None, query=None, min_score=20):
    global _indexador_global
    
    # Si no se pasaron IDs y hay query, buscar con método híbrido
    if ids is None and query:
        resultados = buscar_canciones_avanzado(query, info_completa, min_score)
        ids_con_puntaje = resultados
        ids = [doc_id for doc_id, _, _ in resultados]
    elif ids and not isinstance(ids[0], tuple) and query:
        resultados = buscar_canciones_avanzado(query, info_completa, min_score)
        ids_con_puntaje = resultados
        ids = [doc_id for doc_id, _, _ in resultados]
    elif ids and isinstance(ids[0], tuple):
        # Filtrar por min_score si ya vienen con puntaje
        ids_con_puntaje = [(doc_id, score, razones) for doc_id, score, razones in ids if score >= min_score]
        ids = [doc_id for doc_id, score, _ in ids_con_puntaje]
    else:
        ids_con_puntaje = [(doc_id, 0, []) for doc_id in ids if ids] if ids else []
    
    if not ids:
        print("\n❌ No se encontraron canciones.")
        return
    
    print(f"\n✅ Encontradas {len(ids)} canciones (relevancia ≥ {min_score}):")
    print("=" * 70)
    
    for i, (doc_id, score, razones) in enumerate(ids_con_puntaje[:15], 1):
        # Obtener documento
        if _indexador_global:
            c = _indexador_global.obtener_documento(doc_id)
        elif info_completa:
            c = info_completa.get(doc_id, {})
        else:
            continue
        
        if not c:
            continue
        
        # Mostrar con puntuación
        print(f"\n{i}. [Relevancia: {score:.2f}] 🎵 {c.get('titulo', 'SIN TÍTULO')}")
        print(f"   👤 Artista: {c.get('artista', 'DESCONOCIDO')}")
        
        # Mostrar razón de relevancia
        if razones:
            razones_str = ', '.join(razones[:3])
            print(f"   📊 Relevancia por: {razones_str}")
        
        # Mostrar álbum si existe
        if c.get('album'):
            print(f"   💿 Álbum: {c['album']}")
        
        # Mostrar géneros si existen
        if c.get('generos'):
            generos_str = ', '.join(c['generos'][:3])
            print(f"   🏷️  Géneros: {generos_str}")
        
        # Mostrar tags si existen
        if c.get('tags'):
            tags_str = ', '.join(c['tags'][:3])
            print(f"   🔖 Tags: {tags_str}")
        
        # Mostrar fragmento de letra
        if c.get('letra') and query:
            query_lower = query.lower()
            letra_lower = c['letra'].lower()
            pos = letra_lower.find(query_lower)
            
            if pos != -1:
                inicio = max(0, pos - 50)
                fin = min(len(c['letra']), pos + 100)
                fragmento = c['letra'][inicio:fin].replace('\n', ' ')
                print(f"   📝 ...{fragmento}...")
            else:
                palabras = query_lower.split()
                for palabra in palabras[:2]:
                    if len(palabra) > 3 and palabra in letra_lower:
                        pos = letra_lower.find(palabra)
                        if pos != -1:
                            inicio = max(0, pos - 40)
                            fin = min(len(c['letra']), pos + 60)
                            fragmento = c['letra'][inicio:fin].replace('\n', ' ')
                            print(f"   📝 ...{fragmento}...")
                            break
                else:
                    preview = c['letra'][:100].replace('\n', ' ')
                    if len(preview) > 10:
                        print(f"   📝 {preview}...")
        
        print("-" * 50)
    
    if len(ids) > 15:
        print(f"\n... y {len(ids) - 15} resultados más.")

def mostrar_detalle_completo(cancion_id, info_completa=None):
    global _indexador_global
    
    if _indexador_global:
        c = _indexador_global.obtener_documento(cancion_id)
    elif info_completa:
        c = info_completa.get(cancion_id)
    else:
        c = None
    
    if not c:
        print("❌ Canción no encontrada")
        return
    
    print("\n" + "=" * 60)
    print(f"🎵 {c.get('titulo', 'SIN TÍTULO')}")
    print(f"👤 Artista: {c.get('artista', 'DESCONOCIDO')}")
    if c.get('album'):
        print(f"💿 Álbum: {c['album']}")
    if c.get('generos'):
        print(f"🏷️  Géneros: {', '.join(c['generos'])}")
    if c.get('tags'):
        print(f"🔖 Tags: {', '.join(c['tags'][:10])}")
    
    if _indexador_global and hasattr(_indexador_global, 'idiomas_documentos'):
        idioma = _indexador_global.idiomas_documentos.get(cancion_id, 'desconocido')
        nombre_idioma = {'es': 'Español', 'en': 'Inglés', 'fr': 'Francés', 'pt': 'Portugués', 'it': 'Italiano'}
        print(f"🌐 Idioma detectado: {nombre_idioma.get(idioma, idioma)}")
    
    print("\n📝 LETRA COMPLETA:")
    print("-" * 40)
    print(c.get('letra', 'No hay letra disponible'))
    print("=" * 60)


def buscar_en_genius(query, max_intentos=3, genius_token=None):
    """
    Busca canciones en Genius.com usando su API y web scraping.
    
    Args:
        query (str): Término de búsqueda (artista y/o canción)
        max_intentos (int): Máximo número de canciones a buscar
        genius_token (str|None): Token de acceso de Genius para la API oficial
    
    Returns:
        list: Lista de canciones encontradas con estructura [titulo, artista, letra]
    """
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
    """
    Extrae la letra de una canción en Genius.
    
    Args:
        url (str): URL de la canción en Genius
    
    Returns:
        str: Letra de la canción
    """
    try:
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar contenedor de letras en Genius
        lyrics_container = soup.find('div', {'data-lyrics-container': 'true'})
        if lyrics_container:
            lineas = []
            for br in lyrics_container.find_all('br'):
                br.replace_with('\n')
            letra = lyrics_container.get_text()
            return letra.strip()
        
        return "[Letra no disponible]"
    
    except Exception as e:
        print(f"⚠️  Error extrayendo letra de Genius: {e}")
        return "[Letra no disponible]"


def agregar_canciones_encontradas(canciones_nuevas):
    """
    Agrega canciones encontradas a la base de datos local.
    
    Args:
        canciones_nuevas (list): Lista de canciones a agregar
    
    Returns:
        int: Número de canciones agregadas exitosamente
    """
    global _indexador_global
    
    if not _indexador_global:
        print("❌ Indexador no inicializado")
        return 0
    
    canciones_agregadas = 0
    
    for cancion in canciones_nuevas:
        try:
            # Agregar canción al indexador
            _indexador_global.agregar_documento(cancion)
            canciones_agregadas += 1
            print(f"✅ Agregada: {cancion['titulo']} - {cancion['artista']}")
        except Exception as e:
            print(f"❌ Error agregando canción: {e}")
    
    # Guardar cambios en el índice
    if canciones_agregadas > 0:
        try:
            _indexador_global.guardar_indice('indice_musica.json')
            print(f"💾 Índice actualizado ({canciones_agregadas} canciones nuevas)")
        except Exception as e:
            print(f"⚠️  Error guardando índice: {e}")
    
    return canciones_agregadas


def buscar_canciones_avanzado_con_web(query, min_score=20, usar_genius=False, genius_token=None):
    """
    Búsqueda avanzada que integra búsqueda local y web.
    Si se activa la opción, busca en Genius cuando hay pocos resultados locales.
    
    Args:
        query (str): Término de búsqueda
        min_score (int): Puntuación mínima de relevancia
        usar_genius (bool): Si se debe complementar con búsqueda en Genius
        genius_token (str|None): Token de acceso de Genius para la API oficial
    
    Returns:
        list: Tuplas (doc_id, score, razones)
    """
    # Búsqueda local primero
    resultados_locales = buscar_canciones_avanzado(query, min_score)
    
    print(f"📊 Resultados locales: {len(resultados_locales)}")
    
    if usar_genius and len(resultados_locales) < 5:
        print(f"🌐 Buscando en Genius.com para complementar resultados...")
        canciones_genius = buscar_en_genius(query, max_intentos=5 - len(resultados_locales), genius_token=genius_token)

        if canciones_genius:
            # Agregar las canciones encontradas a la base de datos
            agregadas = agregar_canciones_encontradas(canciones_genius)
            
            # Re-procesar documentos para actualizar el índice
            if agregadas > 0:
                try:
                    _indexador_global.procesar_documentos()
                    print(f"🔄 Documentos re-procesados")
                    
                    # Buscar nuevamente con los datos actualizados
                    resultados_locales = buscar_canciones_avanzado(query, min_score)
                except Exception as e:
                    print(f"⚠️  Error re-procesando documentos: {e}")

    return resultados_locales
    
    return resultados_locales