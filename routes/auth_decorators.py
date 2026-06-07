"""
Decorators de Rotas Protegidas (Squad B — Segurança & Acesso)

- require_active_subscription
- require_plan(plan_identifier)
- require_feature(feature_identifier)

Tudo atrás da feature flag 'plan_enforcement'.
"""

import logging
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity

from models import db, Profissional, Assinatura, Paciente, Plano
from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)


def _get_current_profissional_id() -> int | None:
    """Obtém o ID do profissional autenticado."""
    try:
        identity = get_jwt_identity()
        if identity is not None:
            return int(identity)
    except Exception:
        pass
    return None


def _get_profissional_and_subscription(profissional_id: int):
    """Busca profissional, assinatura e plano de forma eficiente."""
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return None, None, None

    if profissional.role in ("admin", "superadmin"):
        # Admin bypassa limites de plano
        return profissional, None, None

    assinatura = Assinatura.query.filter_by(profissional_id=profissional_id).first()
    plano = assinatura.plano if assinatura else None
    return profissional, assinatura, plano


def require_active_subscription(f):
    """
    Decorator que exige assinatura ativa (ou dentro do grace period).
    Deve ser usado APÓS @jwt_required().
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not FeatureFlagService.is_enabled("plan_enforcement"):
            return f(*args, **kwargs)

        profissional_id = _get_current_profissional_id()
        if not profissional_id:
            return jsonify({"error": "Autenticação necessária."}), 401

        from middleware.subscription_middleware import get_subscription_status

        allowed, in_grace, days_left, message, plano, assinatura = get_subscription_status(
            profissional_id
        )

        if not allowed:
            return (
                jsonify(
                    {
                        "error": "Assinatura inativa ou expirada",
                        "message": message,
                        "expired": True,
                        "redirect_to": "/planos",
                    }
                ),
                403,
            )

        # Se estiver no grace period, adiciona aviso no header da resposta
        if in_grace and days_left is not None:
            response = f(*args, **kwargs)
            if hasattr(response, "headers"):
                response.headers["X-Subscription-Grace-Days"] = str(days_left)
            return response

        return f(*args, **kwargs)

    return decorated_function


def require_plan(plan_identifier: str):
    """
    Decorator que bloqueia acesso se o plano do usuário não incluir o recurso.

    plan_identifier:
        - 'com_ia': exige limite_agentes_ia > 0 no plano
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not FeatureFlagService.is_enabled("plan_enforcement"):
                return f(*args, **kwargs)

            profissional_id = _get_current_profissional_id()
            if not profissional_id:
                return jsonify({"error": "Autenticação necessária."}), 401

            profissional, assinatura, plano = _get_profissional_and_subscription(
                profissional_id
            )

            if not profissional:
                return jsonify({"error": "Profissional não encontrado."}), 404

            # Admin bypass
            if profissional.role in ("admin", "superadmin"):
                return f(*args, **kwargs)

            if plan_identifier == "com_ia":
                # Verifica se o plano inclui IA
                has_ia = False
                if plano and plano.limite_agentes_ia and plano.limite_agentes_ia > 0:
                    has_ia = True
                if not has_ia:
                    return (
                        jsonify(
                            {
                                "error": "Recurso não incluído no plano",
                                "message": "Este recurso de IA não está disponível no seu plano atual. Atualize para o Plano Com IA.",
                                "plan_required": "com_ia",
                                "redirect_to": "/planos",
                            }
                        ),
                        403,
                    )
            else:
                # Identificador de plano desconhecido — bloqueia por segurança
                logger.warning(f"require_plan: identificador desconhecido '{plan_identifier}'")
                return (
                    jsonify(
                        {
                            "error": "Configuração de plano inválida",
                            "message": "Entre em contato com o suporte.",
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_ia_rate_limit(f):
    """
    Decorator que aplica rate limit por tenant/plano para rotas de IA.
    - Plano Sem IA: 0 req/min (bloqueia com 403)
    - Plano Com IA: limite_agentes_ia req/min (bloqueia com 429 se exceder)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not FeatureFlagService.is_enabled("plan_enforcement"):
            return f(*args, **kwargs)

        profissional_id = _get_current_profissional_id()
        if not profissional_id:
            return jsonify({"error": "Autenticação necessária."}), 401

        from services.rate_limit_service import (
            get_ia_rate_limit_for_profissional,
            check_ia_rate_limit,
        )

        limit = get_ia_rate_limit_for_profissional(profissional_id)
        if limit <= 0:
            return (
                jsonify(
                    {
                        "error": "Recurso de IA bloqueado",
                        "message": "Seu plano não inclui recursos de IA. Atualize para o Plano Com IA.",
                        "redirect_to": "/planos",
                    }
                ),
                403,
            )

        allowed, current, limit = check_ia_rate_limit(profissional_id, limit)
        if not allowed:
            return (
                jsonify(
                    {
                        "error": "Limite de requisições IA excedido",
                        "message": f"Você atingiu o limite de {limit} requisição(ões) por minuto no seu plano. Aguarde um momento e tente novamente.",
                        "limit": limit,
                        "current": current,
                    }
                ),
                429,
            )

        return f(*args, **kwargs)

    return decorated_function


def require_feature(feature_identifier: str):
    """
    Decorator que verifica limites quantitativos do plano.

    feature_identifier:
        - 'unlimited_patients': verifica se atingiu limite_pacientes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not FeatureFlagService.is_enabled("plan_enforcement"):
                return f(*args, **kwargs)

            profissional_id = _get_current_profissional_id()
            if not profissional_id:
                return jsonify({"error": "Autenticação necessária."}), 401

            profissional, assinatura, plano = _get_profissional_and_subscription(
                profissional_id
            )

            if not profissional:
                return jsonify({"error": "Profissional não encontrado."}), 404

            # Admin bypass
            if profissional.role in ("admin", "superadmin"):
                return f(*args, **kwargs)

            if feature_identifier == "unlimited_patients":
                # Contar pacientes do profissional (como responsável)
                count = Paciente.query.filter_by(
                    profissional_responsavel_id=profissional_id
                ).count()

                limit = plano.limite_pacientes if plano else 50
                if limit is None or limit < 0:
                    limit = 999999  # ilimitado

                if count >= limit:
                    return (
                        jsonify(
                            {
                                "error": "Limite de pacientes atingido",
                                "message": f"Você atingiu o limite de {limit} paciente(s) do seu plano. Atualize seu plano para cadastrar mais.",
                                "limit": limit,
                                "used": count,
                                "redirect_to": "/planos",
                            }
                        ),
                        403,
                    )
            else:
                logger.warning(
                    f"require_feature: identificador desconhecido '{feature_identifier}'"
                )
                return (
                    jsonify(
                        {
                            "error": "Configuração de recurso inválida",
                            "message": "Entre em contato com o suporte.",
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
