"""
Rotas da API de Módulos de Especialidade.

Endpoints:
  GET    /api/modulos                       — Catálogo (público para logados)
  GET    /api/meus-modulos                  — Assinaturas do profissional logado
  GET    /api/meus-modulos/<slug>           — Detalhe de uma assinatura
  POST   /api/modulos/<slug>/ativar-trial   — Inicia trial de 14 dias
  POST   /api/modulos/<slug>/checkout       — Gera link de pagamento MercadoPago
  POST   /api/modulos/<slug>/revogar-consentimento — Revoga consentimento LGPD
  GET    /api/modulos/export                — Exporta dados pessoais (LGPD)
"""
from datetime import datetime, timedelta
import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Profissional
from models_modulos import (
    Modulo,
    ModuloAssinatura,
    ModuloConsentimento,
    TRIAL_DAYS,
)

logger = logging.getLogger(__name__)

modulos_bp = Blueprint("modulos", __name__, url_prefix="/api/modulos")
meus_modulos_bp = Blueprint("meus_modulos", __name__, url_prefix="/api/meus-modulos")


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _current_profissional_id() -> int | None:
    """Lê o id do profissional a partir do JWT. Retorna None se não autenticado."""
    try:
        ident = get_jwt_identity()
        if ident is None:
            return None
        # JWT pode guardar id numérico ou string; aceitar ambos
        return int(ident)
    except (TypeError, ValueError):
        return None


def _get_modulo_or_404(slug: str):
    modulo = Modulo.query.filter_by(slug=slug, ativo=True).first()
    if not modulo:
        return None, (jsonify({"error": f"Módulo '{slug}' não encontrado"}), 404)
    return modulo, None


def _get_or_create_assinatura(prof_id: int, modulo: Modulo) -> ModuloAssinatura:
    """Retorna assinatura existente ou cria uma nova no estado inicial (sem status ativo)."""
    assinatura = ModuloAssinatura.query.filter_by(
        profissional_id=prof_id, modulo_id=modulo.id
    ).first()
    if not assinatura:
        assinatura = ModuloAssinatura(
            profissional_id=prof_id,
            modulo_id=modulo.id,
            status="trial",  # será sobrescrito em ativar-trial/checkout
        )
        db.session.add(assinatura)
        db.session.flush()
    return assinatura


# ──────────────────────────────────────────────────────────────────
# Catálogo público (autenticado)
# ──────────────────────────────────────────────────────────────────

@modulos_bp.route("", methods=["GET"])
@jwt_required()
def listar_catalogo():
    """Lista todos os módulos ativos do catálogo + status do usuário logado."""
    prof_id = _current_profissional_id()
    modulos = Modulo.query.filter_by(ativo=True).order_by(Modulo.ordem, Modulo.nome).all()

    # Indexar assinaturas do profissional para merge
    assinaturas_por_modulo = {}
    if prof_id:
        for a in ModuloAssinatura.query.filter_by(profissional_id=prof_id).all():
            assinaturas_por_modulo[a.modulo_id] = a

    out = []
    for m in modulos:
        a = assinaturas_por_modulo.get(m.id)
        item = m.to_dict()
        item["minha_assinatura"] = a.to_dict() if a else None
        out.append(item)

    # Política de versão corrente — útil para o frontend validar o termo
    politica = "v1"
    if out:
        politica = out[0].get("politica_versao", "v1")

    return jsonify({"modulos": out, "politica_versao": politica}), 200


# ──────────────────────────────────────────────────────────────────
# Minhas assinaturas
# ──────────────────────────────────────────────────────────────────

@meus_modulos_bp.route("", methods=["GET"])
@jwt_required()
def listar_minhas():
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    rows = (
        db.session.query(ModuloAssinatura, Modulo)
        .join(Modulo, Modulo.id == ModuloAssinatura.modulo_id)
        .filter(ModuloAssinatura.profissional_id == prof_id)
        .order_by(Modulo.ordem)
        .all()
    )
    out = [a.to_dict(modulo=m) for (a, m) in rows]
    return jsonify({"assinaturas": out}), 200


@meus_modulos_bp.route("/<slug>", methods=["GET"])
@jwt_required()
def detalhe_minha(slug: str):
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    modulo, err = _get_modulo_or_404(slug)
    if err:
        return err

    a = ModuloAssinatura.query.filter_by(
        profissional_id=prof_id, modulo_id=modulo.id
    ).first()
    if not a:
        return jsonify({"modulo": modulo.to_dict(), "minha_assinatura": None}), 200
    return jsonify(a.to_dict(modulo=modulo)), 200


# ──────────────────────────────────────────────────────────────────
# Ativar trial
# ──────────────────────────────────────────────────────────────────

@modulos_bp.route("/<slug>/ativar-trial", methods=["POST"])
@jwt_required()
def ativar_trial(slug: str):
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    modulo, err = _get_modulo_or_404(slug)
    if err:
        return err

    if modulo.slug == "base":
        return jsonify({"error": "Módulo 'base' já está incluso no plano"}), 400

    body = request.get_json(silent=True) or {}
    consentimento_aceito = bool(body.get("consentimento_aceito"))
    if modulo.requer_consentimento_lgpd and not consentimento_aceito:
        return jsonify({
            "error": "É necessário aceitar o termo de consentimento LGPD",
            "politica_versao": modulo.politica_versao,
        }), 400

    a = _get_or_create_assinatura(prof_id, modulo)

    # Idempotência: se já tem trial ativo ou active, não duplica
    if a.is_acesso_ativo():
        return jsonify({
            "idempotent": True,
            "minha_assinatura": a.to_dict(modulo=modulo),
            "message": "Você já tem acesso a este módulo.",
        }), 200

    # Registrar consentimento (LGPD)
    if modulo.requer_consentimento_lgpd:
        consent = ModuloConsentimento(
            profissional_id=prof_id,
            modulo_id=modulo.id,
            aceito=True,
            politica_versao=modulo.politica_versao,
            ip_origem=request.remote_addr,
            user_agent=(request.user_agent.string or "")[:256],
            aceito_em=datetime.utcnow(),
        )
        db.session.add(consent)

    agora = datetime.utcnow()
    a.status = "trial"
    a.trial_iniciado_em = agora
    a.trial_expira_em = agora + timedelta(days=TRIAL_DAYS)
    a.ativo_desde = agora
    a.cancelado_em = None
    a.expira_em = a.trial_expira_em  # durante trial, expira_em = trial_expira_em

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao ativar trial do modulo %s", slug)
        return jsonify({"error": "Erro interno ao ativar trial"}), 500

    return jsonify({
        "idempotent": False,
        "minha_assinatura": a.to_dict(modulo=modulo),
        "trial_dias": TRIAL_DAYS,
        "message": f"Trial ativado! Aproveite os próximos {TRIAL_DAYS} dias.",
    }), 200


# ──────────────────────────────────────────────────────────────────
# Checkout (MercadoPago)
# ──────────────────────────────────────────────────────────────────

@modulos_bp.route("/<slug>/checkout", methods=["POST"])
@jwt_required()
def checkout(slug: str):
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    modulo, err = _get_modulo_or_404(slug)
    if err:
        return err

    if modulo.slug == "base":
        return jsonify({"error": "Módulo 'base' já está incluso"}), 400
    if modulo.preco_mensal is None or modulo.preco_mensal <= 0:
        return jsonify({"error": "Este módulo é gratuito — ative o trial em vez de pagar"}), 400

    # Tentar usar o serviço de MP se existir; senão gerar link stub para teste
    body = request.get_json(silent=True) or {}
    consentimento_aceito = bool(body.get("consentimento_aceito"))
    if modulo.requer_consentimento_lgpd and not consentimento_aceito:
        return jsonify({
            "error": "É necessário aceitar o termo de consentimento LGPD",
            "politica_versao": modulo.politica_versao,
        }), 400

    # Registrar consentimento (LGPD)
    if modulo.requer_consentimento_lgpd:
        consent = ModuloConsentimento(
            profissional_id=prof_id,
            modulo_id=modulo.id,
            aceito=True,
            politica_versao=modulo.politica_versao,
            ip_origem=request.remote_addr,
            user_agent=(request.user_agent.string or "")[:256],
            aceito_em=datetime.utcnow(),
        )
        db.session.add(consent)
        db.session.commit()

    # Tentar usar MercadoPago service
    init_point = None
    try:
        from services.mercadopago_service import MercadoPagoService  # type: ignore

        mp = MercadoPagoService()
        # Cria preferência com item recorrente (preapproval). Para simplificar,
        # usamos preferência única de 30 dias como fallback.
        resultado = mp.criar_preferencia(
            items=[
                {
                    "title": f"AraOS — Módulo {modulo.nome} (mensal)",
                    "quantity": 1,
                    "unit_price": float(modulo.preco_mensal),
                    "currency_id": "BRL",
                }
            ],
            external_reference=f"modulo:{modulo.slug}:prof:{prof_id}",
            metadata={"modulo_slug": modulo.slug, "profissional_id": prof_id},
        )
        init_point = resultado.get("init_point")
        sandbox_init_point = resultado.get("sandbox_init_point")
    except (ImportError, Exception) as e:
        logger.warning("MercadoPagoService indisponível para checkout módulo %s: %s", slug, e)
        sandbox_init_point = None

    # Fallback para ambientes sem MP configurado: retorna link stub para testes
    if not init_point:
        backend_base = request.host_url.rstrip("/")
        init_point = (
            f"{backend_base}/api/modulos/webhook?simulate=1"
            f"&modulo={modulo.slug}&prof={prof_id}"
        )

    return jsonify({
        "init_point": init_point,
        "sandbox_init_point": sandbox_init_point,
        "modulo": modulo.to_dict(),
        "preco_mensal": modulo.preco_mensal,
    }), 200


# ──────────────────────────────────────────────────────────────────
# Revogar consentimento (LGPD)
# ──────────────────────────────────────────────────────────────────

@modulos_bp.route("/<slug>/revogar-consentimento", methods=["POST"])
@jwt_required()
def revogar_consentimento(slug: str):
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    modulo, err = _get_modulo_or_404(slug)
    if err:
        return err

    # Marca todos os consentimentos como revogados e cancela a assinatura
    consents = ModuloConsentimento.query.filter_by(
        profissional_id=prof_id, modulo_id=modulo.id, aceito=True, revogado_em=None
    ).all()
    agora = datetime.utcnow()
    for c in consents:
        c.aceito = False
        c.revogado_em = agora

    a = ModuloAssinatura.query.filter_by(
        profissional_id=prof_id, modulo_id=modulo.id
    ).first()
    if a:
        a.status = "cancelled"
        a.cancelado_em = agora

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao revogar consentimento do modulo %s", slug)
        return jsonify({"error": "Erro interno"}), 500

    return jsonify({
        "modulo": modulo.to_dict(),
        "consentimentos_revogados": len(consents),
        "assinatura": a.to_dict(modulo=modulo) if a else None,
        "message": "Consentimento revogado. O módulo foi desativado.",
    }), 200


# ──────────────────────────────────────────────────────────────────
# Webhook MercadoPago (após pagamento aprovado)
# ──────────────────────────────────────────────────────────────────

@modulos_bp.route("/webhook", methods=["POST"])
def webhook_mercadopago():
    """Recebe notificações do MercadoPago e ativa assinatura."""
    # Lê JSON ou form
    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.form.to_dict()

    # Para simulação via link stub: aceitar GET também
    if request.method == "GET":
        payload = request.args.to_dict()

    simulate = str(payload.get("simulate", "")).lower() in ("1", "true", "yes")
    modulo_slug = payload.get("modulo") or (
        (payload.get("external_reference") or "").split(":")[1]
        if ":" in (payload.get("external_reference") or "")
        else None
    )
    prof_id_raw = payload.get("prof") or (
        (payload.get("external_reference") or "").split(":")[-1]
        if (payload.get("external_reference") or "").startswith("modulo:")
        else None
    )
    try:
        prof_id = int(prof_id_raw) if prof_id_raw else None
    except (TypeError, ValueError):
        prof_id = None

    if not modulo_slug or not prof_id:
        return jsonify({"error": "payload inválido"}), 400

    modulo = Modulo.query.filter_by(slug=modulo_slug, ativo=True).first()
    if not modulo:
        return jsonify({"error": "modulo nao encontrado"}), 404

    # Em produção: validar assinatura do webhook via WEBHOOK_SECRET_KEY + IP allowlist.
    # Para simulação local, aceitar direto.
    a = _get_or_create_assinatura(prof_id, modulo)
    agora = datetime.utcnow()
    a.status = "active"
    a.ativo_desde = agora
    a.expira_em = agora + timedelta(days=30)
    a.cancelado_em = None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro no webhook do modulo %s", modulo_slug)
        return jsonify({"error": "erro interno"}), 500

    return jsonify({
        "ok": True,
        "simulate": simulate,
        "modulo": modulo.slug,
        "profissional_id": prof_id,
        "status": a.status,
        "expira_em": a.expira_em.isoformat() if a.expira_em else None,
    }), 200


# ──────────────────────────────────────────────────────────────────
# Export (LGPD)
# ──────────────────────────────────────────────────────────────────

@meus_modulos_bp.route("/export", methods=["GET"])
@jwt_required()
def export_lgpd():
    prof_id = _current_profissional_id()
    if not prof_id:
        return jsonify({"error": "Não autenticado"}), 401

    assinaturas = ModuloAssinatura.query.filter_by(profissional_id=prof_id).all()
    consentimentos = ModuloConsentimento.query.filter_by(profissional_id=prof_id).all()

    return jsonify({
        "profissional_id": prof_id,
        "assinaturas": [
            a.to_dict(modulo=Modulo.query.get(a.modulo_id)) for a in assinaturas
        ],
        "consentimentos": [c.to_dict() for c in consentimentos],
        "gerado_em": datetime.utcnow().isoformat(),
    }), 200


__all__ = ["modulos_bp", "meus_modulos_bp"]