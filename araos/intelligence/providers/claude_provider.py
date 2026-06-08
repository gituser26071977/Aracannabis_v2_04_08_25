"""
AraOS Intelligence — Claude Provider.

Implementação stub do LLMProvider para Anthropic Claude.

Pronto para integração futura. Hoje funciona em modo stub.
"""

from typing import List, Dict, Any, Optional

from ..llm import LLMProvider, LLMRequest, LLMResponse


class ClaudeProvider(LLMProvider):
    """
    Provider para Anthropic Claude (stub).
    
    Uso futuro:
        provider = ClaudeProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = await provider.complete(request)
    """
    
    def __init__(self, api_key: Optional[str] = None, default_model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.default_model = default_model
    
    def get_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]
    
    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="[Claude Provider Stub — integração futura]",
            model=self.default_model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            finish_reason="stop",
            metadata={"provider": "claude", "mode": "stub"},
        )
    
    async def stream(self, request: LLMRequest):
        yield "[Claude Provider Stub — stream não implementado]"
    
    async def embed(self, text: str) -> List[float]:
        return [0.0] * 1024
