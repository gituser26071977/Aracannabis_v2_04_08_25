"""
Rotas de uso/quotas (Squad B — Segurança & Acesso)

Endpoint GET /api/usage
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.quota_service import QuotaService
from services.feature_flag_service import FeatureFlagService

usage_bp = Blueprint("usage", __name__)


@usage_bp.route("/usage", methods=["GET"])
@jwt_required()
def get_usage():
    """Retorna a quota usada/total do profissional autenticado."""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    if not FeatureFlagService.is_enabled("plan_enforcement"):
        return (
            jsonify(
                {
                    "error": "Funcionalidade desativada",
                    "message": "O endpoint de uso está temporariamente indisponível.",
                }
            ),
            503,
        )

    data = QuotaService.get_full_usage(profissional_id)
    if isinstance(data, tuple):
        return jsonify(data[0]), data[1]
    return jsonify(data), 200
