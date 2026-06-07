"""
AraOS Platform API — Agents.

Contrato para endpoints administrativos de agentes.

Endpoints:
    GET    /platform/agents
    GET    /platform/agents/{agent_id}
    POST   /platform/agents/{agent_id}/execute
    GET    /platform/agents/{agent_id}/memory
    DELETE /platform/agents/{agent_id}/memory
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class AgentAPI(ABC):
    """Contrato para API administrativa de agentes."""
    
    @abstractmethod
    async def list_agents(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Lista agentes disponíveis para o tenant."""
        ...
    
    @abstractmethod
    async def get_agent(self, tenant_id: str, agent_id: str) -> Dict[str, Any]:
        """Retorna detalhes de um agente."""
        ...
    
    @abstractmethod
    async def execute_agent(
        self,
        tenant_id: str,
        agent_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Executa agente com input."""
        ...
    
    @abstractmethod
    async def get_agent_memory(self, tenant_id: str, agent_id: str) -> Dict[str, Any]:
        """Retorna memória operacional do agente."""
        ...
    
    @abstractmethod
    async def clear_agent_memory(self, tenant_id: str, agent_id: str) -> bool:
        """Limpa memória operacional do agente."""
        ...
