"""
AraOS Platform — Tenant Provider (Concrete Implementation).

Implementação concreta do contrato TenantProvider.
Conecta o contrato abstrato com o serviço de domínio.
"""

from typing import Optional, Dict, Any

from araos.platform.contracts.tenant import TenantProvider as TenantProviderContract
from araos.platform.contracts.tenant import TenantSettingsProvider as TenantSettingsProviderContract
from araos.platform.contracts.tenant import TenantResolverInput
from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import TenantNotFoundError, TenantResolutionError

from .service import TenantService
from .resolver import TenantContextResolver, ResolverInput


class PlatformTenantProvider(TenantProviderContract):
    """
    Implementação concreta de TenantProvider.
    
    Usa TenantService para operações de banco e TenantContextResolver
    para resolução de requests.
    """
    
    def __init__(self, db_session, identity_client=None):
        self.service = TenantService(db_session)
        self.resolver = TenantContextResolver(
            identity_client=identity_client,
            db_session=db_session,
        )
    
    async def get_by_id(self, tenant_id: str) -> TenantContext:
        """Retorna TenantContext pelo ID da organização."""
        org = self.service.get_organization(tenant_id)
        if not org:
            raise TenantNotFoundError(tenant_id)
        
        return self.service.build_tenant_context(tenant_id)
    
    async def get_by_slug(self, slug: str) -> TenantContext:
        """Retorna TenantContext pelo slug."""
        org = self.service.get_organization_by_slug(slug)
        if not org:
            raise TenantNotFoundError(f"slug:{slug}")
        
        return self.service.build_tenant_context(org.id)
    
    async def get_by_user(self, user_id: str) -> TenantContext:
        """Retorna TenantContext do usuário."""
        user = self.service.get_user(user_id)
        if not user:
            raise TenantNotFoundError(f"user:{user_id}")
        
        return self.service.build_tenant_context(
            user.organization_id,
            user_id=user_id,
        )
    
    async def resolve(self, resolver_input: TenantResolverInput) -> TenantContext:
        """
        Resolve tenant a partir de múltiplas fontes.
        
        Converte TenantResolverInput (contrato) para ResolverInput (interno).
        """
        # Converter input do contrato para input interno
        internal_input = ResolverInput(
            authorization_header=resolver_input.header_api_key,  # JWT pode vir aqui também
            api_key_header=resolver_input.header_api_key,
            tenant_id_header=resolver_input.header_tenant_id,
            service_account_header=None,
            jwt_cookie=None,
            query_params={
                "tenant_id": resolver_input.query_tenant_id
            } if resolver_input.query_tenant_id else {},
            ip_address=resolver_input.ip_address,
            user_agent=resolver_input.user_agent,
        )
        
        return await self.resolver.resolve(internal_input)
    
    async def exists(self, tenant_id: str) -> bool:
        """Verifica se tenant existe."""
        org = self.service.get_organization(tenant_id)
        return org is not None
    
    async def is_active(self, tenant_id: str) -> bool:
        """Verifica se tenant está ativo."""
        org = self.service.get_organization(tenant_id)
        return org is not None and org.is_active()


class PlatformTenantSettingsProvider(TenantSettingsProviderContract):
    """
    Implementação concreta de TenantSettingsProvider.
    """
    
    def __init__(self, db_session):
        self.service = TenantService(db_session)
    
    async def get_settings(self, tenant_id: str) -> Dict[str, Any]:
        """Retorna todas as settings do tenant."""
        org = self.service.get_organization(tenant_id)
        if not org:
            raise TenantNotFoundError(tenant_id)
        return org.settings or {}
    
    async def get_feature_flags(self, tenant_id: str) -> Dict[str, bool]:
        """Retorna feature flags ativas do tenant."""
        flags = self.service.get_feature_flags(tenant_id)
        return {f.key: f.enabled for f in flags}
    
    async def get_feature_flag(self, tenant_id: str, flag: str) -> bool:
        """Retorna valor de uma feature flag específica."""
        return self.service.is_feature_enabled(tenant_id, flag)
    
    async def update_settings(self, tenant_id: str,
                               settings: Dict[str, Any]) -> None:
        """Atualiza settings do tenant."""
        org = self.service.get_organization(tenant_id)
        if not org:
            raise TenantNotFoundError(tenant_id)
        
        current = org.settings or {}
        current.update(settings)
        org.settings = current
        # Commit feito pelo service
    
    async def get_branding(self, tenant_id: str) -> Dict[str, Any]:
        """Retorna configurações de branding."""
        org = self.service.get_organization(tenant_id)
        if not org:
            raise TenantNotFoundError(tenant_id)
        
        return {
            "primary_color": org.primary_color,
            "logo_url": org.logo_url,
            "favicon_url": org.favicon_url,
            "name": org.name,
        }
