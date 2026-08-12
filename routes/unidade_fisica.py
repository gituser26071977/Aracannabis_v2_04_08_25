"""Rotas da hierarquia física da unidade (instalação → andar/setor → espaço).

Endpoints (JWT, tenant-scoped; gestor/secretária/admin):
    GET    /api/unidade              → lista instalações da associação
    POST   /api/unidade              → cria instalação (clínica/hospital/...)
    PUT    /api/unidade/<id>         → atualiza instalação
    GET    /api/unidade/<id>         → instalação com andares + espaços (árvore)
    POST   /api/unidade/<id>/andares → cria andar/setor
    PUT    /api/unidade/andares/<id> → atualiza andar/setor

Espelha o modelo Facility → Sector → Bed do CareOS e expõe as chaves
para o VSF (vsf_facility_key = Location.facility_id).
"""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import jwt_required

from models import db
from models_extra import AndarSetor, SalaAmbiente, UnidadeFisica

logger = logging.getLogger(__name__)

unidade_bp = Blueprint("unidade_fisica", __name__)

TIPOS_UNIDADE = {"clinica", "consultorio", "hospital", "home_care"}
TIPOS_ANDAR = {"andar", "ala", "setor", "uti", "centro_cirurgico", "recepcao", "outro"}


def _associacao_id() -> int | None:
    """Resolve a associação atual (tenant) via middleware (P0-12)."""
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)


@unidade_bp.route("/api/unidade", methods=["GET"])
@jwt_required()
def listar_unidades():
    """Lista instalações da associação atual."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400
    unidades = UnidadeFisica.query.filter_by(associacao_id=assoc_id).order_by(UnidadeFisica.id).all()
    return jsonify({"success": True, "unidades": [u.to_dict() for u in unidades]}), 200


@unidade_bp.route("/api/unidade", methods=["POST"])
@jwt_required()
def criar_unidade():
    """Cria uma instalação (clínica, consultório, hospital, home care)."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    tipo = data.get("tipo", "clinica")
    if not nome:
        return jsonify({"error": "nome é obrigatório"}), 400
    if tipo not in TIPOS_UNIDADE:
        return jsonify({"error": f"tipo inválido. Use: {sorted(TIPOS_UNIDADE)}"}), 400

    unidade = UnidadeFisica(
        associacao_id=assoc_id,
        nome=nome,
        tipo=tipo,
        endereco=data.get("endereco"),
        cidade=data.get("cidade"),
        uf=data.get("uf"),
        possui_uti=bool(data.get("possui_uti", False)),
        possui_centro_cirurgico=bool(data.get("possui_centro_cirurgico", False)),
        vsf_facility_key=data.get("vsf_facility_key"),
    )
    db.session.add(unidade)
    db.session.commit()
    return jsonify({"success": True, "unidade": unidade.to_dict()}), 201


@unidade_bp.route("/api/unidade/<int:unidade_id>", methods=["PUT"])
@jwt_required()
def atualizar_unidade(unidade_id):
    """Atualiza uma instalação."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400
    unidade = UnidadeFisica.query.filter_by(id=unidade_id, associacao_id=assoc_id).first()
    if not unidade:
        return jsonify({"error": "instalação não encontrada"}), 404

    data = request.get_json(silent=True) or {}
    if "nome" in data:
        unidade.nome = (data["nome"] or "").strip() or unidade.nome
    if "tipo" in data and data["tipo"] in TIPOS_UNIDADE:
        unidade.tipo = data["tipo"]
    for campo in ("endereco", "cidade", "uf", "vsf_facility_key"):
        if campo in data:
            setattr(unidade, campo, data[campo] or None)
    if "possui_uti" in data:
        unidade.possui_uti = bool(data["possui_uti"])
    if "possui_centro_cirurgico" in data:
        unidade.possui_centro_cirurgico = bool(data["possui_centro_cirurgico"])
    if "ativo" in data:
        unidade.ativo = bool(data["ativo"])

    db.session.commit()
    return jsonify({"success": True, "unidade": unidade.to_dict()}), 200


@unidade_bp.route("/api/unidade/<int:unidade_id>", methods=["GET"])
@jwt_required()
def obter_unidade_arvore(unidade_id):
    """Instalação com a árvore completa: andares → espaços (para VSF/UI/agente)."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400
    unidade = UnidadeFisica.query.filter_by(id=unidade_id, associacao_id=assoc_id).first()
    if not unidade:
        return jsonify({"error": "instalação não encontrada"}), 404

    andares = AndarSetor.query.filter_by(unidade_id=unidade_id).order_by(AndarSetor.ordem, AndarSetor.id).all()
    espacos = SalaAmbiente.query.filter_by(associacao_id=assoc_id).all()

    # monta árvore: andar → espaços (diretos) + sub-setores
    andares_out = []
    for a in andares:
        sub = [s.to_dict() for s in andares if s.parent_id == a.id]
        espacos_do_andar = [
            s.to_dict() for s in espacos
            if s.andar_setor_id == a.id or (s.unidade_id == unidade_id and s.andar_setor_id is None)
        ]
        andares_out.append({**a.to_dict(), "sub_setores": sub, "espacos": espacos_do_andar})

    return jsonify({
        "success": True,
        "unidade": unidade.to_dict(),
        "andares": andares_out,
        "total_espacos": len(espacos),
    }), 200


@unidade_bp.route("/api/unidade/<int:unidade_id>/andares", methods=["POST"])
@jwt_required()
def criar_andar(unidade_id):
    """Cria um andar/setor dentro da instalação (UTI, ala, centro cirúrgico...)."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400
    unidade = UnidadeFisica.query.filter_by(id=unidade_id, associacao_id=assoc_id).first()
    if not unidade:
        return jsonify({"error": "instalação não encontrada"}), 404

    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    tipo = data.get("tipo", "andar")
    if not nome:
        return jsonify({"error": "nome é obrigatório"}), 400
    if tipo not in TIPOS_ANDAR:
        return jsonify({"error": f"tipo inválido. Use: {sorted(TIPOS_ANDAR)}"}), 400

    andar = AndarSetor(
        associacao_id=assoc_id,
        unidade_id=unidade_id,
        nome=nome,
        tipo=tipo,
        parent_id=data.get("parent_id"),
        ordem=int(data.get("ordem", 0)),
    )
    db.session.add(andar)
    db.session.commit()
    return jsonify({"success": True, "andar": andar.to_dict()}), 201


@unidade_bp.route("/api/unidade/andares/<int:andar_id>", methods=["PUT"])
@jwt_required()
def atualizar_andar(andar_id):
    """Atualiza um andar/setor."""
    assoc_id = _associacao_id()
    if not assoc_id:
        return jsonify({"error": "associação não identificada"}), 400
    andar = AndarSetor.query.filter_by(id=andar_id, associacao_id=assoc_id).first()
    if not andar:
        return jsonify({"error": "andar não encontrado"}), 404

    data = request.get_json(silent=True) or {}
    if "nome" in data:
        andar.nome = (data["nome"] or "").strip() or andar.nome
    if "tipo" in data and data["tipo"] in TIPOS_ANDAR:
        andar.tipo = data["tipo"]
    if "parent_id" in data:
        andar.parent_id = data["parent_id"]
    if "ordem" in data:
        try:
            andar.ordem = int(data["ordem"])
        except (TypeError, ValueError):
            return jsonify({"error": "ordem deve ser inteiro"}), 400
    if "ativo" in data:
        andar.ativo = bool(data["ativo"])

    db.session.commit()
    return jsonify({"success": True, "andar": andar.to_dict()}), 200
