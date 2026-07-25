"""Knowledge API — observability hooks (request_id, correlation_id, latency, audit).

RC1 Gate 2 — REST translation layer.

Every request handled by the blueprint records:

- ``g.request_id``     — per-request UUID; returned via ``X-Request-ID``.
- ``g.correlation_id`` — inbound ``X-Correlation-ID`` header echo (or
  falls back to ``request_id``); returned via ``X-Correlation-ID``.
- ``g.started_monotonic`` — server-measured start time.
- ``g.user_id`` — JWT identity (when present); used for audit.
- ``g.tenant_id`` — populated by ``@tenant_required``.

Latency is appended to the response as ``X-Latency-MS`` and to the
``meta.latency_ms`` field of the response envelope.

A best-effort audit entry is written for every response whose status
code is >= 400 (errors) AND for 2xx writes (POST). Audit failures MUST
NEVER block the response.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from flask import Flask, g, request


logger = logging.getLogger("interfaces.rest.v1.observability")


# ─────────────────────────────────────────────────────────────────────
# Hook installation
# ─────────────────────────────────────────────────────────────────────

def register_request_hooks(app: Flask) -> None:
    """Install before/after request hooks on the given Flask app.

    The hooks are scoped to a path prefix (``/api/v1/knowledge``)
    so other blueprints are unaffected.

    Pattern: install a single ``before_request`` and ``after_request``
    that filter on ``request.path``. This avoids global hook collisions
    with the legacy 60+ blueprints registered in ``app_cors_livre.py``.
    """

    @app.before_request
    def _knowledge_before_request() -> None:
        if not request.path.startswith("/api/v1/knowledge"):
            return None
        g.request_id = str(uuid.uuid4())
        incoming = request.headers.get("X-Correlation-ID")
        g.correlation_id = (incoming.strip() if incoming else "") or g.request_id
        g.started_monotonic = time.monotonic()
        g.audit_action = _action_from_request()
        g.audit_resource_type = _resource_type_from_request()
        g.audit_resource_id = _resource_id_from_request()
        return None

    @app.after_request
    def _knowledge_after_request(response: Any) -> Any:
        if not request.path.startswith("/api/v1/knowledge"):
            return response
        # Latency
        started = getattr(g, "started_monotonic", None)
        latency_ms: float | None = None
        if started is not None:
            latency_ms = round((time.monotonic() - started) * 1000, 2)
            g.latency_ms = latency_ms

        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", "")
        if latency_ms is not None:
            response.headers["X-Latency-MS"] = f"{latency_ms:.2f}"
        # Audit (best-effort, never block)
        if _should_audit(response.status_code):
            _audit_best_effort(response, latency_ms)
        return response


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _action_from_request() -> str:
    method = request.method.upper()
    path = request.path.replace("/api/v1/knowledge", "").strip("/")
    verb_map = {
        "GET": "read",
        "POST": "execute",
        "PUT": "write",
        "PATCH": "write",
        "DELETE": "delete",
    }
    verb = verb_map.get(method, "access")
    return f"knowledge.{verb}.{path or 'root'}"


def _resource_type_from_request() -> str:
    p = request.path.replace("/api/v1/knowledge", "").strip("/")
    if not p:
        return "knowledge_root"
    parts = p.split("/")
    head = parts[0]
    return {"health": "health", "pipelines": "pipeline"}.get(head, head or "resource")


def _resource_id_from_request() -> str | None:
    p = request.path.replace("/api/v1/knowledge", "").strip("/")
    parts = [seg for seg in p.split("/") if seg]
    if len(parts) >= 2 and parts[0] != "pipelines":
        return parts[1]
    return None


def _should_audit(status_code: int) -> bool:
    if status_code >= 500:
        return True
    if 400 <= status_code < 500:
        return True  # 4xx errors (auth/perm/404) — record for audit
    if request.method.upper() == "POST":
        return True   # all writes
    return False


def _audit_best_effort(response: Any, latency_ms: float | None) -> None:
    """Write a single audit entry. NEVER raises."""
    try:
        from models_extra import create_audit_entry

        tenant_id_raw = getattr(g, "tenant_id", None) or getattr(
            g.get("current_association"), "id", None
        )
        if tenant_id_raw is None:
            tenant_id_raw = 0  # unknown tenant — still log, with tenant_id=0
        try:
            tenant_id_int = int(str(tenant_id_raw))
        except (TypeError, ValueError):
            tenant_id_int = 0

        actor = getattr(g, "user_id", None) or getattr(g, "jwt_identity", None)
        user_id_int = None
        try:
            if actor is not None:
                user_id_int = int(str(actor))
        except (TypeError, ValueError):
            user_id_int = None

        create_audit_entry(
            tenant_id=tenant_id_int,
            user_id=user_id_int,
            action=str(getattr(g, "audit_action", "knowledge.access")),
            resource_type=str(getattr(g, "audit_resource_type", "resource")),
            resource_id=getattr(g, "audit_resource_id", None),
            details={
                "request_id": getattr(g, "request_id", None),
                "correlation_id": getattr(g, "correlation_id", None),
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "method": request.method,
                "path": request.path,
            },
            ip=request.remote_addr,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.debug("audit failure (ignored): %s", exc)
