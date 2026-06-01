import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("⚠️ llama-cpp-python no instalado. Ejecuta: pip install llama-cpp-python")


class RAGGenerator:    
    # Opciones de modelo
    MODEL_OPTIONS = {
        "qwen2.5-3b": {
            "name": "Qwen2.5-3B-Instruct",
            "gguf": "qwen2.5-3b-instruct-q4_k_m.gguf",  # Cuantizado a 4-bit
            "hf_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
            "context": 131072,  # 128K context
            "ram_gb": 6,  # Aprox con cuantización 4-bit
        },
        "qwen2.5-3b": {
            "name": "Qwen2.5-3B-Instruct", 
            "gguf": "qwen2.5-3b-instruct-q4_k_m.gguf",
            "hf_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
            "context": 32768,
            "ram_gb": 3,
        },
        "qwen2.5-1.5b": {
            "name": "Qwen2.5-1.5B-Instruct",
            "gguf": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "hf_id": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
            "context": 32768,
            "ram_gb": 2,
        },
        "phi-3.5-mini": {
            "name": "Phi-3.5-mini-Instruct",
            "gguf": "Phi-3.5-mini-instruct-q4_k_m.gguf",
            "hf_id": "microsoft/Phi-3.5-mini-instruct-GGUF",
            "context": 131072,
            "ram_gb": 4,
        }
    }
    
    def __init__(self, model="qwen2.5-3b", model_path=None, use_gpu=False, api_key=None):
        self.model_name = model
        self.model = None
        self.use_gpu = use_gpu
        
        if model_path:
            self.model_path = Path(model_path)
        else:
            model_info = self.MODEL_OPTIONS.get(model, self.MODEL_OPTIONS["qwen2.5-3b"])
            self.model_path = Path("models") / model_info["gguf"]
            self.model_info = model_info
        
        print(f"\n🤖 Inicializando generador con {model_info['name'] if hasattr(self, 'model_info') else model}")
        print(f"   Model path: {self.model_path}")
        print(f"   GPU activada: {use_gpu}")
        
        if not self._cargar_modelo():
            print("⚠️ No se pudo cargar modelo local. Usando fallback.")

    def _cargar_modelo(self):        
        if LLAMA_AVAILABLE:
            try:
                if not self.model_path.exists():
                    print(f"❌ Archivo de modelo no encontrado: {self.model_path}")
                    print(f"\n📥 Para descargar el modelo:")
                    print(f"   1. Ve a Hugging Face: {self.model_info['hf_id']}")
                    print(f"   2. Descarga el archivo: {self.model_info['gguf']}")
                    print(f"   3. Colócalo en la carpeta: models/")
                    print(f"\n   Alternativa con wget:")
                    print(f"   mkdir -p models")
                    print(f"   cd models")
                    print(f"   wget https://huggingface.co/{self.model_info['hf_id']}/resolve/main/{self.model_info['gguf']}")
                    return False
                
                print(f"   📂 Cargando modelo desde {self.model_path}...")
                print(f"   ⏳ Esto puede tomar unos minutos la primera vez...")
                
                # Configuración para llama-cpp
                n_gpu_layers = -1 if self.use_gpu else 0  # -1 = todas las capas en GPU
                
                self.model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=self.model_info.get("context", 8192),
                    n_threads=8,  # Número de threads de CPU
                    n_gpu_layers=n_gpu_layers,
                    verbose=False,
                    seed=42,
                )
                print(f"   ✅ Modelo cargado exitosamente usando llama-cpp-python")
                print(f"   📊 Contexto: {self.model_info.get('context', 8192)} tokens")
                return True
                
            except Exception as e:
                print(f"   ❌ Error cargando con llama-cpp: {e}")
                print("   💡 Asegúrate de tener instalado: pip install llama-cpp-python")
        
        return False

    def generate_answer(self, query, contexts, max_tokens=512, temperature=0.3):
        if not query:
            return ""

        print(f"🔍 Generando respuesta para: {query[:50]}...")
        print(f"   Contextos: {len(contexts)} documentos")

        prompt = self._build_prompt(query, contexts)

        if self.model:
            try:
                response = self._generate_with_llama_cpp(prompt, max_tokens, temperature)
                if response:
                    print("✅ Respuesta generada exitosamente (Qwen2.5 local)")
                    return response
            except Exception as e:
                print(f"❌ Error generando respuesta: {e}")
        
        # Fallback
        print("⚠️ Usando fallback (sin modelo local)")
        return self._fallback_answer(query, contexts)

    def _generate_with_llama_cpp(self, prompt, max_tokens, temperature):
        formatted_prompt = self._format_qwen_chat(prompt)
        
        response = self.model(
            formatted_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|im_end|>", "<|endoftext|>"],
            echo=False,
        )
        
        return response['choices'][0]['text'].strip()

    def _format_qwen_chat(self, user_message):
        return f"""<|im_start|>system
Eres un asistente experto en música. Usa la información de contexto para responder de forma precisa y concisa.<|im_end|>
<|im_start|>user
{user_message}<|im_end|>
<|im_start|>assistant
"""

    def _build_prompt(self, query, contexts):
        """Construye el prompt para el modelo"""
        contexto_texto = "\n\n---\n\n".join(
            [f"Documento {i + 1}:\n{context[:1500]}" for i, context in enumerate(contexts)]
        )
        prompt = (
            f"Consulta: {query}\n\n"
            f"Usa los siguientes documentos como contexto para responder:\n\n"
            f"{contexto_texto}\n\n"
            f"Instrucciones:\n"
            f"1. Usa el contexto de las letras de canciones para responder\n"
            f"2. Si la información es insuficiente, indícalo claramente\n"
            f"3. Sé conciso pero completo\n"
            f"4. Si mencionas canciones, incluye artista y título\n\n"
            f"Respuesta:"
        )
        return prompt

    def _fallback_answer(self, query, contexts, error=None):
        mensaje = []
        
        if error:
            mensaje.append(f"⚠️ Error con modelo local: {error}")
        else:
            mensaje.append("⚠️ Modelo Qwen2.5 no disponible (archivo no encontrado o librería no instalada)")
        
        mensaje.append(f"\n📝 Consulta: {query}")
        mensaje.append("\n📚 Documentos recuperados:\n")
        
        for i, context in enumerate(contexts[:3], 1):
            # Mostrar información clave de cada documento
            lines = context.split('\n')
            titulo = next((l.replace('Título:', '').strip() for l in lines if l.startswith('Título:')), 'Sin título')
            artista = next((l.replace('Artista:', '').strip() for l in lines if l.startswith('Artista:')), 'Desconocido')
            mensaje.append(f"[{i}] {titulo} - {artista}")
        
        mensaje.append("\n💡 Para activar Qwen2.5 local:")
        mensaje.append("   1. Instala: pip install llama-cpp-python")
        mensaje.append("   2. Descarga el modelo GGUF a la carpeta models/")
        mensaje.append("   3. Reinicia la aplicación")
        
        return "\n".join(mensaje)