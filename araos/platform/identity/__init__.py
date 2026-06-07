"""
AraOS Platform — Identity Platform.

Sistema único de identidade para toda a plataforma.
Suporta: usuários humanos, profissionais, admins, service accounts, agentes de IA.

Nenhum módulo deve possuir autenticação própria.
Toda identidade passa por aqui.
"""

from .permissions import Permission, PermissionRegistry, Role, RoleRegistry
from .tokens import JWTTokenProvider, TokenClaims, PlatformTokenPair
from .context import IdentityContext, ActorType
from .service_accounts import ServiceAccountAuthenticator, APIKeyCredentials
from .delegated import DelegatedIdentity, DelegationContext
from .service import IdentityService

__all__ = [
    "Permission",
    "PermissionRegistry",
    "Role",
    "RoleRegistry",
    "JWTTokenProvider",
    "TokenClaims",
    "PlatformTokenPair",
    "IdentityContext",
    "ActorType",
    "ServiceAccountAuthenticator",
    "APIKeyCredentials",
    "DelegatedIdentity",
    "DelegationContext",
    "IdentityService",
]
