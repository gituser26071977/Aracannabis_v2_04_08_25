"""
AraOS Platform — Feature Flag Service Contract.

Interface para resolução de feature flags com múltiplos scopes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from araos.platform.shared.context import TenantContext
from araos.platform.shared.types import TenantID


@dataclass
class FeatureFlagContext:
    """Contexto para avaliação de feature flags."""
    tenant_id: TenantID
    user_id: Optional[str] = None
    user_roles: List[str] = None
    plan: str = "free"
    environment: str = "production"
    device_type: Optional[str] = None  # web, mobile, tablet
    beta_group: Optional[str] = None
    
    def __post_init__(self):
        if self.user_roles is None:
            self.user_roles = []


class FeatureFlagService(ABC):
    """
    Contrato para resolução de feature flags.
    
    Scopes de avaliação (em ordem de prioridade):
        1. Override por usuário
        2. Override por tenant
        3. Plano de assinatura
        4. Grupo beta
        5. Ambiente (dev/staging/prod)
        6. Default global
    
    Implementações:
        - DatabaseFeatureFlagService (concreto): PostgreSQL
        - LaunchDarklyAdapter (futuro): integração externa
    """
    
    @abstractmethod
    async def is_enabled(self, flag_name: str,
                         context: FeatureFlagContext) -> bool:
        """
        Verifica se uma feature está habilitada.
        
        Args:
            flag_name: Nome da feature flag
            context: Contexto de avaliação
        
        Returns:
            True se feature está habilitada
        """
        ...
    
    @abstractmethod
    async def get_all(self, context: FeatureFlagContext) -> Dict[str, bool]:
        """
        Retorna estado de todas as features para o contexto.
        
        Returns:
            Dict {flag_name: is_enabled}
        """
        ...
    
    @abstractmethod
    async def get_enabled_features(self, context: FeatureFlagContext) -> List[str]:
        """
        Retorna lista de features habilitadas.
        """
        ...
    
    @abstractmethod
    async def get_variation(self, flag_name: str,
                            context: FeatureFlagContext,
                            default: Any = None) -> Any:
        """
        Retorna valor de uma feature flag multivariada.
        
        Útil para:
            - Percentual de rollout (ex: 10% dos usuários)
            - Configuração A/B (ex: cor do botão)
            - Limite dinâmico (ex: max_upload_size)
        """
        ...
    
    @abstractmethod
    async def register(self, flag_name: str,
                       default: bool = False,
                       description: str = "") -> None:
        """
        Registra nova feature flag no sistema.
        """
        ...
    
    @abstractmethod
    async def set_tenant_override(self, tenant_id: TenantID,
                                   flag_name: str,
                                   value: bool) -> None:
        """
        Define override para um tenant específico.
        """
        ...
    
    @abstractmethod
    async def set_user_override(self, tenant_id: TenantID,
                                 user_id: str,
                                 flag_name: str,
                                 value: bool) -> None:
        """
        Define override para um usuário específico.
        """
        ...
