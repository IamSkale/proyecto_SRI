from .retriever import RAGRetriever
from .generator import RAGGenerator
import os
from dotenv import load_dotenv

load_dotenv()

class RAGPipeline:
    def __init__(self,
                 index_path="indice_musica.json",  # CAMBIADO a .json
                 data_folder="Database",
                 lyrics_folder="Database/lyrics",
                 model="deepseek-chat",
                 api_key=None):
        
        if api_key is None:
            api_key = os.environ.get('DEEPSEEK_API_KEY')
        
        print(f"\n🔧 Inicializando RAG Pipeline...")
        print(f"   Index path: {index_path}")
        
        self.retriever = RAGRetriever(index_path=index_path,
                                      data_folder=data_folder,
                                      lyrics_folder=lyrics_folder)
        self.generator = RAGGenerator(model=model, api_key=api_key)

    def answer(self, query, top_k=3, max_tokens=250, temperature=0.3):
        print(f"\n🔍 RAG - Procesando consulta: {query[:50]}...")
        
        resultados = self.retriever.retrieve(query, top_k=top_k)
        
        if not resultados:
            return "No se encontraron documentos relevantes.", []
        
        contexts = [doc["contexto"] for doc in resultados]
        answer = self.generator.generate_answer(query, contexts,
                                                max_tokens=max_tokens,
                                                temperature=temperature)
        return answer, resultados