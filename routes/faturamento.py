"""Faturamento Clínico — convênios, serviços/tabela, percentuais, contas a receber.

Modalidades:
    - PARTICULAR (padrão): lançamento sem convenio_id; valor = servico.valor_particular.
    - CONVÊNIO: lançamento com convenio_id; valor fixo por serviço na tabela do convênio.

Controle do gestor:
    - Config (convênios, serviços, tabela, percentuais): admin/superadmin.
    - Operação (lançar/receber/estornar): qualquer profissional logado.
    - Visibilidade: profissional vê o próprio faturamento; admin vê tudo.
"""

from __future__ import annotations

import logging
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    Profissional,
    Convenio,
    Servico,
    TabelaPrecoConvenio,
    PercentualRepasse,
    LancamentoFaturamento,
)
from services.faturamento_service import (
    criar_lancamento,
    estornar_lancamento,
    registrar_recebimento,
    listar_lancamentos,
)

logger = logging.getLogger(__name__)

faturamento_bp = Blueprint("faturamento", __name__)


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════

def _current_user() -> Profissional:
    user_id = get_jwt_identity()
    user = Profissional.query.get(user_id)
    return user


def _is_admin(user: Profissional) -> bool:
    return user is not None and user.role in ("admin", "superadmin")


def admin_required(f):
    """Requer gestor: role admin/superadmin OU perfil solo (acesso pleno)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = _current_user()
        if not user:
            return jsonify({"error": "Autenticação necessária."}), 401
        if user.role in ("admin", "superadmin"):
            return f(*args, **kwargs)
        from services.perfil_acesso import resolver_perfil

        if resolver_perfil(user) == "solo":
            return f(*args, **kwargs)
        return jsonify({"error": "Acesso negado. Requer perfil gestor/solo."}), 403
    return decorated


def _parse_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ════════════════════════════════════════════════════════════════════
# Convênios
# ════════════════════════════════════════════════════════════════════

@faturamento_bp.route("/convenios", methods=["GET"])
@jwt_required()
def listar_convenios():
    """Lista convênios (filtro `?apenas_ativos=true`)."""
    apenas_ativos = request.args.get("apenas_ativos", "false").lower() == "true"
    q = Convenio.query.order_by(Convenio.nome)
    if apenas_ativos:
        q = q.filter(Convenio.ativo.is_(True))
    return jsonify({"convenios": [c.to_dict() for c in q.all()]}), 200


@faturamento_bp.route("/convenios", methods=["POST"])
@jwt_required()
@admin_required
def criar_convenio():
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "Nome do convênio é obrigatório"}), 400
    if Convenio.query.filter_by(nome=nome).first():
        return jsonify({"error": "Convênio já cadastrado"}), 409
    convenio = Convenio(
        nome=nome,
        registro_ans=(data.get("registro_ans") or "").strip() or None,
        tipo=data.get("tipo", "operadora"),
        ativo=data.get("ativo", True),
    )
    db.session.add(convenio)
    db.session.commit()
    return jsonify({"message": "Convênio criado", "convenio": convenio.to_dict()}), 201


@faturamento_bp.route("/convenios/<int:convenio_id>", methods=["PUT"])
@jwt_required()
@admin_required
def atualizar_convenio(convenio_id):
    convenio = Convenio.query.get(convenio_id)
    if not convenio:
        return jsonify({"error": "Convênio não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    if "nome" in data:
        nome = (data["nome"] or "").strip()
        if nome:
            convenio.nome = nome
    if "registro_ans" in data:
        convenio.registro_ans = (data["registro_ans"] or "").strip() or None
    if "tipo" in data:
        convenio.tipo = data["tipo"]
    if "ativo" in data:
        convenio.ativo = bool(data["ativo"])
    db.session.commit()
    return jsonify({"message": "Convênio atualizado", "convenio": convenio.to_dict()}), 200


@faturamento_bp.route("/convenios/<int:convenio_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def deletar_convenio(convenio_id):
    convenio = Convenio.query.get(convenio_id)
    if not convenio:
        return jsonify({"error": "Convênio não encontrado"}), 404
    convenio.ativo = False  # soft delete
    db.session.commit()
    return jsonify({"message": "Convênio desativado"}), 200


# ════════════════════════════════════════════════════════════════════
# Serviços / tabela particular
# ════════════════════════════════════════════════════════════════════

@faturamento_bp.route("/servicos", methods=["GET"])
@jwt_required()
def listar_servicos():
    apenas_ativos = request.args.get("apenas_ativos", "false").lower() == "true"
    q = Servico.query.order_by(Servico.nome)
    if apenas_ativos:
        q = q.filter(Servico.ativo.is_(True))
    return jsonify({"servicos": [s.to_dict() for s in q.all()]}), 200


@faturamento_bp.route("/servicos", methods=["POST"])
@jwt_required()
@admin_required
def criar_servico():
    data = request.get_json(silent=True) or {}
    nome = (data.get("nome") or "").strip()
    if not nome:
        return jsonify({"error": "Nome do serviço é obrigatório"}), 400
    servico = Servico(
        nome=nome,
        tipo=data.get("tipo", "consulta"),
        codigo=(data.get("codigo") or "").strip() or None,
        valor_particular=_parse_float(data.get("valor_particular"), 0.0),
        ativo=data.get("ativo", True),
    )
    db.session.add(servico)
    db.session.commit()
    return jsonify({"message": "Serviço criado", "servico": servico.to_dict()}), 201


@faturamento_bp.route("/servicos/<int:servico_id>", methods=["PUT"])
@jwt_required()
@admin_required
def atualizar_servico(servico_id):
    servico = Servico.query.get(servico_id)
    if not servico:
        return jsonify({"error": "Serviço não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    if "nome" in data and (data["nome"] or "").strip():
        servico.nome = data["nome"].strip()
    if "tipo" in data:
        servico.tipo = data["tipo"]
    if "codigo" in data:
        servico.codigo = (data["codigo"] or "").strip() or None
    if "valor_particular" in data:
        valor = _parse_float(data["valor_particular"], None)
        if valor is not None:
            servico.valor_particular = valor
    if "ativo" in data:
        servico.ativo = bool(data["ativo"])
    db.session.commit()
    return jsonify({"message": "Serviço atualizado", "servico": servico.to_dict()}), 200


@faturamento_bp.route("/servicos/<int:servico_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def deletar_servico(servico_id):
    servico = Servico.query.get(servico_id)
    if not servico:
        return jsonify({"error": "Serviço não encontrado"}), 404
    servico.ativo = False
    db.session.commit()
    return jsonify({"message": "Serviço desativado"}), 200


# ════════════════════════════════════════════════════════════════════
# Tabela de preços por convênio (valor fixo por serviço)
# ════════════════════════════════════════════════════════════════════

@faturamento_bp.route("/convenios/<int:convenio_id>/tabela", methods=["GET"])
@jwt_required()
def listar_tabela_convenio(convenio_id):
    itens = TabelaPrecoConvenio.query.filter_by(convenio_id=convenio_id).all()
    return jsonify({"convenio_id": convenio_id, "itens": [i.to_dict() for i in itens]}), 200


@faturamento_bp.route("/convenios/<int:convenio_id>/tabela", methods=["POST"])
@jwt_required()
@admin_required
def upsert_tabela_convenio(convenio_id):
    data = request.get_json(silent=True) or {}
    servico_id = data.get("servico_id")
    valor = _parse_float(data.get("valor"), None)
    if not servico_id or valor is None:
        return jsonify({"error": "servico_id e valor são obrigatórios"}), 400
    if not Convenio.query.get(convenio_id):
        return jsonify({"error": "Convênio não encontrado"}), 404
    if not Servico.query.get(servico_id):
        return jsonify({"error": "Serviço não encontrado"}), 404
    item = TabelaPrecoConvenio.query.filter_by(
        convenio_id=convenio_id, servico_id=servico_id
    ).first()
    if item:
        item.valor = valor
        item.ativo = data.get("ativo", True)
    else:
        item = TabelaPrecoConvenio(
            convenio_id=convenio_id, servico_id=servico_id, valor=valor, ativo=True
        )
        db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Tabela atualizada", "item": item.to_dict()}), 200


@faturamento_bp.route("/convenios/<int:convenio_id>/tabela/<int:servico_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def remover_tabela_convenio(convenio_id, servico_id):
    item = TabelaPrecoConvenio.query.filter_by(
        convenio_id=convenio_id, servico_id=servico_id
    ).first()
    if not item:
        return jsonify({"error": "Item não encontrado"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item removido da tabela"}), 200


# ════════════════════════════════════════════════════════════════════
# Percentual de repasse do profissional (por serviço; global se servico_id NULL)
# ════════════════════════════════════════════════════════════════════

@faturamento_bp.route("/profissionais/<int:profissional_id>/percentuais", methods=["GET"])
@jwt_required()
def listar_percentuais(profissional_id):
    itens = PercentualRepasse.query.filter_by(profissional_id=profissional_id).all()
    return jsonify(
        {"profissional_id": profissional_id, "itens": [i.to_dict() for i in itens]}
    ), 200


@faturamento_bp.route("/profissionais/<int:profissional_id>/percentuais", methods=["POST"])
@jwt_required()
@admin_required
def upsert_percentual(profissional_id):
    data = request.get_json(silent=True) or {}
    servico_id = data.get("servico_id")  # None = global
    percentual = _parse_float(data.get("percentual"), None)
    if percentual is None or not (0 <= percentual <= 100):
        return jsonify({"error": "percentual deve estar entre 0 e 100"}), 400
    if servico_id is not None and not Servico.query.get(servico_id):
        return jsonify({"error": "Serviço não encontrado"}), 404
    if not Profissional.query.get(profissional_id):
        return jsonify({"error": "Profissional não encontrado"}), 404
    item = PercentualRepasse.query.filter_by(
        profissional_id=profissional_id, servico_id=servico_id
    ).first()
    if item:
        item.percentual = percentual
        item.ativo = data.get("ativo", True)
    else:
        item = PercentualRepasse(
            profissional_id=profissional_id,
            servico_id=servico_id,
            percentual=percentual,
            ativo=True,
        )
        db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Percentual atualizado", "item": item.to_dict()}), 200


@faturamento_bp.route("/profissionais/<int:profissional_id>/percentuais/<int:item_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def remover_percentual(profissional_id, item_id):
    item = PercentualRepasse.query.get(item_id)
    if not item or item.profissional_id != profissional_id:
        return jsonify({"error": "Item não encontrado"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Percentual removido"}), 200


# ════════════════════════════════════════════════════════════════════
# Lançamentos (contas a receber)
# ════════════════════════════════════════════════════════════════════

@faturamento_bp.route("/lancamentos", methods=["POST"])
@jwt_required()
def lancar_faturamento():
    """Cria a conta a receber. `convenio_id` ausente/null = PARTICULAR.

    Body: servico_id, profissional_id (default = usuário logado), convenio_id?,
    paciente_id?, atendimento_id?, desconto?, forma_pagamento?, observacao?
    """
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    data = request.get_json(silent=True) or {}
    servico_id = data.get("servico_id")
    if not servico_id:
        return jsonify({"error": "servico_id é obrigatório"}), 400
    profissional_id = data.get("profissional_id") or user.id
    try:
        lancamento = criar_lancamento(
            servico_id=int(servico_id),
            profissional_id=int(profissional_id),
            convenio_id=int(data["convenio_id"]) if data.get("convenio_id") else None,
            paciente_id=int(data["paciente_id"]) if data.get("paciente_id") else None,
            atendimento_id=int(data["atendimento_id"]) if data.get("atendimento_id") else None,
            desconto=_parse_float(data.get("desconto"), 0.0),
            forma_pagamento=data.get("forma_pagamento", "dinheiro"),
            observacao=data.get("observacao"),
            criado_por=str(user.id),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:  # noqa: BLE001
        logger.exception("falha_ao_lancar_faturamento")
        return jsonify({"error": "Erro ao lançar faturamento"}), 500
    return jsonify({"message": "Faturamento lançado", "lancamento": lancamento.to_dict()}), 201


@faturamento_bp.route("/lancamentos", methods=["GET"])
@jwt_required()
def listar_lancamentos_view():
    """Lista contas a receber com filtros (status, modalidade, profissional, convenio, período)."""
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    args = request.args
    profissional_id = args.get("profissional_id", type=int)
    if not _is_admin(user) and profissional_id is None:
        profissional_id = user.id  # profissional vê o próprio
    try:
        total, itens = listar_lancamentos(
            status=args.get("status"),
            profissional_id=profissional_id,
            convenio_id=args.get("convenio_id", type=int),
            modalidade=args.get("modalidade"),
            de=args.get("de"),
            ate=args.get("ate"),
            limit=min(args.get("limit", 200, type=int), 500),
            offset=args.get("offset", 0, type=int),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "total": total,
        "lancamentos": [l.to_dict() for l in itens],
    }), 200


@faturamento_bp.route("/lancamentos/<int:lancamento_id>/receber", methods=["POST"])
@jwt_required()
def receber_lancamento(lancamento_id):
    """Registra pagamento (parcial/múltiplo) de um lançamento."""
    data = request.get_json(silent=True) or {}
    valor = _parse_float(data.get("valor"), None)
    if valor is None:
        return jsonify({"error": "valor é obrigatório"}), 400
    user = _current_user()
    try:
        lancamento = registrar_recebimento(
            lancamento_id,
            valor,
            forma_pagamento=data.get("forma_pagamento", "dinheiro"),
            observacao=data.get("observacao"),
            criado_por=str(user.id) if user else None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "Recebimento registrado", "lancamento": lancamento.to_dict()}), 200


@faturamento_bp.route("/lancamentos/<int:lancamento_id>/estornar", methods=["POST"])
@jwt_required()
@admin_required
def estornar_lancamento_view(lancamento_id):
    user = _current_user()
    try:
        lancamento = estornar_lancamento(
            lancamento_id, criado_por=str(user.id) if user else None
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "Lançamento estornado", "lancamento": lancamento.to_dict()}), 200


@faturamento_bp.route("/minha-situacao", methods=["GET"])
@jwt_required()
def minha_situacao_financeira():
    """Situação financeira do próprio profissional (read-only, seus lançamentos).

    Visível também ao perfil assistencial (exceção controlada): o médico
    acompanha o financeiro dos próprios pacientes sem operar o faturamento.
    """
    user = _current_user()
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    lancamentos = LancamentoFaturamento.query.filter_by(
        profissional_id=user.id
    ).all()

    a_receber = sum(l.valor_receber for l in lancamentos if l.status != "cancelado")
    recebido = sum(
        l.valor_receber for l in lancamentos if l.status in ("pago", "parcial")
    )
    pendente = sum(
        (l.valor_receber - sum(r.valor for r in l.recebimentos))
        for l in lancamentos if l.status in ("pendente", "parcial")
    )
    repasse_due = sum(
        l.valor_repasse for l in lancamentos if l.status != "cancelado"
    )

    por_status = {"pendente": 0, "parcial": 0, "pago": 0, "cancelado": 0}
    for l in lancamentos:
        por_status[l.status] = por_status.get(l.status, 0) + 1

    return jsonify({
        "profissional_id": user.id,
        "total_lancado": round(a_receber, 2),
        "recebido": round(recebido, 2),
        "pendente": round(max(pendente, 0.0), 2),
        "repasse_due": round(repasse_due, 2),
        "por_status": por_status,
        "lancamentos": [l.to_dict() for l in sorted(
            lancamentos, key=lambda x: x.data_lancamento, reverse=True
        )[:50]],
    }), 200
