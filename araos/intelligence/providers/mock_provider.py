"""
AraOS Intelligence — Mock LLM Provider.

Provider de testes. Não faz chamadas de rede.
Responde de forma determinística baseada no conteúdo da requisição.
"""

from typing import List, Dict, Any

from ..llm import LLMProvider, LLMRequest, LLMResponse, LLMMessage, MessageRole


class MockLLMProvider(LLMProvider):
    """
    Provider mock para testes.
    
    Uso:
        provider = MockLLMProvider()
        response = await provider.complete(request)
        # → LLMResponse com conteúdo baseado nas mensagens
    """
    
    def __init__(self, default_response: str = "[MockLLM resposta padrão]"):
        self.default_response = default_response
        self.call_history: List[LLMRequest] = []
    
    def get_models(self) -> List[str]:
        return ["mock-model"]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        self.call_history.append(request)
        
        # Heurística simples para respostas determinísticas
        last_message = request.messages[-1].content if request.messages else ""
        
        content = self._generate_response(last_message)
        
        return LLMResponse(
            content=content,
            model="mock-model",
            usage={"prompt_tokens": len(last_message.split()), "completion_tokens": len(content.split()), "total_tokens": len(last_message.split()) + len(content.split())},
            finish_reason="stop",
            metadata={"provider": "mock", "mode": "test"},
        )
    
    async def stream(self, request: LLMRequest):
        response = await self.complete(request)
        for word in response.content.split():
            yield word + " "
    
    async def embed(self, text: str) -> List[float]:
        return [0.1] * 768
    
    def _generate_response(self, message: str) -> str:
        """Gera resposta determinística baseada na mensagem."""
        msg_lower = message.lower()
        
        if "resumo" in msg_lower or "summary" in msg_lower:
            return "Aqui está o resumo clínico do paciente."
        if "medicamento" in msg_lower or "medication" in msg_lower:
            return "O paciente está tomando Losartana 50mg 1x ao dia."
        if "alergia" in msg_lower or "allergy" in msg_lower:
            return "O paciente tem alergia a Penicilina (moderada)."
        if "diagnóstico" in msg_lower or "diagnosis" in msg_lower:
            return "O paciente tem Hipertensão Arterial Sistêmica (I10)."
        if "agendamento" in msg_lower or "schedule" in msg_lower:
            return "Posso ajudar com o agendamento. Qual dia e horário prefere?"
        if "tontura" in msg_lower or "dor de cabeça" in msg_lower:
            return "Entendo que está sentindo tontura. Vou registrar seus sintomas para o médico."
        
        return self.default_response
