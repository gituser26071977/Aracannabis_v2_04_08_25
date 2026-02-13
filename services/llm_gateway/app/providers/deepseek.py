from datetime import datetime
import time
import httpx
import logging
from services.llm_gateway.app.validation import validate_soap_response

class BaseLLMProvider:
    async def generate_completion(self, anonymized_text: str, task: str) -> dict:
        raise NotImplementedError("Implementar na subclasse")

class DeepSeekProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = logging.getLogger("deepseek_provider")

    async def generate_completion(self, anonymized_text: str, task: str):
        # 1. Montar Prompt (Seguro - Sem logar)
        if task == "soap_summary":
            system_prompt = """
            Você é um assistente médico AI especializado em criar resumos SOAP estruturados.
            Receba o texto clínico (anonimizado) e extraia um resumo JSON com as chaves:
            - subjective: Queixas do paciente
            - objective: Sinais vitais e exames físicos
            - assessment: Diagnóstico e hipóteses
            - plan: Conduta, exames e prescrições
            
            Retorne APENAS o JSON válido, sem texto adicional.
            """
        else:
            # Fallback seguro
            system_prompt = "Responda como assistente médico seguro."

        user_prompt = f"RESUMO CLÍNICO:\n{anonymized_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 2. Request com Retry
        attempts = 0
        max_retries = 3
        last_error = None
        
        while attempts < max_retries:
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.1, # Determinístico
                        "max_tokens": 1500,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extrair Usage e Content
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)

                content_raw = data["choices"][0]["message"]["content"]
                
                # Validar Estrutura
                validated_json = validate_soap_response(content_raw)
                
                return {
                    "output": validated_json,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "provider": "deepseek"
                }

            except httpx.HTTPStatusError as e:
                # Se for 4xx (erro cliente), não retentar
                 if 400 <= e.response.status_code < 500:
                    self.logger.error(f"DeepSeek Client Error: {e}")
                    raise e
                 # Se for 5xx, retentar
                 last_error = e
            except Exception as e:
                last_error = e
                # Circuit breaker implícito: timeout ou connect error
            
            attempts += 1
            if attempts < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                import asyncio
                await asyncio.sleep(2 ** (attempts - 1))
        
        raise last_error or Exception("Max retries exceeded")
