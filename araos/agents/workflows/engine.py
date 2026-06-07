"""
AraOS Agents — Workflow Engine.

Orquestração de workflows distribuídos.

Exemplo:
    WhatsApp
    ↓
    Concierge
    ↓
    Digital Twin
    ↓
    Consulta

Não implementa IA.
Apenas infraestrutura de orquestração.
"""

import uuid
from typing import List, Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum

from ..runtime.context import AgentContext


class StepStatus(str, Enum):
    """Status de um passo do workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Passo de um workflow."""
    step_id: str
    name: str
    agent_id: Optional[str] = None  # None = passo manual/sistema
    action: str = ""  # nome da ação a executar
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    condition: Optional[str] = None  # expressão simples (futuro)
    depends_on: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class WorkflowResult:
    """Resultado de um workflow."""
    workflow_id: str
    success: bool
    steps: List[WorkflowStep]
    output: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    error: Optional[str] = None


class WorkflowEngine:
    """
    Engine de workflows.
    
    Responsabilidades:
        - Definir workflows como DAGs de passos
        - Executar passos em ordem
        - Gerenciar estado entre passos
        - Emitir eventos de progresso
        - Suportar retry e fallback
    
    Uso:
        engine = WorkflowEngine(runtime)
        
        workflow = engine.define("intake_to_consultation", [
            WorkflowStep("1", "receive_message", agent_id="concierge", action="receive"),
            WorkflowStep("2", "load_patient", agent_id="intake", action="load_twin"),
            WorkflowStep("3", "schedule", agent_id="concierge", action="schedule"),
        ])
        
        result = await engine.execute(workflow_id, context)
    """
    
    def __init__(self, runtime=None, event_bus=None):
        self.runtime = runtime
        self.event_bus = event_bus
        self._workflows: Dict[str, List[WorkflowStep]] = {}
    
    def define(self, workflow_id: str, steps: List[WorkflowStep]) -> str:
        """Define um workflow."""
        self._workflows[workflow_id] = steps
        return workflow_id
    
    async def execute(
        self,
        workflow_id: str,
        context: AgentContext,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Executa workflow.
        
        Args:
            workflow_id: ID do workflow definido
            context: Contexto do agente
            input_data: Dados iniciais
        
        Returns:
            WorkflowResult
        """
        steps = self._workflows.get(workflow_id, [])
        if not steps:
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                steps=[],
                error="WORKFLOW_NOT_FOUND",
            )
        
        execution_id = str(uuid.uuid4())
        correlation_id = context.correlation_id or str(uuid.uuid4())
        
        # Inicializar estado
        state = dict(input_data or {})
        executed_steps: List[WorkflowStep] = []
        
        await self._emit_event(
            "AGENT_STARTED",  # Reutilizamos AGENT_STARTED para início de workflow
            context,
            {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "correlation_id": correlation_id,
            },
        )
        
        try:
            for step in steps:
                # Verificar dependências
                if step.depends_on:
                    pending = [
                        s.step_id for s in executed_steps
                        if s.step_id in step.depends_on and s.status != StepStatus.COMPLETED
                    ]
                    if pending:
                        step.status = StepStatus.SKIPPED
                        step.error = f"Dependencies not met: {pending}"
                        executed_steps.append(step)
                        continue
                
                step.status = StepStatus.RUNNING
                step.started_at = __import__('datetime').datetime.utcnow().isoformat()
                
                # Executar passo
                if step.agent_id and self.runtime:
                    step_context = self._build_step_context(context, step, state)
                    result = await self.runtime.execute(step.agent_id, step_context)
                    
                    if result.success:
                        step.status = StepStatus.COMPLETED
                        step.result = result.output
                        # Mapear outputs para estado
                        for key, state_key in step.output_mapping.items():
                            state[state_key] = result.output.get(key)
                    else:
                        step.status = StepStatus.FAILED
                        step.error = result.error
                        
                        await self._emit_event(
                            "AGENT_FAILED",
                            context,
                            {
                                "workflow_id": workflow_id,
                                "step_id": step.step_id,
                                "error": result.error,
                            },
                        )
                        
                        return WorkflowResult(
                            workflow_id=workflow_id,
                            success=False,
                            steps=executed_steps + [step],
                            output=state,
                            correlation_id=correlation_id,
                            error=f"Step {step.step_id} failed: {result.error}",
                        )
                else:
                    # Passo de sistema — simplesmente marca como completo
                    step.status = StepStatus.COMPLETED
                    step.result = {"status": "system_step"}
                
                step.completed_at = __import__('datetime').datetime.utcnow().isoformat()
                executed_steps.append(step)
                
                await self._emit_event(
                    "AGENT_ACTION_EXECUTED",
                    context,
                    {
                        "workflow_id": workflow_id,
                        "step_id": step.step_id,
                        "agent_id": step.agent_id,
                    },
                )
            
            await self._emit_event(
                "AGENT_COMPLETED",
                context,
                {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "steps_completed": len(executed_steps),
                },
            )
            
            return WorkflowResult(
                workflow_id=workflow_id,
                success=True,
                steps=executed_steps,
                output=state,
                correlation_id=correlation_id,
            )
            
        except Exception as e:
            await self._emit_event(
                "AGENT_FAILED",
                context,
                {
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "error": str(e),
                },
            )
            return WorkflowResult(
                workflow_id=workflow_id,
                success=False,
                steps=executed_steps,
                output=state,
                correlation_id=correlation_id,
                error=str(e),
            )
    
    def _build_step_context(
        self,
        context: AgentContext,
        step: WorkflowStep,
        state: Dict[str, Any],
    ) -> AgentContext:
        """Constrói contexto específico do passo."""
        from dataclasses import replace
        
        # Mapear inputs do estado
        step_input = {}
        for key, state_key in step.input_mapping.items():
            step_input[key] = state.get(state_key)
        
        new_context = replace(
            context,
            input_data=step_input,
            metadata={
                **context.metadata,
                "step_id": step.step_id,
                "workflow": True,
            },
        )
        return new_context
    
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
