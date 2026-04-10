import Indexer.indexer
from Indexer.searcher import mostrar_detalle_completo, mostrar_resultados, buscar_canciones
from Indexer.indexer import cargar_todo

if __name__ == "__main__":
    # Configurar rutas (¡CAMBIA ESTAS RUTAS SEGÚN TU ESTRUCTURA!)
    CARPETA_DATOS = "Database"      # Carpeta donde están los CSVs
    CARPETA_LETRAS = "Database/lyrics"   # Carpeta donde están los .txt de letras
    
    print("\n🚀 INICIANDO SISTEMA DE BÚSQUEDA MUSICAL...\n")
    
    # Cargar todo en memoria
    info_completa = cargar_todo(CARPETA_DATOS, CARPETA_LETRAS)
    
    if not info_completa:
        print("\n❌ ERROR: No se cargaron canciones. Revisa las rutas y los archivos.")
        print("Archivos esperados:")
        print(f"  - {CARPETA_DATOS}/id_information.csv")
        print(f"  - {CARPETA_DATOS}/id_genres.csv")
        print(f"  - {CARPETA_DATOS}/id_tags.csv")
        print(f"  - {CARPETA_LETRAS}/*.txt")
        exit()
    
    # Bucle de búsqueda
    print("\n" + "="*50)
    print("🎵 SISTEMA DE BÚSQUEDA LISTO 🎵")
    print("="*50)
    print("\nComandos:")
    print("  <texto>     - Buscar canciones")
    print("  detalle ID  - Ver letra completa (ej: detalle 0009fFIM1eYThaPg)")
    print("  salir       - Terminar programa")
    print("")
    
    while True:
        print("-"*40)
        query = input("🔍 Buscar: ").strip()
        
        if query.lower() == 'salir':
            print("\n👋 ¡Hasta luego!")
            break
        
        # Comando para ver detalle
        if query.lower().startswith('detalle '):
            partes = query.split()
            if len(partes) > 1:
                mostrar_detalle_completo(partes[1], info_completa)
            continue
        
        if query:
            # Guardar la query para mostrarla en contexto
            mostrar_resultados.ultima_query = query.lower()
            resultados = buscar_canciones(query, info_completa)
            mostrar_resultados(resultados, info_completa)
            
            if resultados:
                print("💡 Tip: Escribe 'detalle ID' para ver la letra completa")
        else:
            print("⚠️ Escribe algo para buscar.")