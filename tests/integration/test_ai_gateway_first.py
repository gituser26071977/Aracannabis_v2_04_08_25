"""Testes do gateway-first no AIProviderManager (F4 — migração LLM).

Cobre:
    - Com LLM_GATEWAY_URL configurado, chat_completion tenta o gateway primeiro.
    - Gateway indisponível → fallback in-process.
    - Sem LLM_GATEWAY_URL → comportamento in-process original.
"""

from __future__ import annotations

import threading

import requests


class FakeResponse:
    def __init__(self, status: int, json_body: dict | None = None) -> None:
        self.status_code = status
        self._json = json_body or {}

    def json(self) -> dict:
        return self._json


class RecordingSession:
    def __init__(self, status: int = 200, body: dict | None = None) -> None:
        self.status = status
        self.body = body
        self.posted: list[tuple[str, dict]] = []
        self._lock = threading.Lock()

    def post(self, url: str, json: dict, timeout: float) -> FakeResponse:
        with self._lock:
            self.posted.append((url, json))
        return FakeResponse(self.status, self.body)


def REDACTED(monkeypatch):
    from services import ai_agents as mod

    monkeypatch.setenv("LLM_GATEWAY_URL", "http://gw:8000")
    session = RecordingSession(
        status=200,
        body={
            "output": {"text": "resposta do gateway"},
            "tokens_used": 10,
            "provider": "deepseek",
            "status": "success",
        },
    )
    # _try_gateway faz `import requests` lazy; patcha o módulo global.
    monkeypatch.setattr("requests.post", session.post)

    manager = mod.AIProviderManager()
    # Evita custo de fallback real caso o gateway falhe
    manager.get_available_providers = lambda: []  # type: ignore[method-assign]

    result = manager.chat_completion(
        messages=[{"role": "user", "content": "oi"}], provider="deepseek"
    )
    assert result.get("via_gateway") is True
    assert result.get("content") == "resposta do gateway"
    url, payload = session.posted[0]
    assert url == "http://gw:8000/generate"
    assert payload["anonymized_text"] == "oi"


def REDACTED(monkeypatch):
    from services import ai_agents as mod

    monkeypatch.setenv("LLM_GATEWAY_URL", "http://gw:8000")

    class BrokenSession:
        def post(self, *args, **kwargs):
            raise requests.ConnectionError("gw down")

    monkeypatch.setattr("requests.post", BrokenSession().post)

    manager = mod.AIProviderManager()
    # Fallback in-process: sem provedores reais, cai no fallback final
    manager.get_available_providers = lambda: []  # type: ignore[method-assign]
    manager._is_provider_available = lambda p: False  # type: ignore[method-assign]

    result = manager.chat_completion(
        messages=[{"role": "user", "content": "oi"}], provider="deepseek"
    )
    assert result.get("via_gateway") is None or result.get("via_gateway") is False
    assert result.get("content") or result.get("error")


def test_no_gateway_url_uses_inprocess(monkeypatch):
    from services import ai_agents as mod

    monkeypatch.delenv("LLM_GATEWAY_URL", raising=False)

    manager = mod.AIProviderManager()
    manager.get_available_providers = lambda: []  # type: ignore[method-assign]
    manager._is_provider_available = lambda p: False  # type: ignore[method-assign]

    result = manager.chat_completion(
        messages=[{"role": "user", "content": "oi"}], provider="deepseek"
    )
    # Sem gateway, nunca marca via_gateway
    assert result.get("via_gateway") is None
