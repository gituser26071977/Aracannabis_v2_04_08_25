"""
AraOS Platform — Feature Flag Provider Contract.

Contrato canônico para resolução e gestão de feature flags.
TODAS as implementações devem satisfazer este contrato.

Implementações futuras:
    - PostgresFeatureFlagProvider (concreto): PostgreSQL
    - RedisFeatureFlagProvider (concreto): Redis
    - LaunchDarklyProvider (adapter): LaunchDarkly
    - ConfigCatProvider (adapter): ConfigCat
    - InMemoryFeatureFlagProvider (teste): para testes
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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


@dataclass
class FeatureFlagState:
    """Estado de uma feature flag."""
    key: str
    enabled: bool
    description: str = ""
    scope: str = "global"  # global | tenant | user | plan | environment
    target: Optional[str] = None  # valor alvo do scope
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FeatureFlagProvider(ABC):
    """
    Contrato canônico para feature flags.
    
    Responsabilidades:
        - is_enabled(): verificar se flag está habilitada
        - enable(): habilitar flag
        - disable(): desabilitar flag
        - get_flags(): listar todas as flags
        - get_context_flags(): listar flags para contexto específico
    
    Todos os métodos são async para suportar I/O (DB, Redis, API externa).
    """
    
    @abstractmethod
    async def is_enabled(self, flag_key: str,
                         context: FeatureFlagContext) -> bool:
        """
        Verifica se uma feature flag está habilitada para o contexto.
        
        Resolução (ordem de precedência):
            1. Override por usuário
            2. Override por tenant
            3. Plano de assinatura
            4. Grupo beta
            5. Ambiente
            6. Default global
        
        Args:
            flag_key: Chave da feature flag (ex: "VOICE_ENABLED")
            context: Contexto de avaliação
        
        Returns:
            True se a feature está habilitada para o contexto
        """
        ...
    
    @abstractmethod
    async def enable(self, flag_key: str,
                     scope: str = "global",
                     target: Optional[str] = None) -> None:
        """
        Habilita uma feature flag.
        
        Args:
            flag_key: Chave da feature flag
            scope: Escopo da habilitação (global, tenant, user, plan, environment)
            target: Alvo do escopo (ex: tenant_id, user_id, plan_name)
        """
        ...
    
    @abstractmethod
    async def disable(self, flag_key: str,
                      scope: str = "global",
                      target: Optional[str] = None) -> None:
        """
        Desabilita uma feature flag.
        
        Args:
            flag_key: Chave da feature flag
            scope: Escopo da desabilitação
            target: Alvo do escopo
        """
        ...
    
    @abstractmethod
    async def get_flags(self) -> List[FeatureFlagState]:
        """
        Retorna todas as feature flags registradas.
        
        Returns:
            Lista de FeatureFlagState
        """
        ...
    
    @abstractmethod
    async def get_context_flags(self,
                                context: FeatureFlagContext) -> Dict[str, bool]:
        """
        Retorna estado de todas as flags para um contexto específico.
        
        Returns:
            Dict {flag_key: is_enabled}
        """
        ...
    
    @abstractmethod
    async def register(self, flag_key: str,
                       default: bool = False,
                       description: str = "",
                       scope: str = "global") -> None:
        """
        Registra uma nova feature flag no sistema.
        
        Args:
            flag_key: Chave única da flag
            default: Valor padrão
            description: Descrição da flag
            scope: Escopo padrão
        """
        ...
    
    @abstractmethod
    async def get_flag(self, flag_key: str) -> Optional[FeatureFlagState]:
        """
        Retorna estado de uma flag específica.
        
        Returns:
            FeatureFlagState ou None se não encontrada
        """
        ...
