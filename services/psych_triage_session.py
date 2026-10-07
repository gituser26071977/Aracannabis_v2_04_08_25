"""Sessão do agente de triagem psiquiátrica.

Persistência de estado com Redis (quando disponível) e fallback em memória
para desenvolvimento/testes. Uma sessão guarda as respostas parciais e o
contexto do paciente.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

STATE_EXPIRY = 3600
_REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")

_memory: Dict[str, Dict[str, Any]] = {}
_client: Optional[Any] = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    try:
        import redis

        client = redis.Redis(host=_REDIS_HOST, port=6379, db=0, decode_responses=True)
        client.ping()
        _client = client
    except Exception as exc:  # noqa: BLE001
        logger.warning("psych_triage_session sem Redis, usando memória: %s", exc)
        _client = None
    return _client


def new_session(tenant_id: str, patient_id: Optional[str] = None, version: str = "latest") -> str:
    session_id = uuid.uuid4().hex[:16]
    set_state(
        session_id,
        {
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "version": version,
            "answers": {},
            "history": [],
            "done": False,
            "response_id": None,
        },
    )
    return session_id


def get_state(session_id: str) -> Optional[Dict[str, Any]]:
    client = _get_client()
    if client is not None:
        raw = client.get(f"psych_triage:{session_id}")
        return json.loads(raw) if raw else None
    return _memory.get(session_id)


def set_state(session_id: str, state: Dict[str, Any]) -> None:
    client = _get_client()
    if client is not None:
        client.set(f"psych_triage:{session_id}", json.dumps(state), ex=STATE_EXPIRY)
    else:
        _memory[session_id] = state


def clear() -> None:
    _memory.clear()
