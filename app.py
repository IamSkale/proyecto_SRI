from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from pathlib import Path
from Indexer.indexer import IndexadorTFIDF
from Indexer.searcher import set_indexador, buscar_canciones_avanzado

app = Flask(__name__)
CORS(app)

# Variable global para el indexador
indexador = None

def inicializar_indexador():
    """Inicializa el indexador al arrancar la aplicación"""
    global indexador
    
    CARPETA_DATOS = "Database"
    CARPETA_LETRAS = "Database/lyrics"
    ARCHIVO_INDICE = "indice_musica.json"
    
    print("🚀 Inicializando sistema de búsqueda...")
    
    indexador = IndexadorTFIDF(CARPETA_DATOS, CARPETA_LETRAS)
    
    if Path(ARCHIVO_INDICE).exists():
        print("📂 Cargando índice guardado...")
        try:
            indexador.cargar_indice(ARCHIVO_INDICE)
        except Exception as e:
            print(f"⚠️ Error al cargar índice: {e}. Reconstruyendo...")
            indexador.ejecutar_indexacion(ARCHIVO_INDICE)
    else:
        print("🔨 Construyendo índice desde cero...")
        indexador.ejecutar_indexacion(ARCHIVO_INDICE)
    
    set_indexador(indexador)
    print(f"✅ Sistema listo. Documentos indexados: {indexador.num_documentos}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    global indexador
    
    if not indexador:
        return jsonify({'error': 'Indexador no inicializado'}), 500
    
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify([])
    
    # Obtener resultados de búsqueda (tuples: doc_id, score, razones)
    resultados_tuples = buscar_canciones_avanzado(query, min_score=20)
    
    # Convertir a formato JSON con datos completos de canciones
    canciones = []
    for doc_id, score, razones in resultados_tuples:
        cancion_doc = indexador.obtener_documento(doc_id)
        if cancion_doc:
            cancion = {
                'id': doc_id,
                'titulo': cancion_doc.get('titulo', ''),
                'artista': cancion_doc.get('artista', ''),
                'album': cancion_doc.get('album', ''),
                'generos': cancion_doc.get('generos', []),
                'tags': cancion_doc.get('tags', []),
                'score': round(score, 2),
                'año': 'N/A',
                'duracion': 'N/A'
            }
            canciones.append(cancion)
    
    return jsonify(canciones)

if __name__ == '__main__':
    inicializar_indexador()
    app.run(debug=True, port=5001)