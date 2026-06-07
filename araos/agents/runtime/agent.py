"""
AraOS Agents — Base Agent.

Classe base para todos os agentes do AraOS.
Define o contrato mínimo que todo agente deve implementar.

Agentes atuais:
    - Voice Copilot
    - Concierge
    - Intake Agent
    - Follow-up Agent
    - Specialty Agent

Agentes futuros:
    - Clinical Decision Support
    - Coding/Billing Agent
    - Quality Agent
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .context import AgentContext


class AgentCapability(str, Enum):
    """Capacidades que um agente pode ter."""
    VOICE = "voice"
    TEXT = "text"
    CHAT = "chat"
    SCHEDULING = "scheduling"
    DOCUMENT_PROCESSING = "document_processing"
    CLINICAL_SUMMARY = "clinical_summary"
    FOLLOW_UP = "follow_up"
    INTAKE = "intake"
    NOTIFICATION = "notification"
    DECISION_SUPPORT = "decision_support"


@dataclass
class AgentResult:
    """Resultado da execução de um agente."""
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    events_generated: List[Dict[str, Any]] = field(default_factory=list)
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None


class BaseAgent(ABC):
    """
    Classe base para todos os agentes AraOS.
    
    Todo agente deve:
        1. Ter um ID único
        2. Declarar suas capabilities
        3. Declarar permissões necessárias
        4. Implementar execute()
        5. Emitir eventos via Event Bus
        6. Respeitar IdentityContext
    
    Uso:
        class VoiceAgent(BaseAgent):
            def __init__(self):
                super().__init__(
                    agent_id="voice_copilot",
                    name="AraOS Voice Copilot",
                    version="1.0.0",
                    capabilities=[AgentCapability.VOICE],
                    required_permissions=["voice.use", "patient.read"],
                )
            
            async def execute(self, context: AgentContext) -> AgentResult:
                # Lógica do agente
                ...
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str,
        capabilities: List[AgentCapability],
        required_permissions: List[str],
        description: str = "",
        author: str = "araos",
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.capabilities = capabilities
        self.required_permissions = required_permissions
        self.description = description
        self.author = author
        self._status = "idle"  # idle, running, paused, failed
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Executa o agente.
        
        Args:
            context: Contexto completo de execução
        
        Returns:
            AgentResult com output e metadados
        """
        ...
    
    def validate_permissions(self, identity_context) -> bool:
        """
        Verifica se identidade tem permissões necessárias.
        
        Usa Permission Registry da Identity Platform.
        Nenhum bypass permitido.
        """
        from araos.platform.identity.permissions import PermissionRegistry
        
        for permission in self.required_permissions:
            if not identity_context.has_permission(permission):
                return False
        return True
    
    @property
    def status(self) -> str:
        return self._status
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa metadados do agente."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": [c.value for c in self.capabilities],
            "required_permissions": self.required_permissions,
            "description": self.description,
            "author": self.author,
            "status": self.status,
        }
