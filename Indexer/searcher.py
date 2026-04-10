import re
import math
from collections import Counter
from difflib import SequenceMatcher

# Variable global para el indexador
_indexador_global = None

def set_indexador(indexador):
    """Establece el indexador para usar en búsquedas TF-IDF"""
    global _indexador_global
    _indexador_global = indexador


def calcular_similitud_textual(texto1, texto2):
    """
    Calcula similitud entre dos textos usando SequenceMatcher
    Útil para comparar títulos completos
    """
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


def buscar_canciones_avanzado(query, info_completa=None, metodo='hibrido', min_score=20):
    global _indexador_global
    
    if not query.strip():
        return []
    
    query_original = query
    query = query.lower().strip()
    
    resultados = []
    
    # Calcular longitud promedio de documentos para BM25
    if _indexador_global and metodo in ['bm25', 'hibrido']:
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
        
        # 4. Búsqueda en letra (usando TF-IDF o BM25)
        if _indexador_global and metodo in ['bm25', 'tfidf', 'hibrido']:
            texto_completo = f"{cancion['titulo']} {cancion['artista']} {cancion['letra']}"
            tokens_doc = _indexador_global.procesador.limpiar_texto(texto_completo)
            tokens_query_proc = _indexador_global.procesador.limpiar_texto(query)
            
            if metodo == 'bm25' or metodo == 'hibrido':
                doc_len = len(texto_completo.split())
                puntuacion_bm25 = calcular_puntuacion_bm25(tokens_query_proc, tokens_doc, doc_len, avg_doc_len)
                puntuacion += puntuacion_bm25 * 1.5
                if puntuacion_bm25 > 0:
                    razones.append(f"BM25 ({puntuacion_bm25:.3f})")
            
            elif metodo == 'tfidf':
                resultados_tfidf = dict(_indexador_global.buscar(query, top_k=50))
                if doc_id in resultados_tfidf:
                    puntuacion += resultados_tfidf[doc_id] * 2.0
                    razones.append(f"TF-IDF ({resultados_tfidf[doc_id]:.3f})")
        
        # 5. Búsqueda textual directa (fallback)
        elif metodo == 'textual':
            if (query in cancion['titulo'].lower() or 
                query in cancion['artista'].lower() or 
                query in cancion['letra'].lower()):
                if query == cancion['titulo'].lower():
                    puntuacion += 10
                elif query in cancion['titulo'].lower():
                    puntuacion += 5
                elif query in cancion['artista'].lower():
                    puntuacion += 3
                else:
                    puntuacion += 1
                razones.append("coincidencia textual")
        
        # 6. Bonus por coincidencia exacta de frase
        if query in cancion['titulo'].lower():
            puntuacion += 8.0
            razones.append("frase exacta en título")
        elif query in cancion['artista'].lower():
            puntuacion += 4.0
            razones.append("frase exacta en artista")
        
        # 7. Bonus por palabras iniciales
        palabras_query_lista = query.split()
        if palabras_query_lista:
            primera_palabra = palabras_query_lista[0]
            if cancion['titulo'].lower().startswith(primera_palabra):
                puntuacion += 3.0
                razones.append(f"título comienza con '{primera_palabra}'")
        
        # FILTRO DE RELEVANCIA MÍNIMA - SOLO AGREGAR SI PUNTUACION >= min_score
        if puntuacion >= min_score:
            resultados.append((doc_id, puntuacion, razones))
    
    # Ordenar por puntuación (mayor a menor)
    resultados.sort(key=lambda x: x[1], reverse=True)
    
    return resultados


def buscar_canciones(query, info_completa=None, metodo='hibrido', min_score=20):
    """
    Busca canciones usando el método especificado
    
    Args:
        query: texto a buscar
        info_completa: diccionario de documentos (fallback)
        metodo: 'bm25', 'tfidf', 'textual', 'hibrido'
        min_score: puntuación mínima para incluir resultado (default 10)
    
    Returns:
        lista de IDs de canciones que coinciden
    """
    resultados = buscar_canciones_avanzado(query, info_completa, metodo, min_score)
    return [doc_id for doc_id, score, razones in resultados]


def mostrar_resultados(ids=None, info_completa=None, query=None, metodo='hibrido', min_score=20):
    """Muestra resultados con puntuación de relevancia y razones"""
    global _indexador_global
    
    # Si no se pasaron IDs y hay query, buscar
    if ids is None and query:
        resultados = buscar_canciones_avanzado(query, info_completa, metodo, min_score)
        ids_con_puntaje = resultados
        ids = [doc_id for doc_id, _, _ in resultados]
    elif ids and not isinstance(ids[0], tuple) and query:
        resultados = buscar_canciones_avanzado(query, info_completa, metodo, min_score)
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
    """Muestra todos los detalles de una canción"""
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