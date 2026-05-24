import numpy as np
import pickle
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class BuscadorFAISS:
    
    def __init__(self):
        self.index = None
        self.embeddings = None
        self.doc_ids_map = []  # Mapeo de índice FAISS a document IDs
        self.doc_embedding_map = {}  # Cache de embeddings por ID
        self.embedding_dim = None
        self.num_docs = 0
        
    def crear_indice(self, embeddings: np.ndarray, doc_ids: List[str], 
                     usar_gpu: bool = False) -> bool:
        if not HAS_FAISS:
            print("⚠️ FAISS no está instalado. Usando búsqueda por similitud coseno.")
            return False
        
        if embeddings is None or len(embeddings) == 0:
            print("❌ No hay embeddings para indexar")
            return False
        
        if len(embeddings) != len(doc_ids):
            print(f"❌ Mismatch: {len(embeddings)} embeddings vs {len(doc_ids)} doc_ids")
            return False
        
        try:
            # Asegurar que los embeddings son float32 (requerido por FAISS)
            embeddings = np.ascontiguousarray(embeddings.astype(np.float32))
            
            self.embedding_dim = embeddings.shape[1]
            self.num_docs = len(embeddings)
            self.doc_ids_map = list(doc_ids)
            self.embeddings = embeddings
            
            # Crear índice Flat (búsqueda exhaustiva pero muy rápida)
            # Flat con producto interno es equivalente a búsqueda coseno en embeddings normalizados
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            
            # Agregar embeddings al índice
            self.index.add(embeddings)
            
            # Cache de embeddings para búsquedas posteriores
            for doc_id, emb in zip(doc_ids, embeddings):
                self.doc_embedding_map[doc_id] = emb
            
            print(f"✅ Índice FAISS creado: {self.num_docs} documentos, dim={self.embedding_dim}")
            return True
            
        except Exception as e:
            print(f"❌ Error al crear índice FAISS: {e}")
            return False
    
    def buscar(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        if self.index is None:
            return []
        
        k = min(k, self.num_docs)
        
        try:
            # Asegurar formato correcto
            query_vec = np.ascontiguousarray(
                query_embedding.astype(np.float32).reshape(1, -1)
            )
            
            # Buscar en FAISS
            distances, indices = self.index.search(query_vec, k)
            
            resultados = []
            for i, idx in enumerate(indices[0]):
                if 0 <= idx < self.num_docs:
                    doc_id = self.doc_ids_map[idx]
                    similarity = float(distances[0][i])  # Score de similaridad
                    resultados.append((doc_id, similarity))
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error en búsqueda FAISS: {e}")
            return []
    
    def buscar_con_umbral(self, query_embedding: np.ndarray, 
                         umbral: float = 0.0, k_max: int = 100) -> List[Tuple[str, float]]:
        resultados = self.buscar(query_embedding, k=min(k_max, self.num_docs))
        return [(doc_id, sim) for doc_id, sim in resultados if sim >= umbral]
    
    def guardar_indice(self, ruta_indice: str, ruta_metadata: str = None):
        if self.index is None:
            print("❌ No hay índice que guardar")
            return False
        
        try:
            # Guardar índice FAISS
            faiss.write_index(self.index, ruta_indice)
            
            # Guardar metadatos (IDs de documentos y embeddings)
            if ruta_metadata is None:
                ruta_metadata = ruta_indice.replace('.faiss', '.pkl')
            
            metadata = {
                'doc_ids_map': self.doc_ids_map,
                'embedding_dim': self.embedding_dim,
                'num_docs': self.num_docs,
                'embeddings': self.embeddings  # Opcional: para regenerar índice si es necesario
            }
            
            with open(ruta_metadata, 'wb') as f:
                pickle.dump(metadata, f)
            
            print(f"✅ Índice FAISS guardado: {ruta_indice}")
            print(f"✅ Metadatos guardados: {ruta_metadata}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar índice: {e}")
            return False
    
    def cargar_indice(self, ruta_indice: str, ruta_metadata: str = None) -> bool:
        if not HAS_FAISS:
            print("⚠️ FAISS no está instalado")
            return False
        
        try:
            # Cargar índice FAISS
            if not Path(ruta_indice).exists():
                print(f"❌ Archivo de índice no encontrado: {ruta_indice}")
                return False
            
            self.index = faiss.read_index(ruta_indice)
            
            # Cargar metadatos
            if ruta_metadata is None:
                ruta_metadata = ruta_indice.replace('.faiss', '.pkl')
            
            if Path(ruta_metadata).exists():
                with open(ruta_metadata, 'rb') as f:
                    metadata = pickle.load(f)
                
                self.doc_ids_map = metadata.get('doc_ids_map', [])
                self.embedding_dim = metadata.get('embedding_dim')
                self.num_docs = metadata.get('num_docs', len(self.doc_ids_map))
                self.embeddings = metadata.get('embeddings')
                
                # Reconstruir cache de embeddings
                if self.embeddings is not None:
                    for doc_id, emb in zip(self.doc_ids_map, self.embeddings):
                        self.doc_embedding_map[doc_id] = emb
                
                print(f"✅ Índice FAISS cargado: {self.num_docs} documentos")
                return True
            else:
                print(f"⚠️ Metadatos no encontrados: {ruta_metadata}")
                return False
                
        except Exception as e:
            print(f"❌ Error al cargar índice: {e}")
            return False
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas del índice"""
        return {
            'num_documentos': self.num_docs,
            'dimension_embedding': self.embedding_dim,
            'faiss_disponible': HAS_FAISS,
            'indice_creado': self.index is not None
        }
    
    def limpiar(self):
        """Limpia el índice y libera memoria"""
        self.index = None
        self.embeddings = None
        self.doc_ids_map = []
        self.doc_embedding_map = {}
        self.embedding_dim = None
        self.num_docs = 0


class BuscadorFAISSHibrido:
    def __init__(self, usar_faiss: bool = True):
        self.buscador_faiss = BuscadorFAISS() if usar_faiss else None
        self.usar_faiss = usar_faiss and HAS_FAISS
        self.embeddings_fallback = None
        self.doc_ids_fallback = []
    
    def crear_indice(self, embeddings: np.ndarray, doc_ids: List[str]) -> bool:
        """Crea índice (FAISS si disponible, fallback a coseno)"""
        self.doc_ids_fallback = list(doc_ids)
        self.embeddings_fallback = embeddings.copy()
        
        if self.usar_faiss and self.buscador_faiss:
            success = self.buscador_faiss.crear_indice(embeddings, doc_ids)
            self.usar_faiss = success
            return success or self._crear_fallback()
        else:
            return self._crear_fallback()
    
    def _crear_fallback(self) -> bool:
        """Crea fallback para búsqueda coseno simple"""
        print("ℹ️ Usando búsqueda coseno como fallback")
        return len(self.embeddings_fallback) > 0
    
    def buscar(self, query_embedding: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """Busca usando FAISS o fallback coseno"""
        if self.usar_faiss and self.buscador_faiss:
            return self.buscador_faiss.buscar(query_embedding, k)
        else:
            return self._buscar_coseno(query_embedding, k)
    
    def _buscar_coseno(self, query_vec: np.ndarray, k: int) -> List[Tuple[str, float]]:
        """Búsqueda por similitud coseno (fallback)"""
        if self.embeddings_fallback is None or len(self.embeddings_fallback) == 0:
            return []
        
        # Asegurar que el query está normalizado
        query_vec = query_vec.astype(np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm
        
        # Calcular similitud coseno
        similarities = np.dot(self.embeddings_fallback.astype(np.float32), query_vec)
        
        # Obtener top-k
        top_indices = np.argsort(similarities)[::-1][:k]
        
        resultados = []
        for idx in top_indices:
            if 0 <= idx < len(self.doc_ids_fallback):
                resultados.append((self.doc_ids_fallback[idx], float(similarities[idx])))
        
        return resultados
    
    def guardar_indice(self, ruta_base: str):
        """Guarda el índice FAISS si está disponible"""
        if self.usar_faiss and self.buscador_faiss:
            ruta_indice = ruta_base.replace('.pkl', '.faiss')
            self.buscador_faiss.guardar_indice(ruta_indice)
    
    def cargar_indice(self, ruta_base: str) -> bool:
        """Carga el índice FAISS si existe"""
        if self.usar_faiss and self.buscador_faiss:
            ruta_indice = ruta_base.replace('.pkl', '.faiss')
            if Path(ruta_indice).exists():
                return self.buscador_faiss.cargar_indice(ruta_indice)
        return False
