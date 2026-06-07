"""
AraOS Platform API — Context.

Contrato para endpoints de contexto da plataforma.

Endpoints:
    GET /platform/context/tenant
    GET /platform/context/identity
    GET /platform/context/session
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class ContextAPI(ABC):
    """Contrato para API de contexto."""
    
    @abstractmethod
    async def get_tenant_context(self, tenant_id: str) -> Dict[str, Any]:
        """Retorna contexto de tenant."""
        ...
    
    @abstractmethod
    async def get_identity_context(self, token: str) -> Dict[str, Any]:
        """Retorna contexto de identidade a partir de token."""
        ...
    
    @abstractmethod
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retorna contexto de sessão."""
        ...
