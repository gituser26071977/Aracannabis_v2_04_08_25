"""
AraOS Intelligence — Gemini Provider.

Implementação do LLMProvider para Google Gemini.

Em produção: usa google.generativeai
Em testes: pode usar MockLLMProvider
"""

from typing import List, Dict, Any, Optional
import time

from ..llm import LLMProvider, LLMRequest, LLMResponse, LLMMessage, MessageRole


class GeminiProvider(LLMProvider):
    """
    Provider para Google Gemini.
    
    Uso:
        provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))
        response = await provider.complete(request)
    
    Stub: se api_key não fornecida, retorna resposta mock.
    """
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.default_model = default_model
        self._client = None
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._client = genai
            except ImportError:
                pass
    
    def get_models(self) -> List[str]:
        return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self._client:
            return self._mock_response(request)
        
        start = time.perf_counter()
        
        model = self._client.GenerativeModel(request.model or self.default_model)
        
        # Converter mensagens para formato Gemini
        contents = []
        for m in request.messages:
            if m.role == MessageRole.SYSTEM:
                contents.append({"role": "user", "parts": [f"[System] {m.content}"]})
            elif m.role == MessageRole.USER:
                contents.append({"role": "user", "parts": [m.content]})
            elif m.role == MessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [m.content]})
        
        response = model.generate_content(contents)
        
        latency_ms = (time.perf_counter() - start) * 1000
        
        return LLMResponse(
            content=response.text,
            model=request.model or self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"latency_ms": latency_ms, "provider": "gemini"},
        )
    
    async def stream(self, request: LLMRequest):
        """Stream de tokens (preparação)."""
        if not self._client:
            yield "[mock stream]"
            return
        
        model = self._client.GenerativeModel(request.model or self.default_model)
        
        contents = []
        for m in request.messages:
            if m.role == MessageRole.USER:
                contents.append({"role": "user", "parts": [m.content]})
            elif m.role == MessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [m.content]})
        
        response = model.generate_content(contents, stream=True)
        for chunk in response:
            yield chunk.text
    
    async def embed(self, text: str) -> List[float]:
        if not self._client:
            return [0.0] * 768
        
        result = self._client.embed_content(
            model="models/embedding-001",
            content=text,
        )
        return result["embedding"]
    
    def _mock_response(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="[Gemini Provider Stub — modo simulação]",
            model=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"provider": "gemini", "mode": "stub"},
        )
