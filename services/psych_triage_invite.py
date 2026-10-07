"""Convite (link assinado) para o paciente responder a triagem sozinho.

Usa `itsdangerous.URLSafeTimedSerializer` (dependência do Flask) — token
assinado e com expiração, sem necessidade de tabela nova. Não interfere no
JWT de autenticação (salt próprio).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SALT = "psych-triage-invite"
DEFAULT_EXPIRY_HOURS = 72


def _serializer() -> URLSafeTimedSerializer:
    secret = (
        os.getenv("PSYCH_TRIAGE_SECRET")
        or os.getenv("JWT_SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or "psych-triage-dev-secret"
    )
    return URLSafeTimedSerializer(secret, salt=SALT)


def create_invite_token(
    tenant_id: str,
    patient_id: Optional[str] = None,
    version: str = "latest",
) -> str:
    return _serializer().dumps(
        {"tenant_id": str(tenant_id), "patient_id": str(patient_id) if patient_id else None, "version": version}
    )


def verify_invite_token(token: str, max_age_hours: int = DEFAULT_EXPIRY_HOURS) -> Optional[Dict[str, Any]]:
    try:
        data = _serializer().loads(token, max_age=int(max_age_hours * 3600))
    except (BadSignature, SignatureExpired):
        return None
    if not isinstance(data, dict) or not data.get("tenant_id"):
        return None
    return data


def build_invite_link(token: str) -> str:
    explicit = os.getenv("PSYCH_TRIAGE_URL")
    if explicit:
        sep = "&" if "?" in explicit else "?"
        return f"{explicit}{sep}token={token}"
    base = (
        os.getenv("ARAOS_SITE_URL")
        or os.getenv("FRONTEND_BASE_URL")
        or os.getenv("BASE_URL")
        or ""
    ).rstrip("/")
    path = f"/static/psicotriagem.html?token={token}"
    return f"{base}{path}" if base else path
