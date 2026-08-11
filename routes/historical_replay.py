"""Replay histórico do SIAP → AraOS (F2 retrofit) — endpoint.

`POST /api/replay/historical` — dispara o replay de anamneses/evoluções
históricas para o AraOS (bootstrap do genome). Restrito a admin.

Retorna o resultado: total, emitted, failed, errors (limitados).
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

replay_bp = Blueprint("historical_replay", __name__)


@replay_bp.route("/api/replay/historical", methods=["POST"])
def run_historical_replay():
    """Executa o replay das anamneses/evoluções históricas para o AraOS."""
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

    # Restrito a admin (sem permitir falha silenciosa de auth)
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
    except Exception:
        return jsonify({"error": "Não autorizado"}), 401

    from models import Profissional, db

    profissional = Profissional.query.get(int(user_id)) if user_id else None
    if not profissional or profissional.role not in ("admin", "superadmin"):
        return jsonify({"error": "Permissão negada"}), 403

    # Parâmetros opcionais
    body = request.get_json(silent=True) or {}
    limit = body.get("limit")

    from services.historical_replay import HistoricalReplayService

    replay = HistoricalReplayService(db.session)
    result = replay.run(limit=limit)

    logger.info(
        "historical_replay: total=%d emitted=%d failed=%d",
        result.total, result.emitted, result.failed,
    )
    return jsonify(result.to_dict()), 200
