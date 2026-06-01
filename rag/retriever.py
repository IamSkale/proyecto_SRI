from pathlib import Path
from Indexer.searcher import buscar_canciones_avanzado


class RAGRetriever:
    def __init__(self,
                 index_path="indice_musica.json",
                 data_folder="Database",
                 lyrics_folder="Database/lyrics",
                 indexador=None):
        self.index_path = Path(index_path)
        self.data_folder = Path(data_folder)
        self.lyrics_folder = Path(lyrics_folder)
        self.indexador = indexador
    
    def _retrieve_hibrido(self, query, top_k=5):
        try:
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