"""Emitter de Clinical Events SIAP → AraOS (F2, wrap não-rewrite).

Quando um fluxo clínico do prontuário escreve (anamnese, evolução, exame,
dosagem, prescrição), o SIAP emite um ClinicalEvent canônico para o
event store do AraOS, que alimenta o Clinical Genome.

Princípios:
    - **Wrap, não rewrite**: o fluxo clínico original continua igual; a
      emissão acontece DEPOIS do commit, sem alterar o comportamento.
    - **Nunca lança**: se o AraOS estiver indisponível, registra e segue.
      O prontuário não pode ser bloqueado por uma integração.
    - **Config-gated**: desligado por padrão (env
      `CLINICAL_EVENTS_ENABLED=true` liga em produção).

Segurança: assinatura HMAC-SHA256 do corpo (X-AraOS-Signature), idêntica
ao consumidor AraOS (`POST /api/v1/clinical/events`).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_event(
    *,
    event_type: str,
    patient_id: str | int,
    tenant_id: str,
    payload: dict[str, Any],
    source: str = "siap",
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    uf: str | None = None,
    municipio: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """Monta o corpo canônico do ClinicalEvent (contrato ara-os/contracts)."""
    return {
        "id": f"{source}:{source_id or event_type}:{patient_id}",
        "type": event_type,
        "occurred_at": _now_iso(),
        "patient_id": str(patient_id),
        "tenant_id": tenant_id or "default",
        "source": source,
        "source_id": source_id,
        "evidence": [],
        "gene_expressions": [],
        "metadata": metadata or {},
        "uf": uf,
        "municipio": municipio,
        "region": region,
        **payload,
    }


class AraOSEventEmitter:
    """Publica Clinical Events para o AraOS via HTTP (fire-and-forget).

    Falha NUNCA bloqueia o fluxo clínico. Desabilitado por padrão.
    """

    def __init__(
        self,
        *,
        webhook_url: str = "",
        secret: str = "",
        enabled: bool = False,
        timeout: float = 5.0,
        session: requests.Session | None = None,
    ) -> None:
        self._url = webhook_url
        self._secret = secret
        self._enabled = enabled
        self._timeout = timeout
        self._session = session

    @property
    def enabled(self) -> bool:
        return self._enabled

    def emit(
        self,
        *,
        event_type: str,
        patient_id: str | int,
        tenant_id: str,
        payload: dict[str, Any],
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        uf: str | None = None,
        municipio: str | None = None,
        region: str | None = None,
    ) -> bool:
        """Emite um evento. Retorna True se publicado; nunca lança."""
        if not self._enabled or not self._url:
            return False

        event = build_event(
            event_type=event_type,
            patient_id=patient_id,
            tenant_id=tenant_id,
            payload=payload,
            source="siap",
            source_id=source_id,
            metadata=metadata,
            uf=uf,
            municipio=municipio,
            region=region,
        )
        raw = json.dumps(event, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._secret:
            sig = hmac.new(self._secret.encode(), raw, hashlib.sha256).hexdigest()
            headers["X-AraOS-Signature"] = sig

        try:
            requester = self._session or requests
            response = requester.post(self._url, headers=headers, content=raw, timeout=self._timeout)
            response.raise_for_status()
            return True
        except Exception as exc:  # noqa: BLE001 — nunca bloqueia o clínico
            logger.warning("araos_event_emit_failed: %s %s: %s", self._url, event_type, exc)
            return False


def default_emitter() -> AraOSEventEmitter:
    """Constrói o emitter a partir do ambiente (env-gated)."""
    return AraOSEventEmitter(
        webhook_url=os.getenv("AROS_WEBHOOK_URL", ""),
        secret=os.getenv("AROS_EVENT_SECRET", ""),
        enabled=os.getenv("CLINICAL_EVENTS_ENABLED", "false").lower() in ("1", "true", "yes"),
        timeout=float(os.getenv("AROS_EVENT_TIMEOUT", "5")),
    )
