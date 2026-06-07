"""
AraOS Platform — Tenant Layer.

Módulo de infraestrutura de multi-tenancy.
Não é um CRUD de organizações — é a base da plataforma.
"""

from .models import (
    Organization,
    Clinic,
    Professional,
    User,
    ServiceAccount,
    FeatureFlag,
    Base,
)
from .resolver import TenantContextResolver, ResolverInput
from .middleware import (
    FlaskTenantMiddleware,
    FastAPITenantMiddleware,
    require_tenant,
    require_feature_flag,
    require_roles,
)
from .service import TenantService
from .provider import PlatformTenantProvider, PlatformTenantSettingsProvider

__all__ = [
    "Base",
    "Organization",
    "Clinic",
    "Professional",
    "User",
    "ServiceAccount",
    "FeatureFlag",
    "TenantContextResolver",
    "ResolverInput",
    "FlaskTenantMiddleware",
    "FastAPITenantMiddleware",
    "require_tenant",
    "require_feature_flag",
    "require_roles",
    "TenantService",
    "PlatformTenantProvider",
    "PlatformTenantSettingsProvider",
]
