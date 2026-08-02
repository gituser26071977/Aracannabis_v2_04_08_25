"""
Sprint S1 — testes do AraOS auth bridge.

Cobre:
  - Emissão de par access+refresh via provider
  - Validação do access token (decorator @araos_jwt_required)
  - Renovação via /refresh
  - Revogação via /logout
  - Rejeição de tokens expirados/inválidos/revogados
"""

import time
import pytest


# ═══════════════════════════════════════════════════════════════════════
# 1. Emissão (issue)
# ═══════════════════════════════════════════════════════════════════════


def REDACTED(flask_app):
    """Login emite par access+refresh (item 1.4 do roadmap)."""
    from services.araos_auth import issue_araos_token_pair

    with flask_app.app_context():
        pair = issue_araos_token_pair(
            actor_id="42",
            tenant_id="org_1",
            roles=["admin"],
            permissions=["*"],
        )
    assert pair.access_token
    assert pair.refresh_token
    assert pair.access_token != pair.refresh_token
    assert pair.token_type == "Bearer"
    assert pair.expires_in == 3600


def REDACTED(flask_app):
    """Tokens AraOS carregam claims padronizados."""
    import jwt as pyjwt

    with flask_app.app_context():
        from services.araos_auth import (
            issue_araos_token_pair,
            get_araos_token_provider,
        )
        provider = get_araos_token_provider()
        pair = issue_araos_token_pair(
            actor_id="42",
            tenant_id="org_1",
            roles=["admin"],
        )

        access_claims = pyjwt.decode(
            pair.access_token,
            flask_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        assert access_claims["sub"] == "42"
        assert access_claims["tenant_id"] == "org_1"
        assert access_claims["type"] == "access"
        assert access_claims["version"] == "1.0"

        refresh_claims = pyjwt.decode(
            pair.refresh_token,
            flask_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        assert refresh_claims["sub"] == "42"
        assert refresh_claims["type"] == "refresh"


# ═══════════════════════════════════════════════════════════════════════
# 2. Validação (decorator)
# ═══════════════════════════════════════════════════════════════════════


def REDACTED(client, flask_app):
    """Token válido em /api/me retorna 200 com claims."""
    with flask_app.app_context():
        from services.araos_auth import issue_araos_token_pair
        pair = issue_araos_token_pair(actor_id="42", tenant_id="org_1")

    resp = client.get("/api/me", headers={
        "Authorization": f"Bearer {pair.access_token}",
    })
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["user"]["id"] == "42"
    assert body["user"]["tenant_id"] == "org_1"


def REDACTED(client):
    """Sem header Authorization, decorator retorna 401."""
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert "Authorization" in resp.get_json()["error"]


def REDACTED(client):
    """Header sem 'Bearer ' prefix → 401."""
    resp = client.get("/api/me", headers={"Authorization": "garbage"})
    assert resp.status_code == 401


def test_invalid_token_returns_401(client):
    """Token assinado com outro secret → 401."""
    resp = client.get("/api/me", headers={
        "Authorization": "Bearer JWT_REDACTED",
    })
    assert resp.status_code == 401


def REDACTED(client, flask_app):
    """Refresh token NÃO pode ser usado como access token (item 1.4 do roadmap)."""
    with flask_app.app_context():
        from services.araos_auth import issue_araos_token_pair
        pair = issue_araos_token_pair(actor_id="42", tenant_id="org_1")

    resp = client.get("/api/me", headers={
        "Authorization": f"Bearer {pair.refresh_token}",
    })
    assert resp.status_code == 401
    assert "inválido" in resp.get_json()["error"] or "expirado" in resp.get_json()["error"]


# ═══════════════════════════════════════════════════════════════════════
# 3. Refresh (item 1.4)
# ═══════════════════════════════════════════════════════════════════════


def test_refresh_returns_new_pair(client, flask_app):
    """/refresh emite novo par a partir de refresh válido."""
    with flask_app.app_context():
        from services.araos_auth import issue_araos_token_pair
        original = issue_araos_token_pair(actor_id="42", tenant_id="org_1")

    resp = client.post("/api/auth/refresh", json={
        "refresh_token": original.refresh_token,
    })
    assert resp.status_code == 200, resp.get_json()
    body = resp.get_json()
    assert body["access_token"]
    assert body["refresh_token"]
    # Refresh one-time use: novo refresh deve diferir do anterior
    assert body["refresh_token"] != original.refresh_token


def test_refresh_rejects_missing_token(client):
    """/refresh sem refresh_token → 400."""
    resp = client.post("/api/auth/refresh", json={})
    assert resp.status_code == 400


def test_refresh_rejects_invalid_token(client):
    """/refresh com refresh_token inválido → 401."""
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": "not.a.valid.jwt",
    })
    assert resp.status_code == 401


def REDACTED(client, flask_app):
    """Refresh token usado NÃO pode ser reusado (one-time use)."""
    with flask_app.app_context():
        from services.araos_auth import (
            issue_araos_token_pair,
            refresh_araos_token_pair,
        )
        original = issue_araos_token_pair(actor_id="42", tenant_id="org_1")
        # 1ª renovação: sucesso
        new_pair = refresh_araos_token_pair(original.refresh_token)
        # Tentar reusar refresh antigo: deve falhar
        with pytest.raises(Exception):
            refresh_araos_token_pair(original.refresh_token)


# ═══════════════════════════════════════════════════════════════════════
# 4. Logout (revogação)
# ═══════════════════════════════════════════════════════════════════════


def test_logout_revokes_token(client, flask_app):
    """/logout revoga token; uso subsequente → 401."""
    with flask_app.app_context():
        from services.araos_auth import issue_araos_token_pair
        pair = issue_araos_token_pair(actor_id="42", tenant_id="org_1")

    # Logout
    resp = client.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {pair.access_token}",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["revoked"] is True

    # Tentar usar access token revogado
    resp = client.get("/api/me", headers={
        "Authorization": f"Bearer {pair.access_token}",
    })
    assert resp.status_code == 401


def REDACTED(client):
    """/logout sem header → 400 (diferente de /me)."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 400


def REDACTED(client):
    """/logout com token inválido retorna 200 (idempotente)."""
    resp = client.post("/api/auth/logout", headers={
        "Authorization": "Bearer bogus",
    })
    assert resp.status_code == 200
    assert resp.get_json()["revoked"] is False


# ═══════════════════════════════════════════════════════════════════════
# 5. Tenant isolation (regressão crítica)
# ═══════════════════════════════════════════════════════════════════════


def test_tokens_carry_tenant_id(flask_app):
    """Tokens carregam tenant_id (item 1.2 — base para isolamento)."""
    import jwt as pyjwt

    with flask_app.app_context():
        from services.araos_auth import issue_araos_token_pair
        pair = issue_araos_token_pair(
            actor_id="42",
            tenant_id="org_xyz",
            roles=["doctor"],
        )

    claims = pyjwt.decode(
        pair.access_token,
        flask_app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
    )
    assert claims["tenant_id"] == "org_xyz"
    assert claims["org_id"] == "org_xyz"  # alias mantido
    assert "doctor" in claims["roles"]
