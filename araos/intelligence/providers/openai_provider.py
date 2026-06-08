"""
AraOS Intelligence — OpenAI Provider.

Implementação do LLMProvider para OpenAI GPT.

Em produção: usa openai.AsyncOpenAI
Em testes: pode usar MockLLMProvider
"""

from typing import List, Dict, Any, Optional
import time

from ..llm import LLMProvider, LLMRequest, LLMResponse, LLMMessage, MessageRole


class OpenAIProvider(LLMProvider):
    """
    Provider para OpenAI GPT.
    
    Uso:
        provider = OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY"))
        response = await provider.complete(request)
    
    Stub: se api_key não fornecida, retorna resposta mock.
    """
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.default_model = default_model
        self.client = None
        
        if api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
            except ImportError:
                pass
    
    def get_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.client:
            return self._mock_response(request)
        
        start = time.perf_counter()
        
        messages = [
            {"role": m.role.value, "content": m.content}
            for m in request.messages
        ]
        
        response = await self.client.chat.completions.create(
            model=request.model or self.default_model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        latency_ms = (time.perf_counter() - start) * 1000
        
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
            metadata={"latency_ms": latency_ms, "provider": "openai"},
        )
    
    async def stream(self, request: LLMRequest):
        """Stream de tokens (preparação)."""
        if not self.client:
            yield "[mock stream]"
            return
        
        messages = [
            {"role": m.role.value, "content": m.content}
            for m in request.messages
        ]
        
        stream = await self.client.chat.completions.create(
            model=request.model or self.default_model,
            messages=messages,
            temperature=request.temperature,
            stream=True,
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def embed(self, text: str) -> List[float]:
        if not self.client:
            return [0.0] * 1536
        
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    
    def _mock_response(self, request: LLMRequest) -> LLMResponse:
        """Resposta mock quando não há API key."""
        return LLMResponse(
            content="[OpenAI Provider Stub — modo simulação]",
            model=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"provider": "openai", "mode": "stub"},
        )
