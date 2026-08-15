"""Pré-atendimento público por tenant.

Rotas públicas (sem JWT) — acessadas pelo paciente pela URL
`/pre-atendimento/<slug>` (ex.: /pre-atendimento/dr.anderson).

    GET  /api/public/pre-atendimento/<slug>  — identidade do instituto + questionário
    POST /api/public/pre-atendimento/<slug>  — envia o pré-atendimento
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from services.pre_atendimento import (
    obter_questionario,
    processar_pre_atendimento,
    resolver_tenant_por_slug,
)

logger = logging.getLogger(__name__)

pre_atendimento_bp = Blueprint("pre_atendimento", __name__)


@pre_atendimento_bp.route("/pre-atendimento/<slug>", methods=["GET"])
def obter_pre_atendimento(slug: str):
    """Retorna identidade do instituto + questionário do tenant (público)."""
    tenant = resolver_tenant_por_slug(slug)
    if not tenant:
        return jsonify({"error": "instituto não encontrado"}), 404

    prof = tenant["profissional"]
    assoc = tenant["associacao"]
    questionario = obter_questionario(prof.id)

    return jsonify({
        "slug": slug,
        "instituto": assoc.nome if assoc else prof.nome,
        "profissional": prof.nome,
        "boas_vindas": (
            f"Bem-vindo(a) ao {assoc.nome if assoc else prof.nome}! "
            "Onde a saúde e o bem-estar se encontram para moldar a sua melhor versão."
        ),
        "questionario": questionario,
    }), 200


@pre_atendimento_bp.route("/pre-atendimento/<slug>", methods=["POST"])
def enviar_pre_atendimento(slug: str):
    """Recebe as respostas do pré-atendimento e cria/vincula o paciente."""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "payload inválido"}), 400

    try:
        resultado = processar_pre_atendimento(slug, data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("pre_atendimento_falhou")
        return jsonify({"error": "erro ao processar pré-atendimento"}), 500

    return jsonify({"message": "Pré-atendimento recebido com sucesso!", "resultado": resultado}), 201
