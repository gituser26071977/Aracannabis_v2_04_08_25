"""
Middleware de Verificação de Assinatura (Squad B — Segurança & Acesso)

Garante que apenas usuários com assinatura ativa acessem o sistema,
respeitando grace period e feature flags.
"""

import logging
from datetime import datetime, timedelta
from flask import request, jsonify, g, redirect

from models import db, Profissional, Assinatura
from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)

# Rotas públicas que NUNCA devem ser bloqueadas
PUBLIC_PATHS = [
    "/",
    "/planos",
    "/api/webhooks/",
    "/api/status",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/request-password-setup",
    "/api/auth/define-password",
    "/api/csrf-token",
    "/api",
    "/api/planos/",
    "/api/tenant/",
]

# Métodos e prefixos adicionais de bypass
PUBLIC_PREFIXES = [
    "/static/",
    "/api/swagger",
    "/api/docs/",
]


def _is_public_path(path: str) -> bool:
    """Verifica se o caminho é público (não deve ser bloqueado)."""
    if request.method == "OPTIONS":
        return True

    for public in PUBLIC_PATHS:
        if path == public or path.startswith(public.rstrip("/") + "/"):
            return True

    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True

    return False


def get_subscription_status(profissional_id: int):
    """
    Retorna o status da assinatura de um profissional.

    Returns:
        tuple: (
            allowed (bool),
            in_grace_period (bool),
            days_until_block (int | None),
            message (str),
            plano (Plano | None),
            assinatura (Assinatura | None),
        )
    """
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return False, False, None, "Profissional não encontrado.", None, None

    # Admin/superadmin bypass total
    if profissional.role in ("admin", "superadmin"):
        return True, False, None, "Acesso liberado (admin).", None, None

    assinatura = Assinatura.query.filter_by(profissional_id=profissional_id).first()

    # Se não tem assinatura, verifica data_expiracao do profissional (legado)
    if not assinatura:
        if profissional.data_expiracao:
            grace_end = profissional.data_expiracao + timedelta(days=7)
            now = datetime.utcnow()
            if now <= profissional.data_expiracao:
                return True, False, None, "Acesso liberado.", None, None
            elif now <= grace_end:
                days_left = (grace_end - now).days
                return (
                    True,
                    True,
                    days_left,
                    f"Seu período de teste expirou. Você tem {days_left} dia(s) de carência para regularizar sua assinatura.",
                    None,
                    None,
                )
            else:
                return (
                    False,
                    False,
                    None,
                    "Seu acesso expirou. Renove sua assinatura para continuar usando o sistema.",
                    None,
                    None,
                )
        # Sem data de expiração = acesso liberado (legado)
        return True, False, None, "Acesso liberado.", None, None

    plano = assinatura.plano
    now = datetime.utcnow()

    # Status cancelada / inadimplente → bloqueia imediatamente (fora grace)
    if assinatura.status in ("cancelada", "inadimplente"):
        return (
            False,
            False,
            None,
            "Sua assinatura está cancelada/inadimplente. Renove seu plano para continuar.",
            plano,
            assinatura,
        )

    # Status ativa → liberado
    if assinatura.status == "ativa":
        return True, False, None, "Assinatura ativa.", plano, assinatura

    # Status trial → verifica trial_ends_at ou data_expiracao
    if assinatura.status == "trial":
        trial_end = assinatura.trial_ends_at or profissional.data_expiracao
        if not trial_end:
            return True, False, None, "Trial sem data de fim.", plano, assinatura

        grace_end = trial_end + timedelta(days=7)

        if now <= trial_end:
            return True, False, None, "Trial ativo.", plano, assinatura
        elif now <= grace_end:
            days_left = (grace_end - now).days
            return (
                True,
                True,
                days_left,
                f"Seu trial expirou. Você tem {days_left} dia(s) de carência para regularizar sua assinatura.",
                plano,
                assinatura,
            )
        else:
            return (
                False,
                False,
                None,
                "Seu período de teste expirou. Escolha um plano para continuar usando o sistema.",
                plano,
                assinatura,
            )

    # Qualquer outro status → bloqueia
    return (
        False,
        False,
        None,
        "Assinatura inválida. Entre em contato com o suporte.",
        plano,
        assinatura,
    )


def register_subscription_middleware(app):
    """Registra o middleware de assinatura na aplicação Flask."""

    @app.before_request
    def subscription_check():
        path = request.path

        if _is_public_path(path):
            return None

        # Feature flag obrigatória
        if not FeatureFlagService.is_enabled("subscription_block"):
            return None

        # Tentar identificar o usuário via JWT (opcional para não quebrar rotas públicas mistas)
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
        except Exception:
            return None  # Rotas sem JWT seguem fluxo normal (jwt_required trata depois)

        if not identity:
            return None

        try:
            profissional_id = int(identity)
        except (TypeError, ValueError):
            return None

        allowed, in_grace, days_left, message, plano, assinatura = get_subscription_status(
            profissional_id
        )

        # Salvar no contexto para uso em decorators/rotas
        g.subscription_allowed = allowed
        g.subscription_grace = in_grace
        g.subscription_grace_days = days_left
        g.subscription_message = message
        g.subscription_plano = plano
        g.subscription_assinatura = assinatura

        if not allowed:
            # Se for requisição de API (aceita JSON), retorna 403 JSON
            if request.is_json or path.startswith("/api/"):
                response = jsonify(
                    {
                        "error": "Assinatura expirada ou inativa",
                        "message": message,
                        "expired": True,
                        "redirect_to": "/planos",
                    }
                ), 403
                return response

            # Caso contrário (frontend), redireciona
            return redirect("/planos", code=302)

        return None
