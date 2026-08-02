"""
Sprint S1 — AraOS JWT Auth Bridge.

Ponte entre a aplicação Flask e o provider de identidade AraOS
(araos.platform.identity.tokens.JWTTokenProvider).

Esta camada:
    - Inicializa o JWTTokenProvider como singleton (uma instância por app)
    - Expõe um decorator @araos_jwt_required() compatível com o padrão
      flask_jwt_extended (substituível)
    - Permite que rotas auth.py usem exclusivamente o provider AraOS
      (access + refresh + revoke) sem depender do flask_jwt_extended.

Uso:
    from services.araos_auth import init_araos_auth, araos_jwt_required

    init_araos_auth(app)
    # ...

    @app.route('/api/auth/login')
    def login():
        ...
        pair = get_araos_token_provider().issue(
            actor_id=user.id, tenant_id=org_id, roles=[], permissions=[],
        )
        return jsonify({
            "access_token": pair.access_token,
            "refresh_token": pair.refresh_token,
            "expires_in": pair.expires_in,
        })

    @araos_jwt_required
    def protected_route():
        user = get_araos_current_user()
        ...
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from flask import current_app, g, jsonify, request

from araos.platform.identity.tokens import (
    JWTTokenProvider,
    TokenClaims,
    PlatformTokenPair,
)
from araos.platform.shared.errors import TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════

_ARAOS_PROVIDER_KEY = "ARAOS_JWT_PROVIDER"


def init_araos_auth(app) -> JWTTokenProvider:
    """
    Inicializa o provider AraOS e o anexa à app.

    Lê JWT_SECRET_KEY de app.config (que vem de config.py).
    Falha de forma explícita se a chave estiver ausente/curta.

    Returns:
        JWTTokenProvider: instância singleton pronta para uso.
    """
    secret = app.config.get("JWT_SECRET_KEY")
    if not secret or len(str(secret)) < 32:
        raise RuntimeError(
            "[araos_auth] JWT_SECRET_KEY ausente ou <32 chars — "
            "config.py já valida isto; verifique .env / docker-compose."
        )

    access_expiry = int(app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    refresh_expiry = int(app.config.get("JWT_REFRESH_TOKEN_EXPIRES", 2592000))

    provider = JWTTokenProvider(
        secret_key=str(secret),
        access_expiry=access_expiry,
        refresh_expiry=refresh_expiry,
    )
    app.extensions[_ARAOS_PROVIDER_KEY] = provider
    app.config.setdefault("JWT_REFRESH_TOKEN_EXPIRES", refresh_expiry)
    logger.info(
        "[araos_auth] JWTTokenProvider inicializado "
        "(access=%ds, refresh=%ds)",
        access_expiry, refresh_expiry,
    )
    return provider


def get_araos_token_provider() -> JWTTokenProvider:
    """
    Recupera o provider inicializado. Falha 503 se ainda não foi inicializado.
    """
    provider = current_app.extensions.get(_ARAOS_PROVIDER_KEY)
    if provider is None:
        raise RuntimeError(
            "[araos_auth] JWTTokenProvider não inicializado. "
            "Chame init_araos_auth(app) em create_app()."
        )
    return provider


# ═══════════════════════════════════════════════════════════════════════
# DECORATOR @araos_jwt_required (substitui @jwt_required do flask_jwt_extended)
# ═══════════════════════════════════════════════════════════════════════


def araos_jwt_required(fn: Callable) -> Callable:
    """
    Decorator equivalente a flask_jwt_extended.jwt_required(), porém
    valida tokens emitidos pelo AraOS JWTTokenProvider.

    Comportamento:
        - Lê header Authorization: Bearer <token>
        - Valida tipo "access" via provider.validate()
        - Em caso de sucesso: armazena TokenClaims em g.araos_claims
        - Em caso de falha: retorna 401 com mensagem específica

    Roteiros ainda em flask_jwt_extended NÃO são afetados (decorators
    separados — eles coexistem; S2/S3 fará a migração gradual).
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Authorization header ausente ou malformado"}), 401

        token = auth.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Token vazio"}), 401

        try:
            provider = get_araos_token_provider()
            claims: TokenClaims = provider.validate(token, expected_type="access")
        except TokenExpiredError:
            return jsonify({"error": "Token expirado"}), 401
        except TokenInvalidError as exc:
            return jsonify({"error": f"Token inválido: {exc}"}), 401
        except RuntimeError as exc:
            # Provider não inicializado
            current_app.logger.error("[araos_auth] %s", exc)
            return jsonify({"error": "Auth não configurada"}), 503

        g.araos_claims = claims
        return fn(*args, **kwargs)

    return wrapper


def get_araos_current_user() -> Optional[Dict[str, Any]]:
    """
    Retorna o dicionário de usuário extraído dos claims AraOS.

    Compatibilidade com o shape antigo:
        {"id": <actor_id>, "tenant_id": <tenant_id>, "actor_type": <actor_type>}
    """
    claims: Optional[TokenClaims] = getattr(g, "araos_claims", None)
    if claims is None:
        return None
    return {
        "id": claims.sub,
        "tenant_id": claims.tenant_id,
        "actor_type": claims.actor_type,
        "roles": claims.roles,
        "permissions": claims.permissions,
    }


# ═══════════════════════════════════════════════════════════════════════
# HELPERS DE EMISSÃO (wrapper amigável para uso em auth.py)
# ═══════════════════════════════════════════════════════════════════════


def issue_araos_token_pair(
    actor_id: str,
    tenant_id: str,
    roles: Optional[List[str]] = None,
    permissions: Optional[List[str]] = None,
    clinic_ids: Optional[List[str]] = None,
    actor_type: str = "user",
    email: Optional[str] = None,
    full_name: Optional[str] = None,
) -> PlatformTokenPair:
    """
    Wrapper conveniente em torno de JWTTokenProvider.issue().
    """
    provider = get_araos_token_provider()
    return provider.issue(
        actor_id=str(actor_id),
        tenant_id=str(tenant_id),
        roles=roles or [],
        permissions=permissions or [],
        clinic_ids=clinic_ids or [],
        actor_type=actor_type,
        email=email,
        full_name=full_name,
    )


def refresh_araos_token_pair(refresh_token: str) -> PlatformTokenPair:
    """
    Wrapper conveniente em torno de JWTTokenProvider.refresh().
    """
    provider = get_araos_token_provider()
    return provider.refresh(refresh_token)


def revoke_araos_token(token: str) -> bool:
    """
    Revoga um token pelo JTI. Retorna True se revogação foi possível.

    Tolerante a tokens inválidos (idempotente).
    """
    try:
        provider = get_araos_token_provider()
        claims = provider.validate(token)
        provider.revoke(claims.jti)
        return True
    except (TokenExpiredError, TokenInvalidError):
        return False
    except RuntimeError:
        return False
