import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Indexer.indexer import IndexadorTFIDF
from Indexer.searcher import set_indexador, buscar_canciones, mostrar_resultados, mostrar_detalle_completo, buscar_canciones_avanzado

# Variable global para el método de búsqueda
METODO_BUSQUEDA = 'hibrido'  # Opciones: 'bm25', 'tfidf', 'textual', 'hibrido'

def main():
    global METODO_BUSQUEDA
    MIN_SCORE = 20
    CARPETA_DATOS = "Database"
    CARPETA_LETRAS = "Database/lyrics"
    ARCHIVO_INDICE = "indice_musica.pkl"
    
    print("\n🚀 INICIANDO SISTEMA DE BÚSQUEDA MUSICAL...\n")
    
    indexador = IndexadorTFIDF(CARPETA_DATOS, CARPETA_LETRAS)
    
    if Path(ARCHIVO_INDICE).exists():
        print("📂 Se encontró un índice guardado. Cargando...")
        try:
            indexador.cargar_indice(ARCHIVO_INDICE)
        except Exception as e:
            print(f"⚠️ Error al cargar índice: {e}")
            print("Reconstruyendo índice...")
            indexador.ejecutar_indexacion(ARCHIVO_INDICE)
    else:
        print("🔨 No se encontró índice. Construyendo desde cero...")
        indexador.ejecutar_indexacion(ARCHIVO_INDICE)
    
    set_indexador(indexador)
    info_completa = indexador.obtener_info_completa()
    
    if not info_completa:
        print("\n❌ ERROR: No se cargaron canciones.")
        return
    
    print("\n" + "=" * 60)
    print("🎵 SISTEMA DE BÚSQUEDA LISTO 🎵")
    print("=" * 60)
    print(f"📊 Documentos indexados: {indexador.num_documentos}")
    print(f"📊 Términos únicos: {len(indexador.vocabulario)}")
    print(f"🌐 Idiomas soportados: Español, Inglés, Francés, Portugués, Italiano")
    print(f"🔍 Método de búsqueda actual: {METODO_BUSQUEDA.upper()}")
    
    print("\n📝 Comandos:")
    print("  <texto>                     - Buscar canciones")
    print("  metodo [bm25|tfidf|hibrido] - Cambiar método de búsqueda")
    print("  detalle <ID>                - Ver letra completa")
    print("  stats                       - Mostrar estadísticas")
    print("  salir                       - Terminar programa")
    print("")
    
    while True:
        print("-" * 50)
        query = input("🔍 Buscar: ").strip()
        
        if query.lower() == 'salir':
            print("\n👋 ¡Hasta luego!")
            break
        
        if query.lower() == 'stats':
            print(f"\n📊 Estadísticas del índice:")
            print(f"  Total documentos: {indexador.num_documentos}")
            print(f"  Términos únicos: {len(indexador.vocabulario)}")
            print(f"  Método actual: {METODO_BUSQUEDA}")
            continue
        
        if query.lower().startswith('metodo '):
            partes = query.split()
            if len(partes) > 1:
                nuevo_metodo = partes[1].lower()
                if nuevo_metodo in ['bm25', 'tfidf', 'textual', 'hibrido']:
                    METODO_BUSQUEDA = nuevo_metodo
                    print(f"✅ Método cambiado a: {METODO_BUSQUEDA.upper()}")
                else:
                    print(f"❌ Método no válido. Opciones: bm25, tfidf, textual, hibrido")
            continue
        
        if query.lower().startswith('detalle '):
            partes = query.split()
            if len(partes) > 1:
                mostrar_detalle_completo(partes[1])
            continue

        if query.lower().startswith('umbral '):
            partes = query.split()
            if len(partes) > 1:
                try:
                    MIN_SCORE = int(partes[1])
                    print(f"✅ Umbral de relevancia cambiado a: {MIN_SCORE}")
                except ValueError:
                    print(f"❌ Valor inválido. Usa un número entero.")
            continue
            
        if query:
            resultados = buscar_canciones_avanzado(query, metodo=METODO_BUSQUEDA, min_score=MIN_SCORE)
            if resultados:
                print(f"\n🔍 Búsqueda: '{query}' (método: {METODO_BUSQUEDA.upper()}, umbral: {MIN_SCORE})")
                mostrar_resultados(resultados, query=query, min_score=MIN_SCORE)
        else:
            print("⚠️ Escribe algo para buscar.")
        

if __name__ == "__main__":
    main()