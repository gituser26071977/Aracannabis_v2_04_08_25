"""
Decorators de Rotas Protegidas (Squad B — Segurança & Acesso)

- require_active_subscription
- require_plan(plan_identifier)
- require_feature(feature_identifier)
- require_permission(*permissions)              [NOVO - Mission 8 Secretária]
- require_staff_role(*roles)                     [NOVO - Mission 8 Secretária]

Tudo atrás da feature flag 'plan_enforcement'.
"""

import logging
from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity

from models import db, Profissional, Assinatura, Paciente, Plano
from services.feature_flag_service import FeatureFlagService
from araos.platform.identity.permissions import RoleRegistry, Permission

logger = logging.getLogger(__name__)


# Roles que têm bypass total de checagem de permissão.
# Admin/Superadmin sempre podem tudo; manager tem permissões amplas.
_ROLE_BYPASS = {"admin", "superadmin"}


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


def _resolve_user_role_names(profissional: Profissional) -> list[str]:
    """Resolve o conjunto de nomes de role ativos para o usuário.

    Combina role global (Profissional.role) com role institucional
    (UsuarioAssociacao.role) se houver tenant context.
    """
    roles: list[str] = [profissional.role] if profissional.role else []
    # Adiciona role institucional se houver tenant context ativo
    link_role = getattr(g, "user_role", None)
    if link_role and link_role not in roles:
        roles.append(link_role)
    return roles


# ════════════════════════════════════════════════════════════════════
# Mission 8 — Decorators Secretária / RBAC granular
# ════════════════════════════════════════════════════════════════════
def require_permission(*permissions: str):
    """
    Bloqueia request se usuário não possui nenhuma das permissões informadas.

    Bypass: admin, superadmin sempre passam.

    Uso:
        @require_permission(Permission.PATIENT_READ)
        def listar_pacientes(): ...

        # Aceita múltiplas (OR — qualquer uma basta):
        @require_permission(Permission.PRESCRIPTION_WRITE, Permission.AI_USE)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            profissional_id = _get_current_profissional_id()
            if not profissional_id:
                return jsonify({"error": "Autenticação necessária."}), 401

            profissional = Profissional.query.get(profissional_id)
            if not profissional:
                return jsonify({"error": "Profissional não encontrado."}), 404

            if profissional.role in _ROLE_BYPASS:
                return f(*args, **kwargs)

            role_names = _resolve_user_role_names(profissional)
            if not RoleRegistry.check_any_permission(role_names, list(permissions)):
                logger.warning(
                    "RBAC: user_id=%s role=%s tentou acessar endpoint protegido (perms=%s)",
                    profissional_id, profissional.role, list(permissions),
                )
                return (
                    jsonify(
                        {
                            "error": "Permissão negada",
                            "message": "Você não tem permissão para esta operação.",
                            "required_permissions": list(permissions),
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_modulo(modulo_slug: str):
    """Bloqueia request se o profissional não tem o módulo de especialidade ativo.

    Gating por módulo aditivo (ex.: 'nutrologia', 'cardiologia', 'oncologia').
    Bypass: admin/superadmin sempre passam.

    Uso:
        @require_modulo('nutrologia')
        def calcular_plano(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            profissional_id = _get_current_profissional_id()
            if not profissional_id:
                return jsonify({"error": "Autenticação necessária."}), 401

            profissional = Profissional.query.get(profissional_id)
            if not profissional:
                return jsonify({"error": "Profissional não encontrado."}), 404

            if profissional.role in _ROLE_BYPASS:
                return f(*args, **kwargs)

            # O módulo 'base' está sempre incluso
            if modulo_slug == "base":
                return f(*args, **kwargs)

            from models_modulos import Modulo, ModuloAssinatura

            modulo = Modulo.query.filter_by(slug=modulo_slug, ativo=True).first()
            if not modulo:
                logger.warning("require_modulo: módulo inexistente %s", modulo_slug)
                return (
                    jsonify({"error": "Módulo não encontrado", "modulo": modulo_slug}),
                    404,
                )

            assinatura = ModuloAssinatura.query.filter_by(
                profissional_id=profissional_id, modulo_id=modulo.id
            ).first()
            if not assinatura or not assinatura.is_acesso_ativo():
                logger.warning(
                    "require_modulo: user=%s sem acesso ao módulo %s",
                    profissional_id, modulo_slug,
                )
                return (
                    jsonify(
                        {
                            "error": "Este recurso requer o módulo ativo",
                            "message": f"Ative o módulo {modulo.nome} para usar esta funcionalidade.",
                            "modulo": modulo_slug,
                            "modulo_nome": modulo.nome,
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def require_staff_role(*allowed_roles: str):
    """
    Bloqueia request se a role do usuário não está na lista permitida.

    Aceita role global (Profissional.role) OU role institucional
    (g.user_role). Use para separar fluxos "secretary", "manager", "admin".

    Bypass: admin/superadmin sempre passam.

    Uso:
        @require_staff_role("secretary", "admin", "manager")
        def cancelar_consulta(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            profissional_id = _get_current_profissional_id()
            if not profissional_id:
                return jsonify({"error": "Autenticação necessária."}), 401

            profissional = Profissional.query.get(profissional_id)
            if not profissional:
                return jsonify({"error": "Profissional não encontrado."}), 404

            if profissional.role in _ROLE_BYPASS:
                return f(*args, **kwargs)

            user_roles = _resolve_user_role_names(profissional)
            if not any(r in allowed_roles for r in user_roles):
                logger.warning(
                    "RBAC: user_id=%s roles=%s não autorizado (allowed=%s)",
                    profissional_id, user_roles, list(allowed_roles),
                )
                return (
                    jsonify(
                        {
                            "error": "Acesso restrito",
                            "message": "Esta operação é exclusiva para perfis específicos.",
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator


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


def require_clinica_management(f):
    """
    Decorator que bloqueia acesso se o plano do usuário não permitir
    gestão de clínica (Plano.permite_gestao_clinica == False).

    Aplica-se a endpoints de CRUD de Clínica em `association/routes.py`.
    Bypass: admin/superadmin (via _ROLE_BYPASS) e feature flag
    `plan_enforcement` desativada.

    Retorna 403 com payload estruturado para o frontend exibir
    banner de upgrade:
        {
            "error": "...",
            "plan_required": "premium",
            "upgrade_url": "/planos",
            "permite_gestao_clinica": false
        }
    """
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

        # Admin/superadmin bypass (padrão dos outros decorators)
        if profissional.role in ("admin", "superadmin"):
            return f(*args, **kwargs)

        # Verifica feature flag no plano
        permite = bool(plano and getattr(plano, "permite_gestao_clinica", False))

        if not permite:
            logger.info(
                "clinica_management_blocked profissional_id=%s plano=%s",
                profissional_id,
                plano.slug if plano else None,
            )
            return (
                jsonify(
                    {
                        "error": "Gestão da Clínica disponível nos planos Premium e Enterprise",
                        "message": "Faça upgrade do seu plano para acessar a Gestão da Clínica.",
                        "plan_required": "premium",
                        "upgrade_url": "/planos",
                        "permite_gestao_clinica": False,
                    }
                ),
                403,
            )

        return f(*args, **kwargs)

    return decorated_function
