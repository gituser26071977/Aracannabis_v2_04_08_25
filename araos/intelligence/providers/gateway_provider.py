"""
AraOS Intelligence — Gateway LLM Provider.

Conecta a camada assíncrona (`araos.intelligence`) ao LLM Gateway (única
porta de egress auditada com rate-limit + custo + auditoria).

Implementa o contrato `LLMProvider` (async) delegando ao
`services.llm_gateway_client.LLMGatewayClient`. Assim, os agentes
inteligentes (Concierge, Voice Copilot) usam a MESMA porta que o pipeline
SOAP — sem duplicar egress nem chaves de API no backend.

F4 — Decisão: ADOTAR `araos/intelligence` como camada assíncrona definitiva.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

from ..llm import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMMessage,
    MessageRole,
)


class GatewayLLMProvider(LLMProvider):
    """Provider que roteia para o LLM Gateway via LLMGatewayClient."""

    def __init__(
        self,
        client: Any | None = None,
        default_model: str = "deepseek-chat",
        default_task: str = "chat",
        tenant_id: Any = 0,
    ):
        # Lazy import para evitar ciclo: services → araos.intelligence
        if client is None:
            from services.llm_gateway_client import default_client

            client = default_client()
        self.client = client
        self.default_model = default_model
        self.default_task = default_task
        self.tenant_id = tenant_id

    def get_models(self) -> List[str]:
        return [self.default_model, "deepseek-reasoner", "glm-4-plus"]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        text = self._messages_to_text(request.messages)
        provider = self._provider_for_model(request.model)

        result = self.client.generate(
            anonymized_text=text,
            tenant_id=self.tenant_id,
            task=self.default_task,
            provider=provider,
        )

        return self._to_response(result)

    def _to_response(self, result: Dict[str, Any]) -> LLMResponse:
        """Constrói LLMResponse a partir do dict canônico do gateway/fallback."""
        content = self._extract_content(result)
        tokens = int(result.get("tokens_used", 0))

        return LLMResponse(
            content=content,
            model=result.get("provider", self.default_model),
            usage={
                "prompt_tokens": 0,
                "completion_tokens": tokens,
                "total_tokens": tokens,
            },
            finish_reason="stop",
            metadata={
                "provider": result.get("provider", self.default_model),
                "via_gateway": result.get("via_gateway", False),
                "gateway_status": result.get("status", "unknown"),
            },
        )

    async def stream(self, request: LLMRequest):
        response = await self.complete(request)
        for word in response.content.split():
            yield word + " "

    async def embed(self, text: str) -> List[float]:
        # Gateway atual não expõe embeddings; contrato preparado para futuro.
        return [0.0] * 768

    # ─── Internals ────────────────────────────────────────────────────

    @staticmethod
    def _messages_to_text(messages: List[LLMMessage]) -> str:
        """Serializa mensagens para o texto anonimizado do gateway."""
        parts: List[str] = []
        for m in messages:
            role = m.role.value if isinstance(m.role, MessageRole) else str(m.role)
            parts.append(f"{role}: {m.content}")
        return "\n".join(parts)

    @staticmethod
    def _provider_for_model(model: Optional[str]) -> str:
        if not model:
            return "deepseek"
        lowered = model.lower()
        if "gemini" in lowered or "zhipu" in lowered or "glm" in lowered:
            return "zhipu"
        if "claude" in lowered:
            return "anthropic"
        if "gpt" in lowered:
            return "openai"
        return "deepseek"

    @staticmethod
    def _extract_content(result: Dict[str, Any]) -> str:
        output = result.get("output")
        if isinstance(output, dict):
            return str(output.get("text", ""))
        if isinstance(output, str):
            return output
        return str(output)
