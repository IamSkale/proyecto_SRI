try:
    import openai
    import os
    try:
        from openai import OpenAI
    except ImportError:
        OpenAI = None
except ImportError:
    openai = None
    OpenAI = None


class RAGGenerator:
    """Genera respuestas usando DeepSeek o un LLM con fallback."""

    def __init__(self, model="deepseek-chat", api_key=None):
        self.model = model
        self.api_key = None
        
        # Prioridad: 1. parámetro, 2. variable de entorno
        if api_key:
            self.api_key = api_key.strip()
        else:
            env_key = os.environ.get('DEEPSEEK_API_KEY', '').strip()
            if env_key:
                self.api_key = env_key
        
        self.openai_available = openai is not None
        self.client = None

        print(f"🔍 Debug - API Key presente: {self.api_key is not None and len(self.api_key) > 0}")
        print(f"🔍 Debug - openai instalado: {self.openai_available}")
        print(f"🔍 Debug - OpenAI clase disponible: {OpenAI is not None}")

        if not self.api_key:
            print("⚠️  DEEPSEEK_API_KEY no configurada. Usando fallback.")
            return

        if not self.openai_available:
            print("⚠️  openai no instalada. Usando fallback.")
            return

        if OpenAI is None:
            print("⚠️  OpenAI client no disponible. Usando fallback.")
            return

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1",
                timeout=30
            )
            print(f"✅ Cliente DeepSeek inicializado correctamente (modelo: {self.model})")
        except Exception as e:
            print(f"❌ Error al inicializar cliente DeepSeek: {e}")
            self.client = None

    def generate_answer(self, query, contexts, max_tokens=256, temperature=0.3):
        if not query:
            return ""

        print(f"🔍 Debug - Generando respuesta para: {query[:50]}...")
        print(f"🔍 Debug - Contextos: {len(contexts)} documentos")

        if self.openai_available and self.client is not None:
            try:
                prompt = self._build_prompt(query, contexts)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto en música. Usa la información de contexto para responder de forma precisa."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                answer = response.choices[0].message.content.strip()
                print("✅ Respuesta generada exitosamente")
                return answer
                
            except Exception as e:
                print(f"❌ Error en API de DeepSeek: {e}")
                return self._fallback_answer(query, contexts, error=str(e))
        
        print("⚠️ Usando fallback (sin DeepSeek)")
        return self._fallback_answer(query, contexts)

    def _build_prompt(self, query, contexts):
        contexto_texto = "\n\n---\n\n".join(
            [f"Documento {i + 1}:\n{context[:1000]}" for i, context in enumerate(contexts)]
        )
        prompt = (
            f"Consulta: {query}\n\n"
            f"Usa los siguientes documentos como contexto y responde de manera concisa:\n\n"
            f"{contexto_texto}\n\n"
            f"Si la respuesta no puede inferirse claramente, indica que la información no es suficiente."  
        )
        return prompt

    def _fallback_answer(self, query, contexts, error=None):
        mensaje = []
        
        if error:
            mensaje.append(f"⚠️ No se pudo usar DeepSeek: {error}")
        else:
            mensaje.append("⚠️ DeepSeek no está disponible.")
        
        mensaje.append(f"\n📝 Consulta original: {query}")
        mensaje.append("\n📚 Documentos recuperados:\n")
        
        for i, context in enumerate(contexts[:3], 1):
            mensaje.append(f"[Documento {i}]\n{context[:500]}...\n")
        
        mensaje.append("\n💡 Para activar DeepSeek, configura la variable de entorno DEEPSEEK_API_KEY")
        
        return "\n".join(mensaje)