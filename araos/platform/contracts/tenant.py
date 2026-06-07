"""
AraOS Platform — Tenant Provider Contract.

Interface abstrata para todos os serviços de multi-tenant.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from araos.platform.shared.context import TenantContext
from araos.platform.shared.types import TenantID, OrganizationID, ClinicID, UserID


class TenantProvider(ABC):
    """
    Contrato para resolução e consulta de tenants.
    
    Implementações:
        - TenantService (concreto): consulta ao PostgreSQL
        - TenantResolver (concreto): resolução de request → TenantContext
        - CachedTenantProvider (decorator): cache em Redis
    """
    
    @abstractmethod
    async def get_by_id(self, tenant_id: TenantID) -> TenantContext:
        """
        Retorna TenantContext pelo ID.
        
        Raises:
            TenantNotFoundError: se tenant não existir
        """
        ...
    
    @abstractmethod
    async def get_by_slug(self, slug: str) -> TenantContext:
        """
        Retorna TenantContext pelo slug (subdomain).
        """
        ...
    
    @abstractmethod
    async def get_by_user(self, user_id: UserID) -> TenantContext:
        """
        Retorna TenantContext do usuário.
        """
        ...
    
    @abstractmethod
    async def resolve(self, resolver_input: "TenantResolverInput") -> TenantContext:
        """
        Resolve tenant a partir de múltiplas fontes (header, JWT, subdomain, etc.).
        """
        ...
    
    @abstractmethod
    async def exists(self, tenant_id: TenantID) -> bool:
        """Verifica se tenant existe."""
        ...
    
    @abstractmethod
    async def is_active(self, tenant_id: TenantID) -> bool:
        """Verifica se tenant está ativo."""
        ...


class TenantSettingsProvider(ABC):
    """
    Contrato para consulta e atualização de settings de tenant.
    """
    
    @abstractmethod
    async def get_settings(self, tenant_id: TenantID) -> Dict[str, Any]:
        """Retorna todas as settings do tenant."""
        ...
    
    @abstractmethod
    async def get_feature_flags(self, tenant_id: TenantID) -> Dict[str, bool]:
        """Retorna feature flags ativas do tenant."""
        ...
    
    @abstractmethod
    async def get_feature_flag(self, tenant_id: TenantID, flag: str) -> bool:
        """Retorna valor de uma feature flag específica."""
        ...
    
    @abstractmethod
    async def update_settings(self, tenant_id: TenantID,
                               settings: Dict[str, Any]) -> None:
        """Atualiza settings do tenant."""
        ...
    
    @abstractmethod
    async def get_branding(self, tenant_id: TenantID) -> Dict[str, Any]:
        """Retorna configurações de branding."""
        ...


class TenantResolverInput:
    """
    Input para o TenantResolver.
    Encapsula todas as fontes possíveis de identificação de tenant.
    """
    header_tenant_id: Optional[str] = None
    header_api_key: Optional[str] = None
    jwt_org_id: Optional[str] = None
    subdomain: Optional[str] = None
    query_tenant_id: Optional[str] = None
    path_tenant_id: Optional[str] = None
    
    # Contexto HTTP
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
