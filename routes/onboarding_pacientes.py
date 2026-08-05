"""Onboarding de pacientes — cadastro administrativo com IA + fila de pendências.

Fluxo:
    POST /api/onboarding/paciente/sugerir  — extrai dados de texto livre (IA/heurística)
    POST /api/onboarding/paciente          — cadastra ou abre pendência (duplicado/incompleto)
    GET  /api/onboarding/pendentes         — fila para o administrativo
    POST /api/onboarding/pendentes/<id>/confirmar — cria ou usa existente
    POST /api/onboarding/pendentes/<id>/descartar — descarta
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Profissional
from services.onboarding_pacientes import (
    confirmar_pendencia,
    descartar_pendencia,
    listar_pendentes,
    registrar_paciente,
    sugerir_dados,
)

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint("onboarding_pacientes", __name__)


def _current_user():
    user_id = get_jwt_identity()
    return Profissional.query.get(int(user_id)) if str(user_id).isdigit() else None


@onboarding_bp.route("/paciente/sugerir", methods=["POST"])
@jwt_required()
def sugerir_paciente():
    """Extrai dados do paciente a partir de texto livre (IA com fallback heurístico)."""
    data = request.get_json(silent=True) or {}
    texto = (data.get("texto") or "").strip()
    if not texto:
        return jsonify({"error": "informe o texto para sugestão"}), 400
    try:
        sugestao = sugerir_dados(texto)
    except Exception:  # noqa: BLE001
        logger.exception("sugestao_falhou")
        return jsonify({"error": "falha ao sugerir dados"}), 500
    return jsonify({"sugestao": sugestao}), 200


@onboarding_bp.route("/paciente", methods=["POST"])
@jwt_required()
def cadastrar_paciente():
    """Cadastra paciente. Se duplicado ou incompleto, abre pendência."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    try:
        resultado = registrar_paciente(data, origem="admin", criado_por=str(user.id))
    except Exception:  # noqa: BLE001
        logger.exception("onboarding_paciente_falhou")
        return jsonify({"error": "erro ao registrar paciente"}), 500

    if resultado["status"] == "criado":
        return jsonify({"message": "Paciente cadastrado", "resultado": resultado}), 201
    return jsonify({"message": "Pendência criada para revisão", "resultado": resultado}), 200


@onboarding_bp.route("/pendentes", methods=["GET"])
@jwt_required()
def listar_pendencias():
    """Fila de pendências do onboarding de pacientes."""
    try:
        itens = listar_pendentes()
    except Exception:  # noqa: BLE001
        return jsonify({"error": "erro ao listar pendências"}), 500
    return jsonify({"total": len(itens), "pendentes": [i.to_dict() for i in itens]}), 200


@onboarding_bp.route("/pendentes/<int:onboarding_id>/confirmar", methods=["POST"])
@jwt_required()
def confirmar(onboarding_id):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    acao = data.get("acao", "criar")
    try:
        resultado = confirmar_pendencia(
            onboarding_id,
            acao=acao,
            dados=data.get("dados"),
            criado_por=str(user.id),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("confirmar_pendencia_falhou")
        return jsonify({"error": "erro ao confirmar pendência"}), 500
    return jsonify({"message": "Pendência resolvida", "resultado": resultado}), 200


@onboarding_bp.route("/pendentes/<int:onboarding_id>/descartar", methods=["POST"])
@jwt_required()
def descartar(onboarding_id):
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    try:
        descartar_pendencia(onboarding_id, criado_por=str(user.id))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("descartar_pendencia_falhou")
        return jsonify({"error": "erro ao descartar pendência"}), 500
    return jsonify({"message": "Pendência descartada"}), 200
