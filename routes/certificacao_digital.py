"""Certificação digital — configuração e assinatura via CESS (Bird ID).

Fluxo assíncrono: `assinar` cria a transação (tcn) + upload; o profissional
valida no app Bird ID; o frontend consulta `/assinatura/<tcn>` (polling) e
baixa o PDF assinado em `/assinatura/<tcn>/download`.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Profissional, Prescricao, SignatureTransaction
from services.digital_signature import (
    obter_config,
    salvar_config,
    iniciar_assinatura,
    consultar_transacao,
    baixar_assinado,
)

logger = logging.getLogger(__name__)

certificacao_bp = Blueprint("certificacao_digital", __name__)


def _current_user():
    user_id = get_jwt_identity()
    return Profissional.query.get(int(user_id)) if str(user_id).isdigit() else None


def _find_tx(tcn: str) -> SignatureTransaction:
    tx = SignatureTransaction.query.filter_by(tcn=tcn).first()
    if tx is None:
        raise ValueError("transação não encontrada")
    return tx


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
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            certificate_alias=data.get("certificate_alias"),
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
    """Inicia a assinatura: cria transação CESS + upload. Retorna o TCN."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    arquivo = request.files.get("file")
    if not arquivo or not arquivo.filename:
        return jsonify({"error": "enviar o arquivo no campo 'file'"}), 400
    data = request.form
    try:
        tx = iniciar_assinatura(
            arquivo.read(),
            provedor=data.get("provedor") or "birdid",
            profissional_id=user.id,
            nome_documento=arquivo.filename,
            motivo=data.get("motivo") or "",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("certificacao_assinar_falhou")
        return jsonify({"error": f"erro ao iniciar assinatura: {exc}"}), 500
    return jsonify({
        "tcn": tx.tcn,
        "status": tx.status,
        "message": "Documento enviado. Valide no aplicativo Bird ID para concluir a assinatura.",
    }), 200


@certificacao_bp.route("/certificacao-digital/assinatura/<tcn>", methods=["GET"])
@jwt_required()
def status_assinatura(tcn):
    """Consulta o status da transação (polling do frontend)."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    try:
        tx = _find_tx(tcn)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    try:
        dados = consultar_transacao(tx)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("certificacao_consulta_falhou")
        return jsonify({"error": f"erro ao consultar: {exc}"}), 500
    return jsonify(dados), 200


@certificacao_bp.route("/certificacao-digital/assinatura/<tcn>/download", methods=["GET"])
@jwt_required()
def download_assinado(tcn):
    """Baixa o PDF assinado."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    try:
        tx = _find_tx(tcn)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    try:
        if not tx.documento_assinado:
            pdf_bytes = baixar_assinado(tx)
        else:
            pdf_bytes = tx.documento_assinado
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("certificacao_download_falhou")
        return jsonify({"error": f"erro ao baixar: {exc}"}), 500
    from io import BytesIO

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=tx.documento_nome or "documento_assinado.pdf",
    )


@certificacao_bp.route("/prescricoes/<int:prescricao_id>/assinar", methods=["POST"])
@jwt_required()
def assinar_prescricao(prescricao_id):
    """Inicia a assinatura do PDF da prescrição."""
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
        tx = iniciar_assinatura(
            pdf_bytes,
            provedor=data.get("provedor") or "birdid",
            profissional_id=user.id,
            nome_documento=f"prescricao_{prescricao_id}.pdf",
            motivo=data.get("motivo") or "Prescrição médica",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("REDACTED")
        return jsonify({"error": f"erro ao iniciar assinatura: {exc}"}), 500
    return jsonify({"prescricao_id": prescricao_id, "tcn": tx.tcn, "status": tx.status}), 200
