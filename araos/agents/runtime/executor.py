"""
AraOS Agents — Agent Executor.

Executa agentes com:
    - Validação de permissões
    - Emissão de eventos
    - Registro de memória
    - Tratamento de erros
    - Audit automático
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from .agent import BaseAgent, AgentResult
from .context import AgentContext
from .memory import MemoryStore, AgentMemory


class AgentExecutor:
    """
    Executor de agentes.
    
    Responsabilidades:
        - Validar permissões antes de executar
        - Emitir eventos AGENT_STARTED, AGENT_COMPLETED, AGENT_FAILED
        - Atualizar memória operacional
        - Registrar auditoria
    
    Uso:
        executor = AgentExecutor(event_bus, memory_store, audit_service)
        result = await executor.run(agent, context)
    """
    
    def __init__(
        self,
        event_bus=None,
        memory_store: Optional[MemoryStore] = None,
        audit_service=None,
    ):
        self.event_bus = event_bus
        self.memory_store = memory_store
        self.audit_service = audit_service
    
    async def run(
        self,
        agent: BaseAgent,
        context: AgentContext,
    ) -> AgentResult:
        """
        Executa agente com todo o plumbing.
        
        Fluxo:
            1. Validar permissões
            2. Carregar memória
            3. Emitir AGENT_STARTED
            4. Executar agente
            5. Emitir AGENT_COMPLETED ou AGENT_FAILED
            6. Persistir memória
            7. Registrar ações no audit
        """
        # 1. Validar permissões
        if not agent.validate_permissions(context.identity_context):
            return AgentResult(
                success=False,
                message=f"Agent {agent.agent_id} lacks required permissions",
                error="PERMISSION_DENIED",
            )
        
        # 2. Carregar memória
        memory = None
        if self.memory_store:
            memory = self.memory_store.load(agent.agent_id, context.tenant_id)
        
        # 3. Emitir AGENT_STARTED
        await self._emit_event(
            "AGENT_STARTED",
            context,
            {"agent_id": agent.agent_id, "version": agent.version},
        )
        
        try:
            # 4. Executar agente
            agent._status = "running"
            result = await agent.execute(context)
            agent._status = "idle" if result.success else "failed"
            
            # 5. Emitir evento de conclusão
            if result.success:
                await self._emit_event(
                    "AGENT_COMPLETED",
                    context,
                    {
                        "agent_id": agent.agent_id,
                        "actions": len(result.actions_executed),
                        "events": len(result.events_generated),
                    },
                )
                
                # Emitir AGENT_ACTION_EXECUTED para cada ação
                for action in result.actions_executed:
                    await self._emit_event(
                        "AGENT_ACTION_EXECUTED",
                        context,
                        {
                            "agent_id": agent.agent_id,
                            "action": action,
                        },
                    )
            else:
                await self._emit_event(
                    "AGENT_FAILED",
                    context,
                    {
                        "agent_id": agent.agent_id,
                        "error": result.error,
                        "message": result.message,
                    },
                )
            
            # 6. Persistir memória
            if memory and self.memory_store:
                memory.record_execution(
                    event_id=context.correlation_id,
                    patient_id=context.patient_id,
                    state_update={"last_result": result.success},
                )
                self.memory_store.save(memory)
            
            return result
            
        except Exception as e:
            agent._status = "failed"
            await self._emit_event(
                "AGENT_FAILED",
                context,
                {
                    "agent_id": agent.agent_id,
                    "error": "EXCEPTION",
                    "message": str(e),
                },
            )
            return AgentResult(
                success=False,
                message=f"Agent execution failed: {str(e)}",
                error="EXCEPTION",
            )
    
    async def _emit_event(
        self,
        event_type: str,
        context: AgentContext,
        payload: Dict[str, Any],
    ) -> None:
        """Emite evento no Event Bus."""
        if not self.event_bus:
            return
        
        from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
        
        event = EventEnvelopeV2(
            event_type=event_type,
            tenant_id=context.tenant_id,
            payload=payload,
            event_category=EventCategory.OPERATIONAL,
            actor_id=context.actor_id,
            actor_type=context.identity_context.actor_type.value,
        )
        
        if context.correlation:
            event.correlation_id = context.correlation.correlation_id
            event.causation_id = context.correlation.causation_id
        
        await self.event_bus.publish(event)
