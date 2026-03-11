import httpx
import logging
from app.validation import validate_soap_response
from .deepseek import BaseLLMProvider

class GoogleProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Base URL do Gemini (Native API)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.client = httpx.AsyncClient(timeout=40.0)
        self.logger = logging.getLogger("google_provider")

    async def generate_completion(self, anonymized_text: str, task: str):
        # Gemini usa um formato de prompt diferente do OpenAI na API nativa
        if task == "soap_summary":
            instruction = """
            Você é um assistente médico AI especializado em criar resumos SOAP estruturados.
            Receba o texto clínico (anonimizado) e extraia um resumo JSON com as chaves:
            - subjective: Queixas do paciente
            - objective: Sinais vitais e exames físicos
            - assessment: Diagnóstico e hipóteses
            - plan: Conduta, exames e prescrições
            
            Retorne APENAS o JSON válido, sem texto adicional.
            """
        else:
            instruction = "Responda como assistente médico seguro."

        prompt = f"{instruction}\n\nRESUMO CLÍNICO:\n{anonymized_text}"

        attempts = 0
        max_retries = 2
        last_error = None
        
        # Modelo solicitado: gemini-1.5-flash
        model = "gemini-1.5-flash"
        
        while attempts < max_retries:
            try:
                # Endpoint nativo para Gemini
                url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
                
                response = await self.client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 2048,
                            "responseMimeType": "application/json"
                        }
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extrair conteúdo (Gemini response format)
                # data['candidates'][0]['content']['parts'][0]['text']
                content_raw = data['candidates'][0]['content']['parts'][0]['text']
                
                # Gemini pode ser verboso; sanitizar
                if content_raw.startswith("```json"):
                    content_raw = content_raw.strip("```json").strip("```").strip()
                elif content_raw.startswith("```"):
                    content_raw = content_raw.strip("```").strip()

                validated_json = validate_soap_response(content_raw)
                
                # Nota: Gemini API nativa v1beta não retorna tokens de forma simples no generateContent padrão?
                # Na verdade retorna em 'usageMetadata'
                usage = data.get("usageMetadata", {})
                tokens_input = usage.get("promptTokenCount", 0)
                tokens_output = usage.get("candidatesTokenCount", 0)

                return {
                    "output": validated_json,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "provider": "google"
                }

            except Exception as e:
                self.logger.error(f"Google API Error: {str(e)}")
                last_error = e
                attempts += 1
                if attempts < max_retries:
                    import asyncio
                    await asyncio.sleep(2)
        
        raise last_error or Exception("Google provider failed")
