"""Cliente do LLM Gateway — porta única de egress auditada (F4).

Consolida a comunicação com `services/llm_gateway` (FastAPI, único serviço
com saída à internet no Docker). Hoje o único consumidor é o pipeline SOAP
(`routes/ai_clinical.py`), que montava o POST inline. Este cliente é o
ponto único:

    - Config-gated: `LLM_GATEWAY_URL` (default `http://llm_gateway:8000`).
    - **Nunca lança**: se o gateway estiver indisponível, retorna o
      resultado do fallback in-process (via `ai_manager.chat_completion`),
      seguindo a regra de ouro "o clínico nunca é bloqueado".
    - Contrato: `POST /generate` com `anonymized_text`, `task`, `provider`,
      `tenant_id` — mesmo shape do `LLMGenerateRequest` do gateway.

Uso:
    client = LLMGatewayClient()
    result = client.generate(
        anonymized_text=text,
        task="soap_summary",
        tenant_id=tenant_id,
        provider=provider,
    )
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


class LLMGatewayClient:
    """Cliente HTTP do LLM Gateway com fallback in-process."""

    def __init__(
        self,
        *,
        base_url: str = "",
        timeout: float = 45.0,
        session: requests.Session | None = None,
        fallback: Any | None = None,
    ) -> None:
        self._base_url = (base_url or os.getenv("LLM_GATEWAY_URL", "http://llm_gateway:8000")).rstrip("/")
        self._timeout = timeout
        self._session = session
        # fallback: callable(anonymized_text, task) → dict
        self._fallback = fallback

    @property
    def base_url(self) -> str:
        return self._base_url

    def generate(
        self,
        *,
        anonymized_text: str,
        tenant_id: Any,
        task: str = "soap_summary",
        provider: str = "deepseek",
        consultation_id: int | None = None,
    ) -> dict[str, Any]:
        """Chama o gateway. Em falha de rede, usa o fallback in-process.

        Returns dict com as chaves canônicas do `LLMGenerateResponse`:
        `output`, `tokens_used`, `provider`, `processing_time_ms`, `status`,
        e `via_gateway: bool` indicando a origem.
        """
        payload: dict[str, Any] = {
            "tenant_id": tenant_id,
            "anonymized_text": anonymized_text,
            "task": task,
            "provider": provider,
        }
        if consultation_id is not None:
            payload["consultation_id"] = consultation_id

        try:
            requester = self._session or requests
            response = requester.post(
                f"{self._base_url}/generate",
                json=payload,
                timeout=self._timeout,
            )
            if response.status_code != 200:
                logger.warning(
                    "llm_gateway_http_error: status=%s body=%s",
                    response.status_code, response.text[:200],
                )
                return self._fallback_generate(anonymized_text, task)

            data = response.json()
            return {
                "output": data.get("output", {}),
                "tokens_used": data.get("tokens_used", 0),
                "provider": data.get("provider", provider),
                "processing_time_ms": data.get("processing_time_ms", 0),
                "status": data.get("status", "success"),
                "via_gateway": True,
            }
        except Exception as exc:  # noqa: BLE001 — nunca bloqueia o fluxo
            logger.warning("llm_gateway_unavailable: %s", exc)
            return self._fallback_generate(anonymized_text, task)

    def _fallback_generate(self, anonymized_text: str, task: str) -> dict[str, Any]:
        """Fallback in-process via ai_manager (se fornecido)."""
        if self._fallback is None:
            return {
                "output": {"text": anonymized_text},
                "tokens_used": 0,
                "provider": "fallback",
                "processing_time_ms": 0,
                "status": "error",
                "via_gateway": False,
                "error": "LLM gateway indisponível e sem fallback configurado",
            }
        try:
            result = self._fallback(anonymized_text, task)
            return {
                "output": result,
                "tokens_used": 0,
                "provider": "in-process",
                "processing_time_ms": 0,
                "status": "fallback",
                "via_gateway": False,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("llm_gateway_fallback_failed: %s", exc)
            return {
                "output": {"text": anonymized_text},
                "tokens_used": 0,
                "provider": "fallback",
                "processing_time_ms": 0,
                "status": "error",
                "via_gateway": False,
                "error": str(exc),
            }


def default_client() -> LLMGatewayClient:
    """Constrói o cliente padrão (env-gated) com fallback ai_manager."""
    from services.ai_agents import ai_manager

    def _fallback(text: str, task: str) -> dict[str, Any]:
        provider = ai_manager.default_provider
        model = ai_manager.default_model
        result = ai_manager.chat_completion(
            messages=[{"role": "user", "content": text}],
            provider=provider,
            model=model,
        )
        return {"text": result.get("content", text)}

    return LLMGatewayClient(fallback=_fallback)
