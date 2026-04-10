def buscar_canciones(query, info_completa):
    """Busca canciones que coincidan con la query"""
    if not query.strip():
        return []
    
    query = query.lower().strip()
    resultados = []
    
    for doc_id, cancion in info_completa.items():
        # Buscar en título, artista o letra
        if (query in cancion['titulo'].lower() or 
            query in cancion['artista'].lower() or 
            query in cancion['letra'].lower() or
            any(query in gen.lower() for gen in cancion['generos']) or
            any(query in tag.lower() for tag in cancion['tags'])):
            resultados.append(doc_id)
    
    return resultados

def mostrar_resultados(ids, info_completa):
    """Muestra resultados con título y artista"""
    if not ids:
        print("\n❌ No se encontraron canciones.")
        return
    
    print(f"\n✅ Encontradas {len(ids)} canciones:\n")
    
    for i, doc_id in enumerate(ids[:10], 1):
        c = info_completa[doc_id]
        
        # Mostrar título y artista siempre
        if c['titulo'] != 'SIN TÍTULO':
            print(f"{i}. 🎵 {c['titulo']} - {c['artista']}")
        else:
            print(f"{i}. 📄 ID: {doc_id} (sin título en los datos)")
        
        # Mostrar álbum si existe
        if c['album']:
            print(f"   💿 Álbum: {c['album']}")
        
        # Mostrar géneros si existen
        if c['generos']:
            generos_str = ', '.join(c['generos'][:3])
            print(f"   🏷️  Géneros: {generos_str}")
        
        # Mostrar tags si existen
        if c['tags']:
            tags_str = ', '.join(c['tags'][:3])
            print(f"   🔖 Tags: {tags_str}")
        
        # Mostrar un fragmento de la letra si existe
        if c['letra']:
            # Buscar donde aparece la query para mostrar contexto
            query = getattr(mostrar_resultados, 'ultima_query', '')
            if query and len(query) > 2 and query in c['letra'].lower():
                letra_lower = c['letra'].lower()
                pos = letra_lower.find(query)
                inicio = max(0, pos - 40)
                fin = min(len(c['letra']), pos + 80)
                fragmento = c['letra'][inicio:fin].replace('\n', ' ')
                print(f"   📝 ...{fragmento}...")
            else:
                # Solo mostrar inicio de la letra
                preview = c['letra'][:100].replace('\n', ' ')
                if len(preview) > 10:
                    print(f"   📝 {preview}...")
        
        print()  # Línea en blanco

def mostrar_detalle_completo(cancion_id, info_completa):
    """Muestra todos los detalles de una canción"""
    if cancion_id not in info_completa:
        print("❌ Canción no encontrada")
        return
    
    c = info_completa[cancion_id]
    print("\n" + "="*60)
    print(f"🎵 {c['titulo']}")
    print(f"👤 Artista: {c['artista']}")
    if c['album']:
        print(f"💿 Álbum: {c['album']}")
    if c['generos']:
        print(f"🏷️  Géneros: {', '.join(c['generos'])}")
    if c['tags']:
        print(f"🔖 Tags: {', '.join(c['tags'][:10])}")
    print("\n📝 LETRA COMPLETA:")
    print("-"*40)
    print(c['letra'] if c['letra'] else "No hay letra disponible")
    print("="*60)
