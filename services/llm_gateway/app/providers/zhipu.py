import httpx
import logging
from app.validation import validate_soap_response
from .deepseek import BaseLLMProvider

class ZhipuProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=45.0)
        self.logger = logging.getLogger("zhipu_provider")

    async def generate_completion(self, anonymized_text: str, task: str):
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
            system_prompt = "Responda como assistente médico seguro."

        user_prompt = f"RESUMO CLÍNICO:\n{anonymized_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        attempts = 0
        max_retries = 2
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
                        "model": "glm-4-plus", # Usando GLM-4 Plus conforme solicitado
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 1500
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)

                content_raw = data["choices"][0]["message"]["content"]
                
                # Zhipu pode retornar markdown ```json ... ```
                if content_raw.startswith("```json"):
                    content_raw = content_raw.strip("```json").strip("```").strip()
                elif content_raw.startswith("```"):
                    content_raw = content_raw.strip("```").strip()

                validated_json = validate_soap_response(content_raw)
                
                return {
                    "output": validated_json,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "provider": "zhipu"
                }

            except Exception as e:
                last_error = e
                attempts += 1
                if attempts < max_retries:
                    import asyncio
                    await asyncio.sleep(2)
        
        raise last_error or Exception("Zhipu provider failed")
