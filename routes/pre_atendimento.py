"""Pré-atendimento público por tenant + conferência.

Rotas públicas (sem JWT) — acessadas pelo paciente pela URL
`/pre-atendimento/<slug>`:

    GET  /api/public/pre-atendimento/<slug>  — identidade do instituto + questionário
    POST /api/public/pre-atendimento/<slug>  — registra pré-atendimento (pendente pagamento)

Rotas de conferência (com JWT — profissional/tenant):

    GET  /api/pre-atendimento/pendentes           — fila de conferência
    POST /api/pre-atendimento/<id>/conferir       — libera ou rejeita
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import Profissional, PreConsulta
from services.pre_atendimento import (
    conferir_pre_atendimento,
    listar_pre_atendimentos,
    obter_questionario,
    registrar_pre_atendimento,
    resolver_tenant_por_slug,
)

logger = logging.getLogger(__name__)

pre_atendimento_bp = Blueprint("pre_atendimento", __name__)
pre_atendimento_conferencia_bp = Blueprint("pre_atendimento_conferencia", __name__)


@pre_atendimento_bp.route("/pre-atendimento/<slug>", methods=["GET"])
def obter_pre_atendimento(slug: str):
    """Retorna identidade do instituto + questionário do tenant (público)."""
    tenant = resolver_tenant_por_slug(slug)
    if not tenant:
        return jsonify({"error": "instituto não encontrado"}), 404

    prof = tenant["profissional"]
    assoc = tenant["associacao"]
    questionario = obter_questionario(prof.id)

    nome_assoc = assoc.nome if assoc else prof.nome
    nome_instituto = "Instituto Vittalis" if nome_assoc.strip().lower() == "vittalis" else nome_assoc

    return jsonify({
        "slug": slug,
        "instituto": nome_instituto,
        "profissional": prof.nome,
        "boas_vindas": (
            f"Bem-vindo(a) ao {nome_instituto}! "
            "Onde a saúde e o bem-estar se encontram para moldar a sua melhor versão."
        ),
        "questionario": questionario,
    }), 200


@pre_atendimento_bp.route("/pre-atendimento/<slug>", methods=["POST"])
def enviar_pre_atendimento(slug: str):
    """Recebe as respostas do pré-atendimento (ficam pendentes de pagamento)."""
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "payload inválido"}), 400

    try:
        resultado = registrar_pre_atendimento(slug, data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("pre_atendimento_falhou")
        return jsonify({"error": "erro ao processar pré-atendimento"}), 500

    return jsonify({"message": resultado.pop("mensagem"), "resultado": resultado}), 201


# ─────────────────────────────────────────────────────────────
# Chat com agente (público — entrevista o lead)
# ─────────────────────────────────────────────────────────────

@pre_atendimento_bp.route("/pre-atendimento/<slug>/chat/iniciar", methods=["POST"])
def iniciar_chat(slug: str):
    """Inicia uma sessão de chat do pré-atendimento."""
    from services.pre_atendimento_chat import nova_sessao
    session_id = nova_sessao(slug)
    return jsonify({"session_id": session_id}), 201


@pre_atendimento_bp.route("/pre-atendimento/<slug>/chat", methods=["POST"])
def chat_pre_atendimento(slug: str):
    """Envia mensagem (texto e/ou imagem) para o agente do pré-atendimento."""
    from services.pre_atendimento_chat import processar_mensagem

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or ""
    mensagem = data.get("mensagem") or ""
    imagem_b64 = data.get("imagem_b64")
    mime_type = data.get("mime_type")

    if not session_id:
        return jsonify({"error": "session_id é obrigatório"}), 400
    if not mensagem and not imagem_b64:
        return jsonify({"error": "mensagem ou imagem é obrigatório"}), 400

    try:
        resultado = processar_mensagem(session_id, mensagem, imagem_b64, mime_type)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("chat_pre_atendimento_falhou")
        return jsonify({"error": "erro ao processar mensagem"}), 500

    return jsonify(resultado), 200


@pre_atendimento_bp.route("/pre-atendimento/<slug>/chat/finalizar", methods=["POST"])
def finalizar_chat(slug: str):
    """Finaliza o chat e registra o pré-atendimento (pendente pagamento)."""
    from services.pre_atendimento_chat import finalizar_pre_atendimento_chat

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id") or ""
    if not session_id:
        return jsonify({"error": "session_id é obrigatório"}), 400

    try:
        resultado = finalizar_pre_atendimento_chat(session_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("finalizar_chat_falhou")
        return jsonify({"error": "erro ao finalizar pré-atendimento"}), 500

    return jsonify({"message": resultado.pop("mensagem"), "resultado": resultado}), 201


# ─────────────────────────────────────────────────────────────
# Conferência (autenticado — fila do tenant)
# ─────────────────────────────────────────────────────────────

def _tenant_ids_do_usuario(user_id: int):
    """Associações ativas do profissional logado.

    Usa skip_tenant=True: a query de UsuarioAssociacao também é filtrada pelo
    tenant (associacao_id=current), o que esconderia vínculos em outras
    associações do mesmo profissional (P0-09 — mesmo padrão de pacientes).
    """
    from models_extra import UsuarioAssociacao
    links = UsuarioAssociacao.query.execution_options(skip_tenant=True).filter_by(
        profissional_id=user_id, status="active"
    ).all()
    return [l.associacao_id for l in links if l.associacao_id]


@pre_atendimento_conferencia_bp.route("/pendentes", methods=["GET"])
@jwt_required()
def listar_pendentes():
    """Fila de conferência dos pré-atendimentos do tenant."""
    user_id = int(get_jwt_identity())
    user = Profissional.query.get(user_id)
    tenant_ids = _tenant_ids_do_usuario(user_id)
    status = request.args.get("status") or None

    # Admin/superadmin veem todos os tenants; demais, só os seus.
    if user and user.role in ("admin", "superadmin") and request.args.get("todos") == "1":
        tenant_ids = None

    itens = listar_pre_atendimentos(tenant_ids=tenant_ids, status=status)
    return jsonify({"total": len(itens), "pre_atendimentos": [i.to_dict() for i in itens]}), 200


@pre_atendimento_conferencia_bp.route("/<int:pre_id>/conferir", methods=["POST"])
@jwt_required()
def conferir(pre_id: int):
    """Libera (cria paciente) ou rejeita um pré-atendimento."""
    user_id = int(get_jwt_identity())
    user = Profissional.query.get(user_id)
    data = request.get_json(silent=True) or {}
    acao = data.get("acao", "liberar")

    try:
        # Temporariamente adota a associação do pré-atendimento como tenant do
        # request (se o usuário pertence a ela), para que o flush P0-08 aceite
        # criar o paciente na associação correta.
        from association.models import Associacao
        from models_extra import UsuarioAssociacao
        pre = PreConsulta.query.execution_options(skip_tenant=True).get(pre_id)
        if pre and pre.associacao_id:
            # skip_tenant: a query de UsuarioAssociacao também é filtrada pelo
            # tenant (associacao_id=current), o que esconderia o vínculo da
            # associação de destino (P0-09 — mesmo padrão de pacientes).
            link = UsuarioAssociacao.query.execution_options(skip_tenant=True).filter_by(
                profissional_id=user_id, associacao_id=pre.associacao_id, status="active"
            ).first()
            if link:
                assoc = Associacao.query.get(pre.associacao_id)
                g.current_association = assoc or link.associacao

        resultado = conferir_pre_atendimento(
            pre_id,
            acao=acao,
            pagamento_confirmado=bool(data.get("pagamento_confirmado")),
            dispensar_pagamento=bool(data.get("dispensar_pagamento")),
            conferido_por=f"{user.nome} (id {user.id})" if user else str(user_id),
            motivo=data.get("motivo"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("conferir_pre_atendimento_falhou")
        return jsonify({"error": "erro ao conferir"}), 500

    if resultado.get("erro"):
        return jsonify({"message": resultado["erro"], "resultado": resultado}), 200
    return jsonify({"message": "Pré-atendimento processado.", "resultado": resultado}), 200
