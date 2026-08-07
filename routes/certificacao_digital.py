"""Certificação digital — configuração e assinatura de documentos (Bird ID e outros).

Cada profissional configura suas credenciais (provedor + client_id/secret) e
pode assinar PDFs (prescrições, laudos, relatórios). O documento é enviado à
plataforma de assinatura, que retorna a sessão/URL para o profissional assinar.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Profissional, Prescricao
from services.digital_signature import (
    obter_config,
    salvar_config,
    assinar_pdf as service_assinar_pdf,
)

logger = logging.getLogger(__name__)

certificacao_bp = Blueprint("certificacao_digital", __name__)


def _current_user():
    user_id = get_jwt_identity()
    return Profissional.query.get(int(user_id)) if str(user_id).isdigit() else None


@certificacao_bp.route("/certificacao-digital/config", methods=["GET"])
@jwt_required()
def get_config():
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    cfg = obter_config(user.id)
    return jsonify({"config": cfg.to_dict() if cfg else None}), 200


@certificacao_bp.route("/certificacao-digital/config", methods=["POST"])
@jwt_required()
def post_config():
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    try:
        cfg = salvar_config(
            user.id,
            provedor=data.get("provedor", "birdid"),
            client_id=(data.get("client_id") or "").strip(),
            client_secret=(data.get("client_secret") or "").strip(),
            base_url=(data.get("base_url") or "").strip() or None,
            criado_por=str(user.id),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("certificacao_config_falhou")
        return jsonify({"error": "erro ao salvar configuração"}), 500
    return jsonify({"message": "Configuração salva", "config": cfg.to_dict()}), 200


@certificacao_bp.route("/certificacao-digital/assinar", methods=["POST"])
@jwt_required()
def assinar_documento():
    """Assina um PDF enviado (multipart) com a configuração do profissional."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    arquivo = request.files.get("file")
    if not arquivo or not arquivo.filename:
        return jsonify({"error": "enviar o arquivo no campo 'file'"}), 400
    data = request.form
    try:
        resultado = service_assinar_pdf(
            arquivo.read(),
            provedor=data.get("provedor") or "birdid",
            profissional_id=user.id,
            nome_assinante=data.get("nome_assinante") or user.nome,
            cpf_assinante=data.get("cpf_assinante") or "",
            motivo=data.get("motivo") or "",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("certificacao_assinar_falhou")
        return jsonify({"error": f"erro ao assinar: {exc}"}), 500
    return jsonify(resultado), 200


@certificacao_bp.route("/prescricoes/<int:prescricao_id>/assinar", methods=["POST"])
@jwt_required()
def assinar_prescricao(prescricao_id):
    """Gera/assina o PDF da prescrição com a certificação digital do profissional."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    prescricao = Prescricao.query.get(prescricao_id)
    if not prescricao or not prescricao.arquivo_path:
        return jsonify({"error": "prescrição não encontrada ou sem PDF"}), 404

    import os

    if not os.path.exists(prescricao.arquivo_path):
        return jsonify({"error": "arquivo da prescrição não encontrado"}), 404
    with open(prescricao.arquivo_path, "rb") as f:
        pdf_bytes = f.read()

    data = request.get_json(silent=True) or {}
    try:
        resultado = service_assinar_pdf(
            pdf_bytes,
            provedor=data.get("provedor") or "birdid",
            profissional_id=user.id,
            nome_assinante=data.get("nome_assinante") or user.nome,
            cpf_assinante=data.get("cpf_assinante") or "",
            motivo=data.get("motivo") or "Prescrição médica",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("REDACTED")
        return jsonify({"error": f"erro ao assinar: {exc}"}), 500
    return jsonify({"prescricao_id": prescricao_id, **resultado}), 200
