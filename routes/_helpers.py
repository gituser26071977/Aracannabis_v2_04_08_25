"""
routes/_helpers.py — helpers compartilhados pelos blueprints Sprint 4.

Consolida utilitários que estavam duplicados em routes/neuro_registry.py
e agora são reusados por todos os blueprints intelligence_* (Sprint 4.1+).

Funções:
    _resolve_tenant_id()   — extrai tenant_id do header ou JWT.
    _get_actor_id()        — extrai user_id do JWT.
    _parse_isoformat_optional() — parse seguro de datas ISO 8601.
    _accepted()            — response helper para 202.
    get_logger(name)       — StructuredLogger do observability layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity


def _resolve_tenant_id() -> str:
    """Extrai tenant_id do header X-Association-ID / X-Tenant-ID ou do JWT."""
    from_header = (
        request.headers.get("X-Association-ID")
        or request.headers.get("X-Tenant-ID")
    )
    if from_header:
        return from_header
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            tid = identity.get("tenant_id") or identity.get("organization_id")
            if tid:
                return str(tid)
    except Exception:
        pass
    return ""


def _get_actor_id() -> Optional[str]:
    """Extrai user_id (actor) do JWT identity."""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            return str(identity.get("user_id") or identity.get("id") or "")
        return str(identity) if identity else None
    except Exception:
        return None


def _parse_isoformat_optional(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 string → datetime timezone-aware. None se vazio/inválido."""
    if not value:
        return None
    try:
        v = value
        if v.endswith("Z"):
            v = v[:-1] + "+00:00"
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _accepted(result) -> tuple:
    """Response 202 Accepted padronizada."""
    return (
        jsonify({
            "event_id": getattr(result, "event_id", None),
            "event_type": getattr(result, "event_type", None),
            "occurred_at": (
                getattr(result, "occurred_at", datetime.now(timezone.utc)).isoformat()
                if hasattr(result, "occurred_at") else datetime.now(timezone.utc).isoformat()
            ),
        }),
        202,
    )


def get_logger(name: str):
    """StructuredLogger do observability layer (lazy import)."""
    try:
        from araos.clinical.observability import get_logger as _g
        return _g(name)
    except ImportError:
        import logging
        return logging.getLogger(name)