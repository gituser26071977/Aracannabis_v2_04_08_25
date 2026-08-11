"""Testes do GatewayLLMProvider (F4 — adoção de araos/intelligence).

Valida que a camada assíncrona roteia pelo LLM Gateway (porta única de
egress auditada) respeitando o contrato `LLMProvider`.
"""

from __future__ import annotations

import asyncio

from araos.intelligence.llm import LLMMessage, LLMRequest, MessageRole
from araos.intelligence.providers.gateway_provider import GatewayLLMProvider


class FakeClient:
    def __init__(self, result: dict | None = None) -> None:
        self.result = result or {
            "output": {"text": "resposta gateway"},
            "tokens_used": 42,
            "provider": "deepseek",
            "status": "success",
            "via_gateway": True,
        }
        self.calls: list[dict] = []

    def generate(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return self.result


def _request(messages: list[str]) -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role=MessageRole.USER, content=m) for m in messages
        ]
    )


class TestGatewayLLMProvider:
    def REDACTED(self):
        client = FakeClient()
        provider = GatewayLLMProvider(client=client, tenant_id=7)

        resp = asyncio.run(provider.complete(_request(["ola medico"])))

        assert resp.content == "resposta gateway"
        assert resp.metadata["via_gateway"] is True
        assert resp.metadata["provider"] == "deepseek"
        assert resp.usage["total_tokens"] == 42

        call = client.calls[0]
        assert call["tenant_id"] == 7
        assert "ola medico" in call["anonymized_text"]
        assert call["provider"] == "deepseek"

    def test_provider_for_model_mapping(self):
        assert GatewayLLMProvider._provider_for_model(None) == "deepseek"
        assert GatewayLLMProvider._provider_for_model("gpt-4o") == "openai"
        assert GatewayLLMProvider._provider_for_model("claude-3") == "anthropic"
        assert GatewayLLMProvider._provider_for_model("glm-4-plus") == "zhipu"
        assert GatewayLLMProvider._provider_for_model("gemini-2.5") == "zhipu"

    def test_embed_returns_placeholder(self):
        client = FakeClient()
        provider = GatewayLLMProvider(client=client)
        emb = asyncio.run(provider.embed("texto"))
        assert len(emb) == 768

    def test_get_models(self):
        client = FakeClient()
        provider = GatewayLLMProvider(client=client)
        assert "deepseek-chat" in provider.get_models()


class TestBuilder:
    def test_build_intelligence_runtime(self):
        from araos.platform.sdk import build_intelligence_runtime

        runtime = build_intelligence_runtime(tenant_id=1)
        assert runtime is not None
        assert runtime.router.get_provider("gateway") is not None
        assert runtime.router.get_provider("mock") is not None

    def test_build_with_fallback(self):
        from araos.platform.sdk import build_intelligence_runtime

        runtime = build_intelligence_runtime(
            tenant_id=1, fallback_provider="in-process"
        )
        assert runtime.router.get_provider("in-process") is not None
