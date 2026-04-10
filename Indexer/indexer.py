"""
SCRIPT COMPLETO CORREGIDO - Para archivos SIN cabecera y separados por TAB
"""

import csv
from pathlib import Path
from collections import defaultdict

# ========== PARTE 1: INDEXACIÓN ==========

def cargar_todo(data_folder, lyrics_folder):
    """Carga todos los datos y devuelve info_completa"""
    
    data_folder = Path(data_folder)
    lyrics_folder = Path(lyrics_folder)
    
    # Estructuras
    canciones = {}      # id -> {titulo, artista, album}
    generos = defaultdict(list)   # id -> [lista de generos]
    tags = defaultdict(list)      # id -> [lista de tags]
    letras = {}         # id -> texto de la letra
    
    # ========== Cargar id_information.csv (artista, canción, álbum) ==========
    print("Cargando id_information.csv...")
    archivo_info = data_folder / 'id_information.csv'
    
    if archivo_info.exists():
        with open(archivo_info, 'r', encoding='utf-8') as f:
            # Usar TAB como separador
            for linea in f:
                partes = linea.strip().split('\t')
                if len(partes) >= 4:
                    id_cancion = partes[0].strip()
                    artista = partes[1].strip()
                    titulo = partes[2].strip()
                    album = partes[3].strip()
                    
                    canciones[id_cancion] = {
                        'titulo': titulo,
                        'artista': artista,
                        'album': album
                    }
                    print(f"  Ejemplo: ID={id_cancion}, Canción={titulo}, Artista={artista}")
        
        print(f"  ✅ Cargadas {len(canciones)} canciones")
    else:
        print(f"  ❌ No se encontró {archivo_info}")
    
    # ========== Cargar id_genres.csv (géneros) ==========
    print("\nCargando id_genres.csv...")
    archivo_generos = data_folder / 'id_genres.csv'
    
    if archivo_generos.exists():
        with open(archivo_generos, 'r', encoding='utf-8') as f:
            for linea in f:
                partes = linea.strip().split('\t')
                if len(partes) >= 2:
                    id_cancion = partes[0].strip()
                    genero = partes[1].strip()
                    
                    if id_cancion and genero:
                        generos[id_cancion].append(genero)
        
        print(f"  ✅ Cargados géneros para {len(generos)} canciones")
    else:
        print(f"  ❌ No se encontró {archivo_generos}")
    
    # ========== Cargar id_tags.csv (tags) ==========
    print("\nCargando id_tags.csv...")
    archivo_tags = data_folder / 'id_tags.csv'
    
    if archivo_tags.exists():
        with open(archivo_tags, 'r', encoding='utf-8') as f:
            for linea in f:
                partes = linea.strip().split('\t')
                if len(partes) >= 2:
                    id_cancion = partes[0].strip()
                    tags_str = partes[1].strip()
                    
                    # Los tags vienen separados por comas
                    if tags_str:
                        lista_tags = [tag.strip() for tag in tags_str.split(',')]
                        tags[id_cancion].extend(lista_tags)
        
        print(f"  ✅ Cargados tags para {len(tags)} canciones")
    else:
        print(f"  ❌ No se encontró {archivo_tags}")
    
    # ========== Cargar letras ==========
    print("\nCargando letras...")
    archivos_letras = list(lyrics_folder.glob('*.txt'))
    
    for archivo in archivos_letras:
        id_cancion = archivo.stem  # Nombre del archivo sin extensión
        with open(archivo, 'r', encoding='utf-8') as f:
            letras[id_cancion] = f.read()
    
    print(f"  ✅ Cargadas {len(letras)} letras")
    
    # ========== Unificar todo ==========
    print("\n🔗 Unificando información...")
    info_completa = {}
    
    # Obtener todos los IDs únicos
    todos_ids = set(canciones.keys()) | set(generos.keys()) | set(tags.keys()) | set(letras.keys())
    
    for id_cancion in todos_ids:
        info_completa[id_cancion] = {
            'id': id_cancion,
            'titulo': canciones.get(id_cancion, {}).get('titulo', 'SIN TÍTULO'),
            'artista': canciones.get(id_cancion, {}).get('artista', 'ARTISTA DESCONOCIDO'),
            'album': canciones.get(id_cancion, {}).get('album', ''),
            'generos': generos.get(id_cancion, []),
            'tags': tags.get(id_cancion, []),
            'letra': letras.get(id_cancion, '')
        }
    
    # Mostrar estadísticas
    print("\n" + "="*50)
    print("📊 ESTADÍSTICAS DEL CORPUS")
    print("="*50)
    print(f"Total canciones únicas: {len(info_completa)}")
    print(f"Con información básica (título/artista): {len(canciones)}")
    print(f"Con géneros: {len(generos)}")
    print(f"Con tags: {len(tags)}")
    print(f"Con letra: {len(letras)}")
    
    # Mostrar ejemplos
    if info_completa:
        print("\n📝 EJEMPLOS DE CANCIONES CARGADAS:")
        ejemplos_mostrados = 0
        for id_cancion, cancion in list(info_completa.items())[:3]:
            if cancion['titulo'] != 'SIN TÍTULO':
                print(f"\n  ID: {cancion['id']}")
                print(f"  🎵 {cancion['titulo']} - {cancion['artista']}")
                if cancion['album']:
                    print(f"  💿 Álbum: {cancion['album']}")
                if cancion['generos']:
                    print(f"  🏷️ Géneros: {', '.join(cancion['generos'][:3])}")
                if cancion['tags']:
                    print(f"  🔖 Tags: {', '.join(cancion['tags'][:3])}")
                ejemplos_mostrados += 1
                if ejemplos_mostrados >= 3:
                    break
        
        # Si no hay canciones con título, mostrar IDs
        if ejemplos_mostrados == 0:
            print("\n  ⚠️ No se encontraron canciones con título. IDs disponibles:")
            for id_cancion in list(info_completa.keys())[:5]:
                print(f"    - {id_cancion}")
    
    return info_completa

