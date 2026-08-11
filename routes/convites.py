"""Rotas de Convites de Associação — onboarding de médicos em clínicas/grupos.

Fluxo:
    POST   /api/convites            → admin da associação gera convite (email+código+token)
    GET    /api/convites            → lista convites da associação (admin)
    DELETE /api/convites/<id>       → revoga convite (admin)
    POST   /api/convites/aceitar    → médico logado aceita via CÓDIGO
    POST   /api/convites/token      → aceita via TOKEN (link) — com validação de email

Aceitar cria/ativa o vínculo UsuarioAssociacao (membro da clínica).
Gerar convite exige role admin na associação (g.user_role).
"""

from __future__ import annotations

import logging
import secrets
import string
import uuid
from datetime import timedelta, datetime

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models_extra import ConviteAssociacao, UsuarioAssociacao

logger = logging.getLogger(__name__)

convites_bp = Blueprint("convites", __name__)

CONVITE_EXPIRA_DIAS = 7


def _associacao_atual():
    """Resolve a associação atual (tenant) via middleware (P0-12)."""
    return getattr(g, "current_association", None)


def _user_id() -> int | None:
    try:
        identity = get_jwt_identity()
        return int(identity)
    except (TypeError, ValueError):
        return None


def _is_admin_assoc(assoc_id: int, user_id: int) -> bool:
    """Verifica se o usuário é admin da associação (role global ou vínculo)."""
    if getattr(g, "user_role", None) in ("admin", "superadmin"):
        return True
    link = UsuarioAssociacao.query.filter_by(
        profissional_id=user_id, associacao_id=assoc_id, status="active"
    ).first()
    return link is not None and link.role == "admin"


def _gerar_codigo() -> str:
    """Código curto alfanumérico (ex.: 6 chars) para aceite manual."""
    alphabet = string.ascii_uppercase + string.digits
    # Evita caracteres ambíguos
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    while True:
        codigo = "".join(secrets.choice(alphabet) for _ in range(6))
        if not ConviteAssociacao.query.filter_by(codigo=codigo).first():
            return codigo


@convites_bp.route("/api/convites", methods=["POST"])
@jwt_required()
def gerar_convite():
    """Gera um convite (email + código + token) para a associação atual."""
    assoc = _associacao_atual()
    user_id = _user_id()
    if not assoc:
        return jsonify({"error": "associação não identificada"}), 400
    if not _is_admin_assoc(assoc.id, user_id):
        return jsonify({"error": "apenas admin da clínica gera convites"}), 403

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "email válido é obrigatório"}), 400

    # Evita duplicar convite pendente para o mesmo email na mesma associação
    existente = ConviteAssociacao.query.filter_by(
        associacao_id=assoc.id, email=email, status="pendente"
    ).first()
    if existente:
        return jsonify({"error": "já existe convite pendente para este email"}), 409

    convite = ConviteAssociacao(
        associacao_id=assoc.id,
        email=email,
        token=uuid.uuid4().hex,
        codigo=_gerar_codigo(),
        role_convidado=data.get("role_convidado", "member"),
        criado_por=user_id,
        expira_em=datetime.utcnow() + timedelta(days=CONVITE_EXPIRA_DIAS),
    )
    db.session.add(convite)
    db.session.commit()

    logger.info("convite_gerado assoc=%s email=%s codigo=%s", assoc.id, email, convite.codigo)
    return jsonify({"success": True, "convite": convite.to_dict()}), 201


@convites_bp.route("/api/convites", methods=["GET"])
@jwt_required()
def listar_convites():
    """Lista convites da associação atual (admin)."""
    assoc = _associacao_atual()
    user_id = _user_id()
    if not assoc:
        return jsonify({"error": "associação não identificada"}), 400
    if not _is_admin_assoc(assoc.id, user_id):
        return jsonify({"error": "apenas admin da clínica lista convites"}), 403

    convites = ConviteAssociacao.query.filter_by(associacao_id=assoc.id).order_by(ConviteAssociacao.id.desc()).all()
    return jsonify({"success": True, "convites": [c.to_dict() for c in convites]}), 200


@convites_bp.route("/api/convites/<int:convite_id>", methods=["DELETE"])
@jwt_required()
def revogar_convite(convite_id):
    """Revoga um convite (admin da associação)."""
    assoc = _associacao_atual()
    user_id = _user_id()
    if not assoc:
        return jsonify({"error": "associação não identificada"}), 400
    if not _is_admin_assoc(assoc.id, user_id):
        return jsonify({"error": "apenas admin da clínica revoga convites"}), 403

    convite = ConviteAssociacao.query.filter_by(id=convite_id, associacao_id=assoc.id).first()
    if not convite:
        return jsonify({"error": "convite não encontrado"}), 404
    if convite.status == "aceito":
        return jsonify({"error": "convite já aceito não pode ser revogado"}), 400

    convite.status = "revogado"
    db.session.commit()
    return jsonify({"success": True, "message": "Convite revogado"}), 200


@convites_bp.route("/api/convites/aceitar", methods=["POST"])
@jwt_required()
def aceitar_por_codigo():
    """Médico logado aceita um convite usando o CÓDIGO."""
    user_id = _user_id()
    if not user_id:
        return jsonify({"error": "usuário não identificado"}), 401

    data = request.get_json(silent=True) or {}
    codigo = (data.get("codigo") or "").strip().upper()
    if not codigo:
        return jsonify({"error": "código é obrigatório"}), 400

    convite = ConviteAssociacao.query.filter_by(codigo=codigo).first()
    if not convite:
        return jsonify({"error": "código inválido"}), 404
    if convite.status != "pendente":
        return jsonify({"error": f"convite {convite.status}"}), 400
    if convite.expira_em and convite.expira_em < datetime.utcnow():
        convite.status = "expirado"
        db.session.commit()
        return jsonify({"error": "convite expirado"}), 400

    return _aceitar(convite, user_id)


@convites_bp.route("/api/convites/token", methods=["POST"])
@jwt_required()
def aceitar_por_token():
    """Médico logado aceita um convite via TOKEN (link)."""
    user_id = _user_id()
    if not user_id:
        return jsonify({"error": "usuário não identificado"}), 401

    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return jsonify({"error": "token é obrigatório"}), 400

    convite = ConviteAssociacao.query.filter_by(token=token).first()
    if not convite:
        return jsonify({"error": "token inválido"}), 404
    if convite.status != "pendente":
        return jsonify({"error": f"convite {convite.status}"}), 400
    if convite.expira_em and convite.expira_em < datetime.utcnow():
        convite.status = "expirado"
        db.session.commit()
        return jsonify({"error": "convite expirado"}), 400

    # Valida que o email do convite bate com o do usuário logado
    from models import Profissional

    prof = db.session.get(Profissional, user_id)
    if prof and prof.email and prof.email.strip().lower() != convite.email:
        return jsonify({
            "error": "este convite foi emitido para outro email",
            "convite_email": convite.email,
        }), 403

    return _aceitar(convite, user_id)


def _aceitar(convite: ConviteAssociacao, user_id: int):
    """Cria/reativa o vínculo do usuário à associação (membro)."""
    # Verifica se já é membro
    link = UsuarioAssociacao.query.filter_by(
        profissional_id=user_id, associacao_id=convite.associacao_id
    ).first()
    if link:
        if link.status == "active":
            return jsonify({"error": "você já é membro desta clínica"}), 400
        link.status = "active"
        link.role = convite.role_convidado or link.role
    else:
        link = UsuarioAssociacao(
            profissional_id=user_id,
            associacao_id=convite.associacao_id,
            role=convite.role_convidado or "member",
            status="active",
        )
        db.session.add(link)

    convite.status = "aceito"
    convite.aceito_em = datetime.utcnow()
    convite.aceito_por = user_id
    db.session.commit()

    logger.info("convite_aceito convite=%s assoc=%s user=%s", convite.id, convite.associacao_id, user_id)
    return jsonify({
        "success": True,
        "message": "Convite aceito — você agora é membro da clínica",
        "associacao_id": convite.associacao_id,
    }), 200
