"""
Sprint S1 — fixtures compartilhadas.

Constrói uma app Flask mínima com:
  - SQLite in-memory
  - JWTTokenProvider (AraOS) inicializado
  - rotas de teste para /refresh, /logout, /me (via Blueprint)
"""

import os
import sys
import secrets as _secrets

import pytest

# Garante que a raiz do projeto está no sys.path (pytest pode rodar a partir de /tests)
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture(scope="session")
def jwt_secret():
    """Secret >= 32 chars (mesmo formato de produção)."""
    return _secrets.token_hex(32)


@pytest.fixture()
def flask_app(jwt_secret):
    """App Flask mínima para testar o AraOS auth bridge."""
    from flask import Flask

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 2592000

    # Inicializar provider AraOS
    from services.araos_auth import (
        init_araos_auth,
        araos_jwt_required,
        get_araos_current_user,
        refresh_araos_token_pair,
        revoke_araos_token,
    )
    init_araos_auth(app)

    # Rota protegida de teste
    @app.route("/api/me", methods=["GET"])
    @araos_jwt_required
    def me():
        from flask import jsonify
        return jsonify({"user": get_araos_current_user()})

    # Endpoints Sprint S1 (refresh, logout) — espelham routes/auth.py
    @app.route("/api/auth/refresh", methods=["POST"])
    def refresh_token():
        from flask import jsonify, request
        data = request.get_json() or {}
        refresh = data.get("refresh_token", "").strip()
        if not refresh:
            return jsonify({"error": "refresh_token ausente"}), 400
        try:
            new_pair = refresh_araos_token_pair(refresh)
        except Exception:
            return jsonify({"error": "refresh_token inválido ou expirado"}), 401
        return jsonify({
            "access_token": new_pair.access_token,
            "refresh_token": new_pair.refresh_token,
            "expires_in": new_pair.expires_in,
            "token_type": new_pair.token_type,
        }), 200

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        from flask import jsonify, request
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Authorization header ausente"}), 400
        token = auth.split(" ", 1)[1].strip()
        revoked = revoke_araos_token(token)
        return jsonify({"message": "Logout efetuado", "revoked": revoked}), 200

    return app


@pytest.fixture()
def client(flask_app):
    return flask_app.test_client()
