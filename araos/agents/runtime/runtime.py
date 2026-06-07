"""
AraOS Agents — Agent Runtime.

Sistema operacional dos agentes.

Responsabilidades:
    - Gerenciar ciclo de vida dos agentes
    - Orquestrar execuções
    - Fornecer contexto padronizado
    - Integrar com Event Bus
"""

from typing import Dict, Any, Optional, Type

from .agent import BaseAgent, AgentResult
from .context import AgentContext
from .executor import AgentExecutor
from ..registry.registry import AgentRegistry


class AgentRuntime:
    """
    Runtime central dos agentes AraOS.
    
    Uso:
        runtime = AgentRuntime(event_bus, memory_store, audit_service)
        runtime.register(VoiceAgent())
        runtime.register(ConciergeAgent())
        
        # Executar agente
        result = await runtime.execute("voice_copilot", context)
    """
    
    def __init__(
        self,
        event_bus=None,
        memory_store=None,
        audit_service=None,
        registry: Optional[AgentRegistry] = None,
    ):
        self.registry = registry or AgentRegistry()
        self.executor = AgentExecutor(
            event_bus=event_bus,
            memory_store=memory_store,
            audit_service=audit_service,
        )
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent) -> None:
        """Registra agente no runtime."""
        self.registry.register(agent)
        self._agents[agent.agent_id] = agent
    
    def unregister(self, agent_id: str) -> None:
        """Remove agente do runtime."""
        self.registry.unregister(agent_id)
        self._agents.pop(agent_id, None)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Retorna agente por ID."""
        return self._agents.get(agent_id)
    
    async def execute(
        self,
        agent_id: str,
        context: AgentContext,
    ) -> AgentResult:
        """
        Executa agente pelo ID.
        
        Args:
            agent_id: ID do agente
            context: Contexto de execução
        
        Returns:
            AgentResult
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return AgentResult(
                success=False,
                message=f"Agent {agent_id} not found",
                error="AGENT_NOT_FOUND",
            )
        
        return await self.executor.run(agent, context)
    
    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """Lista agentes registrados."""
        return {
            agent_id: agent.to_dict()
            for agent_id, agent in self._agents.items()
        }
    
    def get_capabilities(self) -> Dict[str, list]:
        """Retorna capabilities de todos os agentes."""
        return {
            agent_id: [c.value for c in agent.capabilities]
            for agent_id, agent in self._agents.items()
        }
