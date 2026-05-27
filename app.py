import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)
load_dotenv()

from Indexer.indexer import IndexadorTFIDF
from Indexer.searcher import set_indexador, buscar_canciones_avanzado_con_web
from rag.pipeline import RAGPipeline

app = Flask(__name__)
CORS(app)

# Variables globales
indexador = None
rag_pipeline = None

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


def extraer_fragmento_letra(cancion_doc, query, max_antes=40, max_despues=80):
    letra = cancion_doc.get('letra', '') or ''
    if not letra or not query:
        return ''

    query_lower = query.lower().strip()
    letra_lower = letra.lower()
    pos = letra_lower.find(query_lower)

    if pos == -1:
        palabras_buscables = [palabra for palabra in query_lower.split() if len(palabra) > 3]
        for palabra in palabras_buscables:
            pos = letra_lower.find(palabra)
            if pos != -1:
                break

    if pos != -1:
        inicio = max(0, pos - max_antes)
        fin = min(len(letra), pos + len(query_lower) + max_despues)
        fragmento = letra[inicio:fin].strip()
        if inicio > 0:
            fragmento = '...' + fragmento
        if fin < len(letra):
            fragmento = fragmento + '...'
        return fragmento

    preview = letra.strip()
    return preview[:200] + '...' if len(preview) > 200 else preview


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
    usar_genius = bool(data.get('usar_genius', False))
    genius_token = data.get('genius_token', '').strip()
    
    if not query:
        return jsonify([])
    
    resultados_tuples = buscar_canciones_avanzado_con_web(
        query,
        min_score=15,
        usar_genius=usar_genius,
        genius_token=genius_token
    )
    
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
                'duracion': 'N/A',
                'snippet': extraer_fragmento_letra(cancion_doc, query),
                'letra': cancion_doc.get('letra', '')
            }
            canciones.append(cancion)
    
    return jsonify(canciones)


def obtener_rag_pipeline():
    global rag_pipeline
    if rag_pipeline is None:
        # Configuración para Qwen2.5 local
        use_gpu = os.environ.get('USE_GPU', 'false').lower() == 'true'
        model = os.environ.get('RAG_MODEL', 'qwen2.5-3b')
        model_path = os.environ.get('MODEL_PATH', None)
        
        print(f"📌 Configurando RAG con modelo: {model}")
        print(f"   GPU activada: {use_gpu}")
        
        rag_pipeline = RAGPipeline(
            model=model,
            model_path=model_path,
            use_gpu=use_gpu
        )
    return rag_pipeline


@app.route('/rag', methods=['POST'])
def rag():
    data = request.json or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'La consulta no puede estar vacía.'}), 400

    try:
        pipeline = obtener_rag_pipeline()
        respuesta, documentos = pipeline.answer(query, top_k=3)
        return jsonify({'answer': respuesta, 'documents': documentos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    inicializar_indexador()
    app.run(debug=True, port=5000)