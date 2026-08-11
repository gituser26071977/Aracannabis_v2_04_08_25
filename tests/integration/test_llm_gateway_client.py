"""Testes do cliente do LLM Gateway (F4 — migração).

Cobre:
    - generate via gateway (200) → output canônico com via_gateway=True
    - generate com erro HTTP → fallback in-process
    - generate com falha de rede → fallback in-process
    - fallback ausente → retorna status error sem lançar
"""

from __future__ import annotations

import threading

import requests

from services.llm_gateway_client import LLMGatewayClient


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
        self.posted: list[tuple[str, dict, int | None]] = []
        self._lock = threading.Lock()

    def post(self, url: str, json: dict, timeout: float) -> FakeResponse:
        with self._lock:
            self.posted.append((url, json, timeout))
        return FakeResponse(self.status, self.body)


def _fallback(text: str, task: str) -> dict:
    return {"text": f"[in-process] {task}: {text[:10]}"}


class TestGenerate:
    def test_gateway_ok(self):
        session = RecordingSession(
            status=200,
            body={
                "output": {"summary": "SOAP ok"},
                "tokens_used": 120,
                "provider": "deepseek",
                "processing_time_ms": 800,
                "status": "success",
            },
        )
        client = LLMGatewayClient(base_url="http://gw", session=session, fallback=_fallback)
        result = client.generate(
            anonymized_text="texto anonimo",
            tenant_id=5,
            task="soap_summary",
            provider="deepseek",
        )
        assert result["via_gateway"] is True
        assert result["output"] == {"summary": "SOAP ok"}
        assert result["tokens_used"] == 120
        assert result["provider"] == "deepseek"
        url, payload, timeout = session.posted[0]
        assert url == "http://gw/generate"
        assert payload["tenant_id"] == 5
        assert payload["anonymized_text"] == "texto anonimo"
        assert payload["task"] == "soap_summary"
        assert payload["provider"] == "deepseek"
        assert timeout == 45

    def test_http_error_falls_back(self):
        session = RecordingSession(status=503)
        client = LLMGatewayClient(base_url="http://gw", session=session, fallback=_fallback)
        result = client.generate(anonymized_text="x", tenant_id=1, task="chat")
        assert result["via_gateway"] is False
        assert result["status"] == "fallback"
        assert result["provider"] == "in-process"
        assert result["output"]["text"].startswith("[in-process]")

    def test_network_error_falls_back(self):
        class BrokenSession:
            def post(self, *args, **kwargs):
                raise requests.ConnectionError("down")

        client = LLMGatewayClient(base_url="http://gw", session=BrokenSession(), fallback=_fallback)
        result = client.generate(anonymized_text="x", tenant_id=1)
        assert result["via_gateway"] is False
        assert result["status"] == "fallback"

    def REDACTED(self):
        session = RecordingSession(status=503)
        client = LLMGatewayClient(base_url="http://gw", session=session, fallback=None)
        result = client.generate(anonymized_text="x", tenant_id=1)
        assert result["via_gateway"] is False
        assert result["status"] == "error"
        assert "error" in result

    def test_default_base_url_from_env(self, monkeypatch):
        monkeypatch.setenv("LLM_GATEWAY_URL", "http://gw-env:9999")
        client = LLMGatewayClient(fallback=_fallback)
        assert client.base_url == "http://gw-env:9999"
