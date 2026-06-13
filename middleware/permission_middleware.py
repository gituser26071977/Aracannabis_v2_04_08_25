"""
Middleware de Resolução de Permissões (Squad B — Segurança & Acesso)

Combina as roles do `Profissional` (global) e `UsuarioAssociacao` (per-association)
para produzir um conjunto efetivo de permissões via AraOS RoleRegistry.

Popula em `before_request`:
  - g.user_role          : role GLOBAL do Profissional (já populada pelo TenantMiddleware)
  - g.user_permissions   : FrozenSet[str] de permissões AraOS efetivas
  - g.current_association: Associacao ativa (já populada pelo TenantMiddleware)

Uso:
  - Decorator @require_permission(perm) consulta g.user_permissions
  - Decorator @require_role(*roles) consulta g.user_role
  - Decorator @require_association_member consulta g.current_association
"""
from __future__ import annotations

import logging
from typing import Iterable, Optional

from flask import g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

logger = logging.getLogger(__name__)


# Rotas que não precisam de resolução de permissões (públicas / health / webhooks)
PUBLIC_PATH_PREFIXES = (
    '/api/auth',
    '/api/status',
    '/api/public',
    '/api/webhooks',
    '/api/csrf-token',
    '/static',
)


def _is_public_request(path: str) -> bool:
    if request.method == 'OPTIONS':
        return True
    return any(path.startswith(p) for p in PUBLIC_PATH_PREFIXES)


def _resolve_role_for_user(user_id: int) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve (global_role, association_role) para o usuário atual.
    Importado lazy para evitar import circular.
    """
    from models import Profissional
    from models_extra import UsuarioAssociacao

    profissional = Profissional.query.get(user_id)
    if not profissional:
        return None, None

    # Role global (ex: 'admin', 'profissional', 'secretary', 'manager', 'auxiliar', 'superadmin')
    global_role = getattr(profissional, 'role', None) or 'profissional'

    # Role per-association (vinda do header X-Association-ID)
    assoc_id = request.headers.get('X-Association-ID')
    association_role: Optional[str] = None
    if assoc_id:
        try:
            assoc_id_int = int(assoc_id)
            link = UsuarioAssociacao.query.filter_by(
                profissional_id=user_id,
                associacao_id=assoc_id_int,
                status='active',
            ).first()
            if link:
                association_role = link.role
        except (ValueError, TypeError):
            association_role = None

    # Se não houver header, pega o primeiro vínculo ativo como fallback
    if not association_role:
        link = UsuarioAssociacao.query.filter_by(
            profissional_id=user_id,
            status='active',
        ).first()
        if link:
            association_role = link.role

    return global_role, association_role


def resolve_effective_permissions(global_role: Optional[str], association_role: Optional[str]) -> frozenset:
    """
    Combina permissões das duas roles via AraOS RoleRegistry.

    Mapeamento DB Role -> AraOS Role (Fase 1):
      - admin       -> admin           (acesso total via bypass)
      - superadmin  -> admin           (bypass)
      - profissional -> physician      (médico)
      - secretary   -> secretary       (staff)
      - manager     -> manager         (gestor de clínica)
      - auxiliar    -> secretary       (alias legacy deprecated)
      - patient     -> patient         (portal paciente)
      - viewer      -> viewer          (read-only)

    Regras:
      - admin/superadmin global => todas as permissões (bypass)
      - Caso contrário, resolve cada role individualmente e une os conjuntos
      - Roles desconhecidas são ignoradas silenciosamente
    """
    try:
        from araos.platform.identity.permissions import RoleRegistry
    except Exception as exc:  # pragma: no cover — import defensivo
        logger.warning("AraOS RoleRegistry indisponível: %s", exc)
        return frozenset()

    if not global_role:
        return frozenset()

    # Admin global tem acesso total
    if global_role in ('admin', 'superadmin'):
        try:
            return frozenset(RoleRegistry.get('admin').permissions)
        except Exception:
            return frozenset()

    # Mapeamento DB -> AraOS
    db_to_araos = {
        'profissional': 'physician',
        'secretary': 'secretary',
        'manager': 'manager',
        'auxiliar': 'secretary',  # legacy
        'patient': 'patient',
        'viewer': 'viewer',
    }

    roles_to_resolve = []
    mapped = db_to_araos.get(global_role)
    if mapped:
        roles_to_resolve.append(mapped)
    # Association role pode trazer 'admin'/'secretary'/'manager' já alinhados
    if association_role and association_role not in ('member',):
        mapped_assoc = db_to_araos.get(association_role, association_role)
        if mapped_assoc not in roles_to_resolve:
            roles_to_resolve.append(mapped_assoc)

    return frozenset(RoleRegistry.resolve_permissions(roles_to_resolve))


def register_permission_middleware(app):
    """
    Registra before_request que popula g.user_permissions e (fallback) g.current_association.

    Em produção, o `register_tenant_middleware` é registrado ANTES deste e já popula
    g.user_role e g.current_association. Este middleware é defensivo: se o tenant
    middleware não estiver presente (ex: testes), popula o contexto de associação
    a partir do header X-Association-ID, mantendo a interface consistente.

    Idempotente — pode ser chamado uma única vez.
    """
    @app.before_request
    def populate_user_permissions():
        # Inicializa sempre — evita AttributeError em rotas que não populam
        g.user_permissions = frozenset()
        if not hasattr(g, "current_association"):
            g.current_association = None

        if _is_public_request(request.path):
            return

        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
        except Exception:
            return

        if not identity:
            return

        try:
            user_id = int(identity)
        except (ValueError, TypeError):
            return

        global_role, association_role, assoc_obj = _resolve_role_for_user_full(user_id)
        g.user_permissions = resolve_effective_permissions(global_role, association_role)

        # Fallback: se o tenant_middleware não setou g.current_association, setamos aqui
        if g.current_association is None and assoc_obj is not None:
            g.current_association = assoc_obj

        logger.debug(
            "Resolved perms for user_id=%s global=%s assoc=%s -> %d permissions",
            user_id, global_role, association_role, len(g.user_permissions),
        )


def _resolve_role_for_user_full(user_id: int):
    """
    Resolve (global_role, association_role, association_obj) para o usuário atual.

    Retorna tupla com o objeto Associacao carregado (ou None).
    """
    from models import Profissional
    from models_extra import UsuarioAssociacao
    from association.models import Associacao

    profissional = Profissional.query.get(user_id)
    if not profissional:
        return None, None, None

    global_role = getattr(profissional, 'role', None) or 'profissional'

    assoc_id = request.headers.get('X-Association-ID')
    association_role: Optional[str] = None
    association_obj = None

    if assoc_id:
        try:
            assoc_id_int = int(assoc_id)
            link = UsuarioAssociacao.query.filter_by(
                profissional_id=user_id,
                associacao_id=assoc_id_int,
                status='active',
            ).first()
            if link:
                association_role = link.role
                association_obj = link.associacao
        except (ValueError, TypeError):
            association_role = None

    if not association_role:
        link = UsuarioAssociacao.query.filter_by(
            profissional_id=user_id,
            status='active',
        ).first()
        if link:
            association_role = link.role
            association_obj = link.associacao

    return global_role, association_role, association_obj
