"""
Script para integrar datos recopilados por el crawler al índice musical principal.
Versión COMPLETA: Actualiza índice JSON, embeddings, y modelos vectoriales.

Este script:
1. Carga el índice existente (indice_musica.json + embeddings + modelos)
2. Lee todos los archivos JSON del crawler (Database/crawled_data/)
3. Agrega nuevas canciones evitando duplicados
4. Regenera el índice invertido e IDF
5. Genera NUEVOS embeddings para las canciones agregadas
6. Actualiza la base de datos vectorial (archivos .npz, .pkl)
7. Guarda TODOS los índices actualizados
"""

import json
import math
import pickle
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

# Importar módulos del proyecto
from Indexer.indexer import ProcesadorTexto, IndexadorTFIDF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

# Intentar importar sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️ sentence-transformers no instalado. Los embeddings se generarán con TF-IDF+SVD.")


class MergerIndicesCompleto:
    """
    Clase para integrar datos del crawler a TODOS los índices del sistema.
    """
    
    def __init__(self, index_path="Database/indice_musica.json", data_folder="Database", lyrics_folder="Database/lyrics"):
        self.index_path = Path(index_path)
        self.data_folder = Path(data_folder)
        self.lyrics_folder = Path(lyrics_folder)
        self.procesador = ProcesadorTexto()
        
        # Estructuras del índice
        self.documentos = {}
        self.indice_invertido = {}
        self.frecuencia_documentos = {}
        self.idf = {}
        self.vocabulario = set()
        self.idiomas_documentos = {}
        self.document_ids_order = []
        self.num_documentos = 0
        
        # Embeddings y modelos
        self.vectorizer = None
        self.svd = None
        self.document_embeddings = None
        self.st_model = None
        self.st_model_name = None
        self.use_sentence_transformer = HAS_SENTENCE_TRANSFORMERS
        
    def cargar_indice_completo(self):
        """Carga TODOS los índices (JSON + embeddings + modelos)."""
        print("\n📂 Cargando índice completo...")
        
        # 1. Cargar índice JSON
        if not self.index_path.exists():
            print(f"❌ No se encontró {self.index_path}")
            return False
        
        with open(self.index_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        self.documentos = datos.get('documentos', {})
        self.indice_invertido = datos.get('indice_invertido', {})
        self.frecuencia_documentos = datos.get('frecuencia_documentos', {})
        self.idf = datos.get('idf', {})
        self.vocabulario = set(datos.get('vocabulario', []))
        self.num_documentos = datos.get('num_documentos', len(self.documentos))
        self.idiomas_documentos = datos.get('idiomas_documentos', {})
        self.document_ids_order = datos.get('document_ids_order', list(self.documentos.keys()))
        
        print(f"  ✅ Índice JSON cargado: {self.num_documentos} documentos")
        
        # 2. Cargar embeddings y modelos
        self._cargar_embeddings()
        
        return True
    
    def _cargar_embeddings(self):
        """Carga embeddings desde archivos auxiliares."""
        base_path = self.index_path.with_suffix('')
        
        # Intentar cargar embeddings de sentence-transformers
        st_embeddings_path = base_path.with_suffix('.st.embeddings.npz')
        st_model_path = base_path.with_suffix('.st_model.txt')
        st_order_path = base_path.with_suffix('.st_order.txt')
        
        if st_embeddings_path.exists() and HAS_SENTENCE_TRANSFORMERS:
            try:
                data = np.load(st_embeddings_path)
                self.document_embeddings = data['embeddings']
                
                if st_order_path.exists():
                    with open(st_order_path, 'r', encoding='utf-8') as f:
                        self.document_ids_order = [line.strip() for line in f if line.strip()]
                
                if st_model_path.exists():
                    with open(st_model_path, 'r', encoding='utf-8') as f:
                        self.st_model_name = f.read().strip()
                        self.st_model = SentenceTransformer(self.st_model_name)
                
                print(f"  ✅ Embeddings ST cargados: {self.document_embeddings.shape}")
                return True
            except Exception as e:
                print(f"  ⚠️ Error cargando embeddings ST: {e}")
        
        # Intentar cargar TF-IDF + SVD
        vectorizer_path = base_path.with_suffix('.vectorizer.pkl')
        svd_path = base_path.with_suffix('.svd.pkl')
        embeddings_path = base_path.with_suffix('.embeddings.npz')
        
        if vectorizer_path.exists() and svd_path.exists() and embeddings_path.exists():
            try:
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                with open(svd_path, 'rb') as f:
                    self.svd = pickle.load(f)
                data = np.load(embeddings_path)
                self.document_embeddings = data['embeddings']
                print(f"  ✅ Embeddings TF-IDF+SVD cargados: {self.document_embeddings.shape}")
                return True
            except Exception as e:
                print(f"  ⚠️ Error cargando embeddings TF-IDF: {e}")
        
        print("  ⚠️ No se encontraron embeddings. Se generarán nuevos.")
        return False
    
    def obtener_datos_crawler(self):
        """Obtiene todos los archivos JSON del crawler."""
        crawled_dir = Path('Database/crawled_data')
        if not crawled_dir.exists():
            print(f"⚠️ No existe el directorio {crawled_dir}")
            return []
        
        archivos_json = list(crawled_dir.glob('*.json'))
        # Excluir archivos que no son del crawler
        archivos_json = [f for f in archivos_json if 'crawled_songs' in f.name or 'crawled_data' in f.name]
        
        if not archivos_json:
            print(f"⚠️ No se encontraron archivos JSON en {crawled_dir}")
            return []
        
        print(f"📊 Encontrados {len(archivos_json)} archivos del crawler")
        
        todas_canciones = []
        for archivo in archivos_json:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    todas_canciones.extend(data)
                elif isinstance(data, dict):
                    # Buscar en posibles keys
                    for key in ['canciones', 'songs', 'data', 'results']:
                        if key in data and isinstance(data[key], list):
                            todas_canciones.extend(data[key])
                            break
                    else:
                        todas_canciones.append(data)
                
                print(f"  ✅ {archivo.name}: {len(data) if isinstance(data, list) else 1} canciones")
            except Exception as e:
                print(f"  ❌ Error leyendo {archivo.name}: {e}")
        
        return todas_canciones
    
    def generar_id_cancion(self, titulo, artista):
        """Genera un ID único basado en título y artista."""
        import hashlib
        texto = f"{titulo.lower().strip()}|{artista.lower().strip()}"
        return hashlib.md5(texto.encode()).hexdigest()[:16]
    
    def es_duplicado(self, nueva_cancion):
        """Verifica si una canción ya existe en el índice."""
        titulo_nuevo = nueva_cancion.get('titulo', '').lower().strip()
        artista_nuevo = nueva_cancion.get('artista', '').lower().strip()
        url_nuevo = nueva_cancion.get('url', '').lower().strip()
        
        if not titulo_nuevo or not artista_nuevo:
            return True
        
        for doc_id, doc in self.documentos.items():
            titulo_existente = doc.get('titulo', '').lower().strip()
            artista_existente = doc.get('artista', '').lower().strip()
            url_existente = doc.get('url', '').lower().strip()
            
            # Comparar por URL
            if url_nuevo and url_existente and url_nuevo == url_existente:
                return True
            
            # Comparar por título + artista
            if titulo_existente == titulo_nuevo and artista_existente == artista_nuevo:
                return True
            
            # Comparar por ID si existe
            if nueva_cancion.get('id') == doc.get('id'):
                return True
        
        return False
    
    def normalizar_cancion(self, cancion):
        """Normaliza la estructura de una canción del crawler."""
        return {
            'id': cancion.get('id', self.generar_id_cancion(
                cancion.get('titulo', ''), 
                cancion.get('artista', '')
            )),
            'titulo': cancion.get('titulo', ''),
            'artista': cancion.get('artista', ''),
            'album': cancion.get('album', ''),
            'generos': cancion.get('generos', []) if isinstance(cancion.get('generos'), list) else [],
            'tags': cancion.get('tags', []) if isinstance(cancion.get('tags'), list) else [],
            'letra': cancion.get('letra', ''),
            'url': cancion.get('url', ''),
            'fecha_extraccion': cancion.get('fecha_extraccion', '')
        }
    
    def integrar_datos_crawler(self, nuevas_canciones):
        """Integra nuevas canciones al índice evitando duplicados."""
        canciones_agregadas = 0
        canciones_duplicadas = 0
        nuevos_ids = []
        
        print(f"\n📥 Integrando {len(nuevas_canciones)} canciones del crawler...")
        
        for cancion in nuevas_canciones:
            # Validar que tenga datos mínimos
            if not cancion.get('titulo') or not cancion.get('artista'):
                continue
            
            # Verificar duplicados
            if self.es_duplicado(cancion):
                canciones_duplicadas += 1
                continue
            
            # Normalizar canción
            doc_normalizado = self.normalizar_cancion(cancion)
            doc_id = doc_normalizado['id']
            
            # Evitar sobreescribir
            if doc_id in self.documentos:
                canciones_duplicadas += 1
                continue
            
            # Agregar al índice
            self.documentos[doc_id] = doc_normalizado
            nuevos_ids.append(doc_id)
            canciones_agregadas += 1
        
        print(f"  ✅ Agregadas: {canciones_agregadas}")
        print(f"  ⚠️ Duplicadas: {canciones_duplicadas}")
        
        return nuevos_ids
    
    def regenerar_indices_textuales(self):
        """Regenera el índice invertido e IDF con todos los documentos."""
        print(f"\n🔧 Regenerando índices textuales...")
        
        self.indice_invertido = defaultdict(list)
        self.frecuencia_documentos = defaultdict(int)
        self.vocabulario = set()
        self.idf = {}
        self.idiomas_documentos = {}
        
        num_docs = len(self.documentos)
        print(f"  📊 Procesando {num_docs} documentos...")
        
        for i, (doc_id, doc) in enumerate(self.documentos.items()):
            if (i + 1) % 5000 == 0:
                print(f"    Procesados: {i + 1}/{num_docs}")
            
            # Crear texto completo
            texto_completo = f"{doc.get('titulo', '')} {doc.get('artista', '')} {doc.get('letra', '')}"
            if doc.get('generos'):
                texto_completo += " " + " ".join(doc['generos'])
            if doc.get('tags'):
                texto_completo += " " + " ".join(doc['tags'])
            
            # Detectar idioma
            idioma = self.procesador.detectar_idioma(texto_completo)
            self.idiomas_documentos[doc_id] = idioma
            
            # Limpiar y tokenizar
            tokens = self.procesador.limpiar_texto(texto_completo, idioma)
            
            # Calcular TF y actualizar índice invertido
            tf = Counter(tokens)
            for termino, freq in tf.items():
                self.indice_invertido[termino].append((doc_id, freq))
                self.vocabulario.add(termino)
        
        # Calcular frecuencia de documentos (DF)
        for termino, posting_list in self.indice_invertido.items():
            self.frecuencia_documentos[termino] = len(posting_list)
        
        # Calcular IDF
        print(f"  📊 Calculando IDF para {len(self.vocabulario)} términos...")
        for termino in self.vocabulario:
            df = self.frecuencia_documentos.get(termino, 0)
            self.idf[termino] = math.log(num_docs / (df + 1))
        
        self.num_documentos = num_docs
        
        print(f"  ✅ Índices regenerados: {len(self.vocabulario)} términos")
    
    def _texto_semantico_doc(self, doc):
        """Construye texto para embeddings semánticos."""
        partes = [doc.get('titulo', ''), doc.get('artista', ''), doc.get('album', '')]
        if doc.get('generos'):
            partes.append(' '.join(doc['generos']))
        if doc.get('tags'):
            partes.append(' '.join(doc['tags']))
        partes.append(doc.get('letra', ''))
        return ' '.join([p for p in partes if p]).strip()
    
    def generar_embeddings_incrementales(self, nuevos_ids, n_components=128, max_features=5000):
        """
        Genera embeddings SOLO para los documentos nuevos y los agrega.
        Esto es mucho más eficiente que regenerar todos los embeddings.
        """
        if not nuevos_ids:
            return
        
        print(f"\n🧠 Generando embeddings para {len(nuevos_ids)} documentos nuevos...")
        
        # Obtener textos de documentos nuevos
        nuevos_textos = []
        nuevos_ids_validos = []
        
        for doc_id in nuevos_ids:
            doc = self.documentos.get(doc_id)
            if doc:
                nuevos_textos.append(self._texto_semantico_doc(doc))
                nuevos_ids_validos.append(doc_id)
        
        if not nuevos_textos:
            return
        
        # Caso 1: Usar sentence-transformers
        if self.use_sentence_transformer and HAS_SENTENCE_TRANSFORMERS:
            try:
                if self.st_model is None:
                    model_name = self.st_model_name or 'all-MiniLM-L6-v2'
                    self.st_model = SentenceTransformer(model_name)
                    self.st_model_name = model_name
                
                nuevos_embeddings = self.st_model.encode(nuevos_textos, show_progress_bar=False, convert_to_numpy=True)
                nuevos_embeddings = normalize(nuevos_embeddings)
                
                if self.document_embeddings is not None and len(self.document_embeddings) > 0:
                    self.document_embeddings = np.vstack([self.document_embeddings, nuevos_embeddings])
                else:
                    self.document_embeddings = nuevos_embeddings
                
                # Actualizar orden
                self.document_ids_order.extend(nuevos_ids_validos)
                
                print(f"  ✅ Embeddings ST generados: {len(nuevos_embeddings)} nuevos vectores")
                return
            except Exception as e:
                print(f"  ⚠️ Error generando embeddings ST: {e}")
        
        # Caso 2: Usar TF-IDF + SVD
        try:
            # Obtener todos los textos (viejos + nuevos)
            todos_ids = self.document_ids_order + nuevos_ids_validos
            todos_textos = []
            for doc_id in todos_ids:
                doc = self.documentos.get(doc_id, {})
                todos_textos.append(self._texto_semantico_doc(doc))
            
            # Reconstruir vectorizador si es necesario
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(max_features=max_features, ngram_range=(1, 2))
                X = self.vectorizer.fit_transform(todos_textos)
            else:
                # Transformar textos existentes y nuevos
                X = self.vectorizer.transform(todos_textos)
            
            n_components = min(n_components, X.shape[1] - 1, X.shape[0] - 1)
            if n_components >= 1:
                if self.svd is None:
                    self.svd = TruncatedSVD(n_components=n_components, random_state=42)
                    X_reduced = self.svd.fit_transform(X)
                else:
                    X_reduced = self.svd.transform(X)
                self.document_embeddings = normalize(X_reduced)
            else:
                self.document_embeddings = normalize(X.toarray())
            
            self.document_ids_order = todos_ids
            print(f"  ✅ Embeddings TF-IDF+SVD regenerados: {self.document_embeddings.shape}")
            
        except Exception as e:
            print(f"  ⚠️ Error generando embeddings TF-IDF: {e}")
    
    def guardar_indice_completo(self):
        """Guarda TODOS los índices (JSON + embeddings + modelos)."""
        print("\n💾 Guardando índice completo...")
        
        # 1. Guardar índice JSON
        datos_json = {
            'documentos': self.documentos,
            'indice_invertido': dict(self.indice_invertido),
            'frecuencia_documentos': self.frecuencia_documentos,
            'idf': self.idf,
            'vocabulario': list(self.vocabulario),
            'num_documentos': self.num_documentos,
            'idiomas_documentos': self.idiomas_documentos,
            'document_ids_order': self.document_ids_order
        }
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(datos_json, f, ensure_ascii=False, indent=2)
        
        tamaño_mb = self.index_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Índice JSON guardado: {tamaño_mb:.2f} MB")
        
        # 2. Guardar embeddings y modelos
        self._guardar_embeddings()
    
    def _guardar_embeddings(self):
        """Guarda embeddings y modelos en archivos auxiliares."""
        if self.document_embeddings is None:
            print("  ⚠️ No hay embeddings para guardar")
            return
        
        base_path = self.index_path.with_suffix('')
        
        # Guardar embeddings de sentence-transformers
        if self.st_model is not None:
            try:
                st_embeddings_path = base_path.with_suffix('.st.embeddings.npz')
                st_model_path = base_path.with_suffix('.st_model.txt')
                st_order_path = base_path.with_suffix('.st_order.txt')
                
                np.savez_compressed(st_embeddings_path, embeddings=self.document_embeddings)
                
                with open(st_model_path, 'w', encoding='utf-8') as f:
                    f.write(self.st_model_name or 'all-MiniLM-L6-v2')
                
                with open(st_order_path, 'w', encoding='utf-8') as f:
                    for doc_id in self.document_ids_order:
                        f.write(doc_id + '\n')
                
                print(f"  ✅ Embeddings ST guardados")
                return
            except Exception as e:
                print(f"  ⚠️ Error guardando embeddings ST: {e}")
        
        # Guardar embeddings de TF-IDF+SVD
        if self.vectorizer is not None and self.svd is not None:
            try:
                vectorizer_path = base_path.with_suffix('.vectorizer.pkl')
                svd_path = base_path.with_suffix('.svd.pkl')
                embeddings_path = base_path.with_suffix('.embeddings.npz')
                
                with open(vectorizer_path, 'wb') as f:
                    pickle.dump(self.vectorizer, f)
                with open(svd_path, 'wb') as f:
                    pickle.dump(self.svd, f)
                np.savez_compressed(embeddings_path, embeddings=self.document_embeddings)
                
                print(f"  ✅ Embeddings TF-IDF+SVD guardados")
            except Exception as e:
                print(f"  ⚠️ Error guardando embeddings TF-IDF: {e}")
    
    def ejecutar(self):
        """Ejecuta el proceso completo de integración."""
        print("\n" + "="*60)
        print("🎵 INTEGRADOR COMPLETO - CRAWLER → ÍNDICE")
        print("="*60)
        
        # 1. Cargar índice actual
        if not self.cargar_indice_completo():
            print("❌ No se pudo cargar el índice")
            return False
        
        # 2. Obtener datos del crawler
        nuevas_canciones = self.obtener_datos_crawler()
        if not nuevas_canciones:
            print("⚠️ No hay datos del crawler para integrar")
            return False
        
        # 3. Integrar datos evitando duplicados
        nuevos_ids = self.integrar_datos_crawler(nuevas_canciones)
        
        if not nuevos_ids:
            print("⚠️ No se agregaron canciones nuevas")
            return False
        
        # 4. Regenerar índices textuales
        self.regenerar_indices_textuales()
        
        # 5. Generar embeddings para nuevas canciones
        self.generar_embeddings_incrementales(nuevos_ids)
        
        # 6. Guardar todo
        self.guardar_indice_completo()
        
        # 7. Mostrar resumen
        print("\n" + "="*60)
        print("✅ INTEGRACIÓN COMPLETADA")
        print("="*60)
        print(f"📊 Documentos totales: {self.num_documentos}")
        print(f"📚 Términos únicos: {len(self.vocabulario)}")
        print(f"🌐 Idiomas detectados: {len(set(self.idiomas_documentos.values()))}")
        print(f"🔢 Embeddings: {self.document_embeddings.shape if self.document_embeddings is not None else 'Ninguno'}")
        print(f"📁 Índice guardado en: {self.index_path}")
        print("="*60)
        
        return True


def main():
    """Función principal."""
    merger = MergerIndicesCompleto()
    merger.ejecutar()


if __name__ == "__main__":
    main()