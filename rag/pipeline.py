from .retriever import RAGRetriever
from .generator import RAGGenerator
from dotenv import load_dotenv

load_dotenv()

class RAGPipeline:
    def __init__(self,
                 index_path="indice_musica.json",
                 data_folder="Database",
                 lyrics_folder="Database/lyrics",
                 model="qwen2.5-3b",  # Cambiado a Qwen2.5-7B
                 model_path=None,
                 use_gpu=False,
                 api_key=None,
                 indexador=None):
        
        print(f"\n🔧 Inicializando RAG Pipeline...")
        print(f"   Index path: {index_path}")
        print(f"   Modelo: {model}")
        
        self.retriever = RAGRetriever(index_path=index_path,
                                      data_folder=data_folder,
                                      lyrics_folder=lyrics_folder,
                                      indexador=indexador)
        self.generator = RAGGenerator(
            model=model, 
            model_path=model_path,
            use_gpu=use_gpu,
            api_key=api_key
        )

    def answer(self, query, top_k=3, max_tokens=512, temperature=0.3):
        print(f"\n🔍 RAG - Procesando consulta: {query[:50]}...")
        
        resultados = self.retriever.retrieve(query, top_k=top_k)
        
        if not resultados:
            return "No se encontraron documentos relevantes.", []
        
        contexts = [doc["contexto"] for doc in resultados]
        answer = self.generator.generate_answer(query, contexts,
                                                max_tokens=max_tokens,
                                                temperature=temperature)
        return answer, resultados