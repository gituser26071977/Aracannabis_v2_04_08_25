"""
Decorators de Rotas Protegidas (Squad B — Segurança & Acesso)

- require_active_subscription
- require_plan(plan_identifier)
- require_feature(feature_identifier)
- require_role(*allowed_roles)              [Fase 3 — RBAC secretária]
- require_permission(permission_name)         [Fase 3 — RBAC secretária]
- require_association_member()                [Fase 3 — RBAC secretária]

Os decorators de subscription/plan/feature ficam atrás da flag 'plan_enforcement'.
Os decorators de RBAC (role/permission/association) são sempre ativos e
consultam `g.user_role` e `g.user_permissions` populados pelo PermissionMiddleware.
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


# ═══════════════════════════════════════════════════════════════════════
# RBAC DECORATORS (Fase 3 — RBAC Secretária)
# ═══════════════════════════════════════════════════════════════════════

def _resolve_profissional_role() -> str | None:
    """
    Resolve a role GLOBAL do profissional atual a partir do JWT.
    Retorna None se não autenticado.
    """
    try:
        identity = get_jwt_identity()
        if not identity:
            return None
        profissional = Profissional.query.get(int(identity))
        if not profissional:
            return None
        return profissional.role
    except Exception as exc:
        logger.warning("Falha ao resolver role do profissional: %s", exc)
        return None


def require_role(*allowed_roles: str):
    """
    Bloqueia request se a role GLOBAL do profissional não está em `allowed_roles`.

    Regras:
      - 'admin' e 'superadmin' sempre passam (bypass).
      - Aceita múltiplas roles: @require_role('admin', 'manager', 'secretary').
      - Aceita 'qualquer' como bypass explícito (equivalente a não usar decorator).
      - Aceita callable predicate para lógica custom: @require_role(lambda r: r in (...)).

    Deve ser usado APÓS @jwt_required() (ou em rota que já valide auth).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not allowed_roles or "qualquer" in allowed_roles:
                return f(*args, **kwargs)

            role = _resolve_profissional_role()

            # Admin bypass
            if role in ("admin", "superadmin"):
                return f(*args, **kwargs)

            # Suporte a predicate
            for allowed in allowed_roles:
                if callable(allowed):
                    try:
                        if allowed(role):
                            return f(*args, **kwargs)
                    except Exception:
                        continue
                elif allowed == role:
                    return f(*args, **kwargs)

            logger.info(
                "Acesso negado: role=%s não está em allowed=%s para %s",
                role, allowed_roles, f.__name__,
            )
            return jsonify({
                "error": "Acesso negado",
                "message": f"Sua role ({role or 'desconhecida'}) não tem permissão para este recurso.",
                "required_roles": [r for r in allowed_roles if not callable(r)],
            }), 403

        return decorated_function

    return decorator


def require_permission(permission_name: str):
    """
    Bloqueia request se a permissão AraOS não está em `g.user_permissions`.

    `g.user_permissions` é populado pelo PermissionMiddleware (before_request)
    combinando Profissional.role + UsuarioAssociacao.role.

    Regras:
      - Admin global sempre passa (todas as permissões).
      - 'permission_name' deve ser uma string do tipo 'resource.action' registrada
        em Permission (araos.platform.identity.permissions). Validação runtime via
        PermissionRegistry.is_valid (best-effort; warning se não registrada).
    """
    # Validação best-effort da permissão
    try:
        from araos.platform.identity.permissions import PermissionRegistry
        if not PermissionRegistry.is_valid(permission_name):
            logger.warning(
                "require_permission: '%s' não está registrada no PermissionRegistry "
                "(pode ser wildcard ou typo).", permission_name,
            )
    except Exception:
        pass

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Admin bypass
            role = _resolve_profissional_role()
            if role in ("admin", "superadmin"):
                return f(*args, **kwargs)

            user_perms = getattr(g, "user_permissions", None) or frozenset()

            # Verifica permissão direta
            if permission_name in user_perms:
                return f(*args, **kwargs)

            # Verifica wildcards (ex: 'patient.*' cobre 'patient.read')
            resource = permission_name.split(".", 1)[0] if "." in permission_name else None
            if resource and f"{resource}.*" in user_perms:
                return f(*args, **kwargs)

            logger.info(
                "Acesso negado: permissão '%s' ausente para %s",
                permission_name, f.__name__,
            )
            return jsonify({
                "error": "Acesso negado",
                "message": f"Você não tem a permissão necessária ({permission_name}) para este recurso.",
                "required_permission": permission_name,
            }), 403

        return decorated_function

    return decorator


def require_association_member(f):
    """
    Bloqueia request se o usuário não está vinculado a uma associação ativa.

    Use em rotas multi-tenant que operam dentro do escopo de uma clínica.
    Bypassa para admin/superadmin (eles podem operar sem associação).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = _resolve_profissional_role()
        if role in ("admin", "superadmin"):
            return f(*args, **kwargs)

        current_assoc = getattr(g, "current_association", None)
        if not current_assoc:
            return jsonify({
                "error": "Associação necessária",
                "message": "Você precisa estar vinculado a uma instituição para acessar este recurso.",
            }), 403

        return f(*args, **kwargs)

    return decorated_function
