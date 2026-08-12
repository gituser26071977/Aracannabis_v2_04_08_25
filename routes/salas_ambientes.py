"""Rotas de Salas/Ambientes da clínica (tenant) — gestão de espaços.

Endpoints (JWT, tenant-scoped via `g.current_association`):
    GET    /api/salas/ambientes            → lista espaços da associação
    POST   /api/salas/ambientes            → cria espaço
    PUT    /api/salas/ambientes/<id>       → atualiza espaço
    DELETE /api/salas/ambientes/<id>       → desativa espaço
    GET    /api/salas/ocupacao             → visão de ocupação (para o agente IA)

Os espaços alimentam o agente de IA de gestão de pessoas/espaços/insumos
e conectam com o VSF (visão computacional) via `vsf_room_key`.
"""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import jwt_required

from models import db
from models_extra import SalaAmbiente

logger = logging.getLogger(__name__)

salas_ambientes_bp = Blueprint("salas_ambientes", __name__)

TIPOS_VALIDOS = {
    "consultorio", "sala_espera", "infusao", "procedimento", "banheiro",
    "terapia", "pre_atendimento", "recepcao", "triagem", "outro",
}


def _associacao_id() -> int | None:
    """Resolve a associação atual (tenant) via middleware (P0-12)."""
    assoc = getattr(g, "current_association", None)
    if assoc is not None:
        return getattr(assoc, "id", None)
    return None


@salas_ambientes_bp.route("/api/salas/ambientes", methods=["GET"])
@jwt_required()
def listar_salas():
    """Lista os espaços da associação (tenant) atual."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    salas = SalaAmbiente.query.filter_by(associacao_id=assoc_id).order_by(SalaAmbiente.id).all()
    return jsonify({"success": True, "salas": [s.to_dict() for s in salas]}), 200


@salas_ambientes_bp.route("/api/salas/ambientes", methods=["POST"])
@jwt_required()
def criar_sala():
    """Cria um novo espaço (consultório, sala de espera, infusão, ...)."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    tipo = data.get("tipo", "consultorio")
    if not nome:
        return jsonify({"error": "nome é obrigatório"}), 400
    if tipo not in TIPOS_VALIDOS:
        return jsonify({"error": f"tipo inválido. Use um de: {sorted(TIPOS_VALIDOS)}"}), 400

    try:
        capacidade = int(data.get("capacidade", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "capacidade deve ser inteiro"}), 400

    sala = SalaAmbiente(
        associacao_id=assoc_id,
        nome=nome,
        tipo=tipo,
        capacidade=max(1, capacidade),
        andar=data.get("andar"),
        ala=data.get("ala"),
        recursos=data.get("recursos"),
        vsf_room_key=data.get("vsf_room_key"),
    )
    db.session.add(sala)
    db.session.commit()
    return jsonify({"success": True, "sala": sala.to_dict()}), 201


@salas_ambientes_bp.route("/api/salas/ambientes/<int:sala_id>", methods=["PUT"])
@jwt_required()
def atualizar_sala(sala_id):
    """Atualiza um espaço da associação."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    sala = SalaAmbiente.query.filter_by(id=sala_id, associacao_id=assoc_id).first()
    if not sala:
        return jsonify({"error": "sala não encontrada"}), 404

    data = request.get_json(silent=True) or {}
    if "nome" in data:
        sala.nome = (data["nome"] or "").strip() or sala.nome
    if "tipo" in data and data["tipo"] in TIPOS_VALIDOS:
        sala.tipo = data["tipo"]
    if "capacidade" in data:
        try:
            sala.capacidade = max(1, int(data["capacidade"]))
        except (TypeError, ValueError):
            return jsonify({"error": "capacidade deve ser inteiro"}), 400
    if "ativo" in data:
        sala.ativo = bool(data["ativo"])
    if "vsf_room_key" in data:
        sala.vsf_room_key = data["vsf_room_key"] or None
    if "andar" in data:
        sala.andar = data["andar"]
    if "ala" in data:
        sala.ala = data["ala"]
    if "recursos" in data:
        sala.recursos = data["recursos"] or None

    db.session.commit()
    return jsonify({"success": True, "sala": sala.to_dict()}), 200


@salas_ambientes_bp.route("/api/salas/ambientes/<int:sala_id>", methods=["DELETE"])
@jwt_required()
def desativar_sala(sala_id):
    """Desativa um espaço (soft delete — histórico preservado)."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    sala = SalaAmbiente.query.filter_by(id=sala_id, associacao_id=assoc_id).first()
    if not sala:
        return jsonify({"error": "sala não encontrada"}), 404

    sala.ativo = False
    db.session.commit()
    return jsonify({"success": True, "message": "Sala desativada"}), 200


@salas_ambientes_bp.route("/api/salas/ocupacao", methods=["GET"])
@jwt_required()
def visao_ocupacao():
    """Visão de ocupação dos espaços (para o agente de IA).

    Retorna os espaços ativos com metadados; a ocupação em tempo real é
    alimentada pelo VSF (ROOM_ENTERED/ROOM_EXITED) via vsf_room_key.
    """
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    salas = (
        SalaAmbiente.query.filter_by(associacao_id=assoc_id, ativo=True)
        .order_by(SalaAmbiente.tipo, SalaAmbiente.nome)
        .all()
    )
    resumo: dict[str, int] = {}
    for s in salas:
        resumo[s.tipo] = resumo.get(s.tipo, 0) + 1

    return jsonify({
        "success": True,
        "associacao_id": assoc_id,
        "salas": [s.to_dict() for s in salas],
        "resumo_por_tipo": resumo,
        "total_salas": len(salas),
    }), 200


@salas_ambientes_bp.route("/api/salas/unidade", methods=["GET"])
@jwt_required()
def visao_unidade():
    """Configuração consolidada da unidade (para UI e agente de IA).

    Formato pensado para o VSF (visão computacional): cada espaço expõe
    `vsf_room_key` (RoomRef.room_id) + localização (andar/ala), para os
    eventos ROOM_ENTERED/ROOM_EXITED serem correlacionados.

    Retorna:
        unidade: {nome, total_salas, total_capacidade, resumo_por_tipo}
        salas: lista completa (com andar/ala/capacidade/vsf_room_key)
        total_profissionais: nº de profissionais vinculados à associação
    """
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    from association.models import Associacao
    from models_extra import UsuarioAssociacao

    assoc = db.session.get(Associacao, assoc_id)
    salas = (
        SalaAmbiente.query.filter_by(associacao_id=assoc_id)
        .order_by(SalaAmbiente.tipo, SalaAmbiente.nome)
        .all()
    )
    ativas = [s for s in salas if s.ativo]

    resumo: dict[str, dict] = {}
    for s in ativas:
        entry = resumo.setdefault(
            s.tipo,
            {"quantidade": 0, "capacidade_total": 0, "capacidade_por_espaco": []},
        )
        entry["quantidade"] += 1
        entry["capacidade_total"] += s.capacidade or 0
        entry["capacidade_por_espaco"].append({"nome": s.nome, "lugares": s.capacidade})

    total_profissionais = (
        UsuarioAssociacao.query.filter_by(associacao_id=assoc_id, status="active").count()
    )

    return jsonify({
        "success": True,
        "associacao_id": assoc_id,
        "unidade": {
            "nome": assoc.nome if assoc else None,
            "total_salas": len(ativas),
            "total_capacidade": sum(s.capacidade or 0 for s in ativas),
            "total_profissionais": total_profissionais,
            "resumo_por_tipo": resumo,
        },
        "salas": [s.to_dict() for s in salas],
    }), 200
