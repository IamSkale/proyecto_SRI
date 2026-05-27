import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Intentar importar llama-cpp-python para modelos locales GGUF
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    print("⚠️ llama-cpp-python no instalado. Ejecuta: pip install llama-cpp-python")

# Intentar importar transformers (alternativa más pesada pero más flexible)
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class RAGGenerator:
    """Genera respuestas usando Qwen2.5-3B local o un LLM con fallback."""
    
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
        """
        Args:
            model: Nombre del modelo ('qwen2.5-7b', 'qwen2.5-3b', 'qwen2.5-1.5b', 'phi-3.5-mini')
            model_path: Ruta directa al archivo .gguf (opcional, sobreescribe model)
            use_gpu: Si es True, intenta usar GPU (requiere versión con CUDA de llama-cpp)
            api_key: Se ignora, mantenido por compatibilidad
        """
        self.model_name = model
        self.model = None
        self.use_gpu = use_gpu
        
        # Determinar la ruta del modelo
        if model_path:
            self.model_path = Path(model_path)
        else:
            # Buscar en carpeta models/ local
            model_info = self.MODEL_OPTIONS.get(model, self.MODEL_OPTIONS["qwen2.5-3b"])
            self.model_path = Path("models") / model_info["gguf"]
            self.model_info = model_info
        
        print(f"\n🤖 Inicializando generador con {model_info['name'] if hasattr(self, 'model_info') else model}")
        print(f"   Model path: {self.model_path}")
        print(f"   GPU activada: {use_gpu}")
        
        # Intentar cargar el modelo
        if not self._cargar_modelo():
            print("⚠️ No se pudo cargar modelo local. Usando fallback.")

    def _cargar_modelo(self):
        """Carga el modelo usando llama-cpp-python (recomendado) o transformers"""
        
        # Método 1: llama-cpp-python (más eficiente, recomendado)
        if LLAMA_AVAILABLE:
            try:
                # Verificar si el archivo existe
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
        
        # Método 2: transformers (alternativa más pesada)
        if TRANSFORMERS_AVAILABLE and not self.use_gpu:  # Solo si no forzamos GPU
            try:
                print(f"   📂 Cargando modelo con transformers...")
                print(f"   ⚠️ Este método usa más RAM (~12GB para 7B)")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    f"Qwen/{self.model_info['name']}" if hasattr(self, 'model_info') else "Qwen/Qwen2.5-3B-Instruct",
                    trust_remote_code=True
                )
                self.model_hf = AutoModelForCausalLM.from_pretrained(
                    f"Qwen/{self.model_info['name']}" if hasattr(self, 'model_info') else "Qwen/Qwen2.5-3B-Instruct",
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
                print(f"   ✅ Modelo cargado con transformers")
                return True
                
            except Exception as e:
                print(f"   ❌ Error cargando con transformers: {e}")
        
        return False

    def generate_answer(self, query, contexts, max_tokens=512, temperature=0.3):
        if not query:
            return ""

        print(f"🔍 Generando respuesta para: {query[:50]}...")
        print(f"   Contextos: {len(contexts)} documentos")

        prompt = self._build_prompt(query, contexts)

        # Usar modelo local si está cargado
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
        """Genera usando llama-cpp-python"""
        # Formato de chat para Qwen2.5
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
        """Formatea el mensaje para Qwen2.5 usando el formato de chat"""
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
            f"1. Responde basándote ÚNICAMENTE en la información proporcionada\n"
            f"2. Si la información es insuficiente, indícalo claramente\n"
            f"3. Sé conciso pero completo\n"
            f"4. Si mencionas canciones, incluye artista y título\n\n"
            f"Respuesta:"
        )
        return prompt

    def _fallback_answer(self, query, contexts, error=None):
        """Fallback cuando el modelo local no está disponible"""
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
    
    def get_model_info(self):
        """Retorna información del modelo actual"""
        if hasattr(self, 'model_info'):
            return {
                'cargado': self.model is not None,
                'nombre': self.model_info['name'],
                'contexto': self.model_info.get('context', 8192),
                'tamaño_ram': self.model_info.get('ram_gb', '?'),
                'archivo': str(self.model_path)
            }
        return {'cargado': False, 'nombre': self.model_name}