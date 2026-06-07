"""
AraOS Platform — Identity Client Contract.

Cliente simplificado para consumidores que precisam apenas
validar tokens e verificar permissões.

Para operações completas (login, registro, etc), use IdentityProvider.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from araos.platform.shared.context import TenantContext
from araos.platform.shared.types import UserID, TenantID


class IdentityClient(ABC):
    """
    Cliente de identidade para consumidores.
    
    Operações:
        - validate_token: valida JWT e retorna contexto
        - check_permission: verifica permissão
        - get_user_context: retorna TenantContext completo
    
    Implementações:
        - JWTIdentityClient (concreto): validação local de JWT
        - RemoteIdentityClient (concreto): chamada HTTP ao Identity Service
    """
    
    @abstractmethod
    async def validate_token(self, token: str) -> TenantContext:
        """
        Valida token e retorna contexto do usuário.
        
        Raises:
            TokenExpiredError: se token expirou
            TokenInvalidError: se token é inválido
        """
        ...
    
    @abstractmethod
    async def check_permission(self, token: str,
                                permission: str) -> bool:
        """
        Verifica se usuário tem permissão específica.
        """
        ...
    
    @abstractmethod
    async def get_user_context(self, user_id: UserID) -> TenantContext:
        """
        Retorna contexto completo do usuário.
        """
        ...
    
    @abstractmethod
    async def get_user_roles(self, token: str) -> List[str]:
        """
        Retorna papéis do usuário.
        """
        ...
    
    @abstractmethod
    async def refresh_session(self, token: str) -> str:
        """
        Renova token de acesso.
        
        Returns:
            Novo access token
        """
        ...
