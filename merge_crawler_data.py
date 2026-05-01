"""
Script para integrar datos recopilados por el crawler al índice musical principal.

Este script:
1. Carga el índice existente (indice_musica.json)
2. Lee todos los archivos JSON del crawler (Database/crawled_data/)
3. Agrega nuevas canciones evitando duplicados
4. Regenera el índice invertido e IDF
5. Guarda el índice actualizado
"""

import json
import math
from pathlib import Path
from collections import defaultdict, Counter
from Indexer.indexer import ProcesadorTexto

def cargar_indice_actual():
    """Carga el índice musical actual."""
    archivo = Path('indice_musica.json')
    if not archivo.exists():
        print("❌ No se encontró indice_musica.json")
        return None
    
    with open(archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    return datos

def obtener_datos_crawler():
    """Obtiene todos los archivos JSON del crawler."""
    crawled_dir = Path('Database/crawled_data')
    archivos_json = list(crawled_dir.glob('*.json'))
    
    if not archivos_json:
        print(f"⚠️ No se encontraron archivos JSON en {crawled_dir}")
        return []
    
    print(f"📊 Encontrados {len(archivos_json)} archivos del crawler")
    
    todas_canciones = []
    for archivo in archivos_json:
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # El archivo puede contener un array o un dict
            if isinstance(data, list):
                todas_canciones.extend(data)
            elif isinstance(data, dict):
                if 'canciones' in data:
                    todas_canciones.extend(data['canciones'])
                elif 'songs' in data:
                    todas_canciones.extend(data['songs'])
                else:
                    todas_canciones.append(data)
            
            print(f"  ✅ {archivo.name}: {len(data) if isinstance(data, list) else 1} canciones")
        except Exception as e:
            print(f"  ❌ Error leyendo {archivo.name}: {e}")
    
    return todas_canciones

def generar_id_cancion(titulo, artista):
    """Genera un ID único basado en título y artista."""
    import hashlib
    texto = f"{titulo.lower().strip()}|{artista.lower().strip()}"
    return hashlib.md5(texto.encode()).hexdigest()[:16]

def es_duplicado(nueva_cancion, documentos_existentes):
    """Verifica si una canción ya existe en el índice."""
    titulo_nuevo = nueva_cancion.get('titulo', '').lower().strip()
    artista_nuevo = nueva_cancion.get('artista', '').lower().strip()
    
    if not titulo_nuevo or not artista_nuevo:
        return True
    
    # Buscar coincidencias exactas o muy similares
    for doc_id, doc in documentos_existentes.items():
        titulo_existente = doc.get('titulo', '').lower().strip()
        artista_existente = doc.get('artista', '').lower().strip()
        
        if titulo_existente == titulo_nuevo and artista_existente == artista_nuevo:
            return True
        
        # También verificar coincidencia por ID si existe
        if nueva_cancion.get('id') == doc.get('id'):
            return True
    
    return False

def integrar_datos_crawler(indice_actual, nuevas_canciones):
    """Integra nuevas canciones al índice evitando duplicados."""
    
    documentos = indice_actual['documentos']
    canciones_agregadas = 0
    canciones_duplicadas = 0
    
    print(f"\n📥 Integrando {len(nuevas_canciones)} canciones del crawler...")
    
    for cancion in nuevas_canciones:
        # Validar que tenga datos mínimos
        if not cancion.get('titulo') or not cancion.get('artista'):
            continue
        
        # Verificar duplicados
        if es_duplicado(cancion, documentos):
            canciones_duplicadas += 1
            continue
        
        # Generar ID si no existe
        if 'id' not in cancion:
            cancion['id'] = generar_id_cancion(cancion['titulo'], cancion['artista'])
        
        doc_id = cancion['id']
        
        # Evitar sobreescribir si el ID ya existe
        if doc_id in documentos:
            canciones_duplicadas += 1
            continue
        
        # Normalizar estructura
        documento_normalizado = {
            'id': doc_id,
            'titulo': cancion.get('titulo', ''),
            'artista': cancion.get('artista', ''),
            'album': cancion.get('album', ''),
            'generos': cancion.get('generos', []) if isinstance(cancion.get('generos'), list) else [],
            'tags': cancion.get('tags', []) if isinstance(cancion.get('tags'), list) else [],
            'letra': cancion.get('letra', ''),
            'url': cancion.get('url', ''),
            'fecha_extraccion': cancion.get('fecha_extraccion', '')
        }
        
        documentos[doc_id] = documento_normalizado
        canciones_agregadas += 1
    
    print(f"  ✅ Agregadas: {canciones_agregadas}")
    print(f"  ⚠️ Duplicadas: {canciones_duplicadas}")
    
    return indice_actual

def regenerar_indices(indice):
    """Regenera el índice invertido e IDF con todos los documentos."""
    
    print(f"\n🔧 Regenerando índices...")
    
    procesador = ProcesadorTexto()
    indice_invertido = defaultdict(list)
    frecuencia_documentos = defaultdict(int)
    vocabulario = set()
    idf = {}
    idiomas_documentos = indice.get('idiomas_documentos', {})
    
    documentos = indice['documentos']
    num_docs = len(documentos)
    
    print(f"  📊 Procesando {num_docs} documentos...")
    
    for i, (doc_id, doc) in enumerate(documentos.items()):
        if (i + 1) % 10000 == 0:
            print(f"    Procesados: {i + 1}/{num_docs}")
        
        # Crear texto completo
        texto_completo = f"{doc['titulo']} {doc['artista']} {doc['letra']}"
        if doc['generos']:
            texto_completo += " " + " ".join(doc['generos'])
        if doc['tags']:
            texto_completo += " " + " ".join(doc['tags'])
        
        # Detectar idioma si no existe
        if doc_id not in idiomas_documentos:
            idioma = procesador.detectar_idioma(texto_completo)
            idiomas_documentos[doc_id] = idioma
        else:
            idioma = idiomas_documentos[doc_id]
        
        # Limpiar y tokenizar
        tokens = procesador.limpiar_texto(texto_completo, idioma)
        
        # Calcular TF
        tf = Counter(tokens)
        
        # Actualizar índice invertido
        for termino, freq in tf.items():
            indice_invertido[termino].append((doc_id, freq))
            vocabulario.add(termino)
    
    # Calcular frecuencia de documentos (DF)
    for termino, posting_list in indice_invertido.items():
        frecuencia_documentos[termino] = len(posting_list)
    
    # Calcular IDF
    print(f"  📊 Calculando IDF para {len(vocabulario)} términos...")
    for termino in vocabulario:
        df = frecuencia_documentos[termino]
        idf[termino] = math.log(num_docs / (df + 1))
    
    # Actualizar índice
    indice['documentos'] = documentos
    indice['indice_invertido'] = dict(indice_invertido)
    indice['frecuencia_documentos'] = dict(frecuencia_documentos)
    indice['idf'] = idf
    indice['vocabulario'] = list(vocabulario)
    indice['num_documentos'] = num_docs
    indice['idiomas_documentos'] = idiomas_documentos
    
    print(f"  ✅ Vocabulario actualizado: {len(vocabulario)} términos")
    
    return indice

def guardar_indice_actualizado(indice):
    """Guarda el índice actualizado."""
    archivo = Path('indice_musica.json')
    
    print(f"\n💾 Guardando índice actualizado...")
    
    with open(archivo, 'w', encoding='utf-8') as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)
    
    tamaño_mb = archivo.stat().st_size / (1024 * 1024)
    print(f"  ✅ Índice guardado: {tamaño_mb:.2f} MB")

def main():
    print("\n" + "="*60)
    print("🎵 INTEGRADOR DE DATOS CRAWLER AL ÍNDICE MUSICAL")
    print("="*60)
    
    # 1. Cargar índice actual
    print("\n📂 Cargando índice actual...")
    indice = cargar_indice_actual()
    if not indice:
        return
    
    print(f"  ✅ Índice cargado: {indice['num_documentos']} documentos")
    
    # 2. Obtener datos del crawler
    print("\n🕷️ Buscando datos del crawler...")
    nuevas_canciones = obtener_datos_crawler()
    
    if not nuevas_canciones:
        print("⚠️ No hay datos del crawler para integrar")
        return
    
    print(f"  ✅ Total canciones a procesar: {len(nuevas_canciones)}")
    
    # 3. Integrar datos evitando duplicados
    indice = integrar_datos_crawler(indice, nuevas_canciones)
    
    # 4. Regenerar índices
    indice = regenerar_indices(indice)
    
    # 5. Guardar índice actualizado
    guardar_indice_actualizado(indice)
    
    # 6. Mostrar resumen
    print("\n" + "="*60)
    print("✅ INTEGRACIÓN COMPLETADA")
    print("="*60)
    print(f"📊 Documentos totales: {indice['num_documentos']}")
    print(f"📚 Términos únicos: {len(indice['vocabulario'])}")
    print(f"🌐 Idiomas: {len(set(indice['idiomas_documentos'].values()))} detectados")
    print()

if __name__ == "__main__":
    main()
