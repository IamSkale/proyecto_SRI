import os
import traceback
from pathlib import Path
import numpy as np
from Indexer.indexer import IndexadorTFIDF
from Indexer.searcher import buscar_canciones_avanzado, set_indexador


class RAGRetriever:
    """Retrieves relevant documents from the existing music index using cosine similarity."""

    def __init__(self,
                 index_path="indice_musica.json",
                 data_folder="Database",
                 lyrics_folder="Database/lyrics",
                 indexador=None):
        self.index_path = Path(index_path)
        self.data_folder = Path(data_folder)
        self.lyrics_folder = Path(lyrics_folder)
        self.indexador = indexador
        if self.indexador is None:
            self._cargar_indexador()
        else:
            print("   ✅ Usando indexador existente")

    def _cargar_indexador(self):
        print(f"\n📂 Cargando índice desde: {self.index_path}")
        
        if not self.index_path.exists():
            raise FileNotFoundError(f"No se encontró el índice: {self.index_path}\n"
                                   f"Ejecuta primero 'python main.py' para generar el índice.")
        
        try:
            self.indexador = IndexadorTFIDF(str(self.data_folder), str(self.lyrics_folder))
            self.indexador.cargar_indice(str(self.index_path))
            print(f"   ✅ Índice cargado: {self.indexador.num_documentos} documentos")
            
            # Registrar en el buscador para fallback keyword
            set_indexador(self.indexador)
            
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
        
        documentos = self._retrieve_hibrido(query, top_k)
          
        return documentos
    
    def _retrieve_hibrido(self, query, top_k=5):
        """Búsqueda híbrida usando el motor de búsqueda avanzado"""
        try:
            # Usamos min_score=5 para ser más permisivos en RAG
            resultados_avanzados = buscar_canciones_avanzado(query, min_score=5)
            
            documentos = []
            for doc_id, score, razones in resultados_avanzados[:top_k]:
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
            
            print(f"   ✅ Búsqueda híbrida: {len(documentos)} resultados")
            return documentos
        except Exception as e:
            print(f"   ❌ Error en búsqueda híbrida: {e}")
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