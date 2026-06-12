"""
Blueprint de Rotas para a Secretária / Equipe Administrativa (FASE 4)

Endpoints otimizados para o dia-a-dia da equipe:
  - GET  /api/secretaria/dashboard           → cards de resumo
  - GET  /api/secretaria/agenda?data=YYYY-MM-DD
  - POST /api/secretaria/consultas/<id>/checkin
  - GET  /api/secretaria/pacientes?q=...     → quick search read-only
  - GET  /api/secretaria/pacientes           → listagem paginada

Todas as rotas exigem:
  - JWT válido
  - Role em (admin, manager, secretary, auxiliar, superadmin) — staff
  - Vínculo com a associação (g.current_association populado pelo tenant middleware)

LGPD: Apenas dados agregados / read-only são retornados. Nada aqui modifica
prontuário clínico (prescrição, evolução, anamnese) — esses ficam restritos a physician.
"""
from __future__ import annotations

import logging
from typing import Optional

from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.secretaria_service import SecretariaService
from routes.auth_decorators import require_role, require_association_member

logger = logging.getLogger(__name__)

secretaria_bp = Blueprint("secretaria", __name__, url_prefix="/api/secretaria")


def _get_service() -> Optional[SecretariaService]:
    """Resolve a associação ativa para o usuário e retorna o service."""
    if not g.get("current_association"):
        return None
    return SecretariaService(
        associacao_id=g.current_association.id,
        profissional_id=int(get_jwt_identity()),
    )


# ═══════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

@secretaria_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@require_role("admin", "manager", "secretary", "auxiliar", "superadmin")
@require_association_member
def get_dashboard():
    """Cards do dashboard da secretária."""
    svc = _get_service()
    if not svc:
        return jsonify({"error": "Selecione uma clínica no menu superior."}), 400
    try:
        data = svc.get_dashboard_data()
        return jsonify({"success": True, **data}), 200
    except Exception as e:
        logger.exception("Erro em get_dashboard")
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════
# AGENDA
# ═══════════════════════════════════════════════════════════════════════

@secretaria_bp.route("/agenda", methods=["GET"])
@jwt_required()
@require_role("admin", "manager", "secretary", "auxiliar", "superadmin")
@require_association_member
def get_agenda():
    """Agenda completa de uma data (default: hoje)."""
    svc = _get_service()
    if not svc:
        return jsonify({"error": "Selecione uma clínica."}), 400
    try:
        data_str = request.args.get("data")
        agenda = svc.get_agenda(data_str)
        return jsonify({"success": True, "agenda": agenda}), 200
    except Exception as e:
        logger.exception("Erro em get_agenda")
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════
# CHECK-IN
# ═══════════════════════════════════════════════════════════════════════

@secretaria_bp.route("/consultas/<int:consulta_id>/checkin", methods=["POST"])
@jwt_required()
@require_role("admin", "manager", "secretary", "auxiliar", "superadmin")
@require_association_member
def marcar_checkin(consulta_id):
    """Marca uma consulta como 'confirmada' (comparecimento confirmado)."""
    svc = _get_service()
    if not svc:
        return jsonify({"error": "Selecione uma clínica."}), 400
    try:
        result = svc.marcar_checkin(consulta_id)
        status = 200 if result.get("success") else 400
        return jsonify(result), status
    except Exception as e:
        logger.exception("Erro em marcar_checkin")
        return jsonify({"success": False, "error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════════════
# PACIENTES (read-only)
# ═══════════════════════════════════════════════════════════════════════

@secretaria_bp.route("/pacientes", methods=["GET"])
@jwt_required()
@require_role("admin", "manager", "secretary", "auxiliar", "superadmin")
@require_association_member
def listar_pacientes():
    """Lista pacientes do tenant (read-only)."""
    svc = _get_service()
    if not svc:
        return jsonify({"error": "Selecione uma clínica."}), 400
    try:
        q = request.args.get("q", "").strip()
        if q:
            pacientes = svc.quick_search_pacientes(q)
            return jsonify({"success": True, "items": pacientes, "total": len(pacientes)}), 200

        try:
            limit = int(request.args.get("limit", 100))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            limit, offset = 100, 0

        data = svc.listar_pacientes(limit=limit, offset=offset)
        return jsonify({"success": True, **data}), 200
    except Exception as e:
        logger.exception("Erro em listar_pacientes")
        return jsonify({"success": False, "error": str(e)}), 500
