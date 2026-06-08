"""
AraOS Specialty Framework — Specialty Agent.

Agente especializado integrado ao Agent Runtime.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from araos.agents.runtime.agent import BaseAgent, AgentCapability, AgentResult
from araos.agents.runtime.context import AgentContext

from .definitions import SpecialtyDefinition


class SpecialtyAgent(BaseAgent, ABC):
    """
    Agente especializado base.

    Todo agente de especialidade deve herdar desta classe.
    Integra com o Agent Runtime da plataforma.

    Exemplos futuros:
        - CannabisAgent
        - NutrologyAgent
        - PsychiatryAgent

    Uso:
        class CannabisAgent(SpecialtyAgent):
            @property
            def specialty_code(self) -> str:
                return "cannabis"

            async def execute(self, context: AgentContext) -> AgentResult:
                # Lógica específica
                ...
    """

    @property
    @abstractmethod
    def specialty_code(self) -> str:
        """Código da especialidade."""
        ...

    def get_specialty_capabilities(self) -> List[AgentCapability]:
        """Capacidades adicionais do agente especializado."""
        return [
            AgentCapability.CLINICAL_SUMMARY,
            AgentCapability.DECISION_SUPPORT,
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Executa o agente especializado.

        Subclasses devem sobrescrever para implementar lógica específica.
        """
        return AgentResult(
            success=True,
            output={
                "specialty_code": self.specialty_code,
                "agent_id": self.agent_id,
                "message": f"Specialty agent {self.specialty_code} executed",
            },
        )

    def get_specialty_context(self, context: AgentContext) -> Dict[str, Any]:
        """
        Extrai contexto especializado do AgentContext.

        Returns:
            Dicionário com dados relevantes à especialidade.
        """
        result: Dict[str, Any] = {
            "specialty_code": self.specialty_code,
            "patient_id": getattr(context, "patient_id", None),
            "tenant_id": getattr(context, "tenant_id", None),
        }

        # Extrair twin se disponível
        twin = getattr(context, "patient_twin", None)
        if twin:
            result["twin"] = {
                "patient_id": twin.patient_id,
                "has_profile": twin.profile is not None,
            }

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o agente."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialty_code": self.specialty_code,
            "capabilities": [c.value for c in self.capabilities],
        }
