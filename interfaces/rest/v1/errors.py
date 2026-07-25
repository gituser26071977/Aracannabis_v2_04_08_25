"""Knowledge API — error envelope, codes, blueprint error handlers.

RC1 Gate 2 — REST translation layer.

All API responses (success or failure) use the standard envelope:

    {
      "success": <bool>,
      "data": <...> | null,
      "error": {"code": <str>, "message": <str>, "details": [...]} | null,
      "meta": {"timestamp": <iso>, "request_id": <uuid>, "correlation_id": <str>, "latency_ms": <float>}
    }

Error codes are stable identifiers that clients can switch on. They are
documented in ``docs/OPENAPI.yaml`` under ``components.schemas.Error``.

Error envelopes are wrapped by ``register_error_handlers(bp)`` which
installs:
- a generic ``Exception`` handler that returns ``INTERNAL_ERROR`` 500
- an ``HTTPException`` handler that maps Werkzeug errors to envelopes

The blob ``success_response`` and ``error_response`` are borrowed from
``araos.platform.api.response`` (already used by ``routes/cannabis.py``,
``routes/twin.py``, ``routes/followup.py``); we re-export them here for
convenience.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from araos.platform.api.response import error_response as _platform_error_response
from araos.platform.api.response import success_response as _platform_success_response
from flask import Blueprint, Flask, jsonify
from werkzeug.exceptions import HTTPException


logger = logging.getLogger("interfaces.rest.v1.errors")


# ─────────────────────────────────────────────────────────────────────
# Error codes (stable identifiers — referenced from OPENAPI.yaml)
# ─────────────────────────────────────────────────────────────────────

# 400
INVALID_REQUEST = "INVALID_REQUEST"
VALIDATION_ERROR = "VALIDATION_ERROR"

# 401
AUTH_REQUIRED = "AUTH_REQUIRED"
TENANT_REQUIRED = "TENANT_REQUIRED"

# 403
PERMISSION_DENIED = "PERMISSION_DENIED"

# 404
GENOME_NOT_FOUND = "GENOME_NOT_FOUND"
COHORT_NOT_FOUND = "COHORT_NOT_FOUND"
RESEARCH_SESSION_NOT_FOUND = "RESEARCH_SESSION_NOT_FOUND"
PATIENT_NOT_FOUND = "PATIENT_NOT_FOUND"

# 500 / 503
INTERNAL_ERROR = "INTERNAL_ERROR"
SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# ─────────────────────────────────────────────────────────────────────
# Helpers — thin wrappers around platform envelope (records meta + logs)
# ─────────────────────────────────────────────────────────────────────

def success_envelope(
    data: Any,
    *,
    status: int = 200,
    meta_extra: Mapping[str, Any] | None = None,
) -> tuple[Any, int]:
    """Return the standard success envelope (delegates to platform helper).

    Adds ``latency_ms`` to ``meta`` when present in flask.g (set by
    observability.before_request_hook / after_request_hook).
    """
    try:
        from flask import g
        meta_extra = dict(meta_extra or {})
        if hasattr(g, "started_monotonic"):
            import time
            meta_extra.setdefault(
                "latency_ms",
                round((time.monotonic() - g.started_monotonic) * 1000, 2),
            )
        meta_extra.setdefault("request_id", getattr(g, "request_id", None))
        meta_extra.setdefault("correlation_id", getattr(g, "correlation_id", None))
    except Exception:
        pass
    return _platform_success_response(data=data, meta=meta_extra, status=status)


def error_envelope(
    code: str,
    message: str,
    *,
    status: int = 400,
    details: list | None = None,
) -> tuple[Any, int]:
    """Return the standard error envelope (delegates to platform helper)."""
    return _platform_error_response(
        code=code, message=message, status=status, details=details or []
    )


# ─────────────────────────────────────────────────────────────────────
# Blueprint-local error handler registration
# ─────────────────────────────────────────────────────────────────────

def _http_exception_to_envelope(exc: HTTPException):
    """Map a Werkzeug HTTPException to one of our known error codes."""
    code_map = {
        400: VALIDATION_ERROR,
        401: AUTH_REQUIRED,
        403: PERMISSION_DENIED,
        404: GENOME_NOT_FOUND,         # any 404 from below is a not-found
        405: INVALID_REQUEST,
        409: INVALID_REQUEST,
        413: INVALID_REQUEST,
        415: INVALID_REQUEST,
        422: VALIDATION_ERROR,
        429: INVALID_REQUEST,
        500: INTERNAL_ERROR,
        503: SERVICE_UNAVAILABLE,
    }
    code = code_map.get(exc.code or 0, INVALID_REQUEST)
    return error_envelope(code, exc.description or exc.name, status=exc.code or 500)


def register_error_handlers(bp: Blueprint) -> None:
    """Install error handlers on the blueprint (and optionally the app)."""

    # flask-jwt-extended raises non-HTTP exceptions. Catch and convert
    # them to our standard envelope shape so the client always sees the
    # same envelope (success/data/error/meta).
    try:
        from flask_jwt_extended.exceptions import (
            NoAuthorizationError,
            InvalidHeaderError,
            JWTDecodeError,
            CSRFError,
        )

        @bp.errorhandler(NoAuthorizationError)
        def _on_no_auth(exc: NoAuthorizationError):
            return error_envelope(AUTH_REQUIRED, str(exc) or "Missing Authorization", status=401)

        @bp.errorhandler(InvalidHeaderError)
        def _on_bad_header(exc: InvalidHeaderError):
            return error_envelope(AUTH_REQUIRED, str(exc) or "Invalid Authorization header", status=401)

        @bp.errorhandler(JWTDecodeError)
        def _on_bad_token(exc: JWTDecodeError):
            return error_envelope(AUTH_REQUIRED, str(exc) or "Invalid token", status=401)

        @bp.errorhandler(CSRFError)
        def _on_csrf(exc: CSRFError):
            return error_envelope(AUTH_REQUIRED, str(exc) or "CSRF check failed", status=401)
    except ImportError:
        pass  # flask-jwt-extended version without these exceptions

    @bp.errorhandler(HTTPException)
    def _on_http_exc(exc: HTTPException):
        return _http_exception_to_envelope(exc)

    @bp.errorhandler(Exception)
    def _on_exception(exc: Exception):  # noqa: BLE001 — last-resort handler
        logger.exception("Unhandled error in knowledge blueprint: %s", exc)
        # Do not leak str(exc) — clients get a generic message; logs keep detail.
        return error_envelope(
            INTERNAL_ERROR,
            "An unexpected error occurred",
            status=500,
        )


def register_app_error_handlers(app: Flask) -> None:
    """Optionally install handlers at app level (for non-blueprint routes)."""
    @app.errorhandler(HTTPException)
    def _on_http_exc(exc: HTTPException):
        return _http_exception_to_envelope(exc)

    @app.errorhandler(Exception)
    def _on_exception(exc: Exception):  # noqa: BLE001
        logger.exception("Unhandled app-level error: %s", exc)
        return error_envelope(
            INTERNAL_ERROR, "An unexpected error occurred", status=500,
        )
