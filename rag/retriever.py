import os
import traceback
from pathlib import Path
import numpy as np
from Indexer.indexer import IndexadorTFIDF


class RAGRetriever:
    """Retrieves relevant documents from the existing music index using cosine similarity."""

    def __init__(self,
                 index_path="indice_musica.json",
                 data_folder="Database",
                 lyrics_folder="Database/lyrics"):
        self.index_path = Path(index_path)
        self.data_folder = Path(data_folder)
        self.lyrics_folder = Path(lyrics_folder)
        self.indexador = None
        self._cargar_indexador()

    def _cargar_indexador(self):
        print(f"\n📂 Cargando índice desde: {self.index_path}")
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"No se encontró el índice: {self.index_path}\n"
                                   f"Ejecuta primero 'python main.py' para generar el índice.")
        
        try:
            self.indexador = IndexadorTFIDF(str(self.data_folder), str(self.lyrics_folder))
            self.indexador.cargar_indice(str(self.index_path))
            print(f"   ✅ Índice cargado: {self.indexador.num_documentos} documentos")
            
            # Verificar embeddings
            if hasattr(self.indexador, 'document_embeddings') and self.indexador.document_embeddings is not None:
                print(f"   ✅ Embeddings semánticos: {self.indexador.document_embeddings.shape[0]} vectores")
            else:
                print(f"   ⚠️ No hay embeddings semánticos.")
                
        except Exception as e:
            print(f"   ❌ Error al cargar índice: {e}")
            traceback.print_exc()
            raise

    def retrieve(self, query, top_k=5):
        query = query.strip()
        if not query:
            return []

        if self.indexador is None:
            raise RuntimeError("Indexador no inicializado correctamente")
        
        return self._retrieve_con_coseno(query, top_k)
    
    def _retrieve_con_coseno(self, query, top_k=5):
        """Búsqueda por similitud coseno"""
        try:
            embedding_query = self.indexador.obtener_embedding(query)
            if embedding_query is None:
                print("   ⚠️ No se pudo generar embedding para la consulta")
                return []
            
            if self.indexador.document_embeddings is None:
                print("   ⚠️ No hay embeddings de documentos")
                return []
            
            # Calcular similitud coseno
            similitudes = np.dot(self.indexador.document_embeddings, embedding_query)
            
            # Obtener top_k
            top_indices = np.argsort(similitudes)[::-1][:top_k]
            
            documentos = []
            doc_ids_order = getattr(self.indexador, 'document_ids_order', list(self.indexador.documentos.keys()))
            
            for idx in top_indices:
                if idx < len(doc_ids_order):
                    doc_id = doc_ids_order[idx]
                    score = float(similitudes[idx])
                    documento = self.indexador.obtener_documento(doc_id) or {}
                    documentos.append({
                        "id": doc_id,
                        "score": score,
                        "titulo": documento.get("titulo", ""),
                        "artista": documento.get("artista", ""),
                        "generos": documento.get("generos", []),
                        "tags": documento.get("tags", []),
                        "letra": documento.get("letra", ""),
                        "contexto": self._build_context(documento)
                    })
            
            print(f"   ✅ Búsqueda por coseno: {len(documentos)} resultados")
            return documentos
            
        except Exception as e:
            print(f"   ❌ Error en búsqueda por coseno: {e}")
            traceback.print_exc()
            return []

    def _build_context(self, documento):
        partes = [
            f"Título: {documento.get('titulo', '')}",
            f"Artista: {documento.get('artista', '')}",
            f"Géneros: {', '.join(documento.get('generos', []))}",
            f"Tags: {', '.join(documento.get('tags', []))}",
            f"Letra: {documento.get('letra', '')[:1500]}"
        ]
        return "\n".join([parte.strip() for parte in partes if parte and parte.strip()])