"""Knowledge API — auth decorators.

RC1 Gate 2 — REST translation layer.

This module exports two decorators used by every business endpoint:

- ``@tenant_required`` — JWT + tenant resolver.
  Wraps ``flask_jwt_extended.jwt_required()`` and pulls the active
  association from ``flask.g`` (populated by ``middleware/tenant_middleware.py``).
  Exposes ``g.tenant_id`` for downstream code (composition, repository).
  Returns 401 (not 403) on missing association so existence is not leaked.

- ``@require_permission`` — RBAC re-export.
  Reuses the existing decorator at ``routes/auth_decorators.py``.
  Multiple permissions are ORed (any of them passes).

Why these decorators?
- Centralize auth concerns.
- Force every route to be "born prepared for authentication, tenant,
  audit" (per the RC1 API directive).
- Keep handlers free of repeated ``@jwt_required()`` /
  ``g.current_association.id`` boilerplate.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

# Re-use the existing platform decorator (defined in routes/auth_decorators.py).
# routes/auth_decorators.py:73-120 already implements the OR-multiple-permissions
# semantics + admin bypass + standard 401/403/404 envelopes we want.
from routes.auth_decorators import require_permission as _platform_require_permission


logger = logging.getLogger("interfaces.rest.v1.auth")


# ─────────────────────────────────────────────────────────────────────
# Tenant resolution
# ─────────────────────────────────────────────────────────────────────

def _resolve_tenant_id() -> str | None:
    """Resolve the active tenant_id (str) from current request context.

    Priority order (deliberately JWT-authoritative — P0-12):
    1. ``g.current_association.id`` (populated by
       ``middleware/tenant_middleware.py`` — this is the platform's
       authoritative tenant, derived from the JWT-linked
       ``UsuarioAssociacao`` link).
    2. ``None`` (signals: caller has no active association).

    We NEVER consult ``X-Tenant-ID`` / ``X-Association-ID`` / request
    body for tenant resolution — those are spoofable vectors.
    """
    assoc = g.get("current_association")
    if assoc is None:
        return None
    return str(getattr(assoc, "id", None) or "") or None


# ─────────────────────────────────────────────────────────────────────
# @tenant_required
# ─────────────────────────────────────────────────────────────────────

def tenant_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator: requires JWT + active association for the current request.

    Behavior:
    - No JWT → ``flask_jwt_extended.jwt_required()`` returns 401.
    - Invalid JWT → 401 (delegated).
    - JWT valid but no active association → 401 ``TENANT_REQUIRED``
      (NOT 403 — to avoid leaking whether an association exists).
    - All else → exposes ``g.tenant_id`` (str) and proceeds to handler.

    Usage:
        @bp.route("/foo")
        @tenant_required
        def foo():
            tenant = g.tenant_id  # guaranteed non-empty here
            ...
    """
    @wraps(f)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Verify identity is present (jwt_required ensures g.user_identity exists)
        identity = get_jwt_identity()
        if not identity:
            from interfaces.rest.v1.errors import error_envelope, AUTH_REQUIRED
            return error_envelope(AUTH_REQUIRED, "Missing or invalid JWT", status=401)

        tenant_id = _resolve_tenant_id()
        if not tenant_id:
            from interfaces.rest.v1.errors import error_envelope, TENANT_REQUIRED
            logger.warning(
                "JWT identity %s has no active association — rejecting (401 TENANT_REQUIRED)",
                identity,
            )
            return error_envelope(
                TENANT_REQUIRED,
                "Active association required for this endpoint",
                status=401,
            )
        g.tenant_id = tenant_id
        return f(*args, **kwargs)

    return wrapper


# ─────────────────────────────────────────────────────────────────────
# @require_permission (re-export)
# ─────────────────────────────────────────────────────────────────────

# We re-export the platform decorator unchanged. Multiple permissions are
# ORed — any of them passes. Admin/superadmin users bypass entirely.
require_permission = _platform_require_permission


__all__ = [
    "tenant_required",
    "require_permission",
]
