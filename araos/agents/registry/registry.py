"""
AraOS Agents — Registry.

Registro central de agentes.

Cada agente possui:
    - id
    - name
    - version
    - permissions
    - capabilities
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean

from araos.platform.tenant.models import Base


def now_utc():
    from datetime import timezone
    return datetime.now(timezone.utc)


@dataclass
class AgentDefinition:
    """Definição de um agente."""
    agent_id: str
    name: str
    version: str
    capabilities: List[str]
    required_permissions: List[str]
    description: str = ""
    author: str = "araos"
    active: bool = True
    configuration: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "required_permissions": self.required_permissions,
            "description": self.description,
            "author": self.author,
            "active": self.active,
            "configuration": self.configuration,
        }


class AgentRegistration(Base):
    """Registro persistido de agente."""
    __tablename__ = "araos_agent_registry"
    
    agent_id = Column(String(100), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(100), nullable=True)
    
    capabilities = Column(JSON, nullable=False, default=list)
    required_permissions = Column(JSON, nullable=False, default=list)
    
    active = Column(Boolean, nullable=False, default=True)
    configuration = Column(JSON, nullable=True, default=dict)
    
    registered_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class AgentRegistry:
    """
    Registro de agentes.
    
    Responsabilidades:
        - Registrar agentes
        - Descobrir agentes por capability
        - Validar agentes
        - Listar agentes ativos
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._definitions: Dict[str, AgentDefinition] = {}
    
    def register(self, agent) -> None:
        """
        Registra agente.
        
        Aceita BaseAgent ou AgentDefinition.
        """
        from ..runtime.agent import BaseAgent
        
        if isinstance(agent, BaseAgent):
            definition = AgentDefinition(
                agent_id=agent.agent_id,
                name=agent.name,
                version=agent.version,
                capabilities=[c.value for c in agent.capabilities],
                required_permissions=agent.required_permissions,
                description=agent.description,
                author=agent.author,
            )
        else:
            definition = agent
        
        self._definitions[definition.agent_id] = definition
    
    def unregister(self, agent_id: str) -> None:
        """Remove agente do registro."""
        self._definitions.pop(agent_id, None)
    
    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Retorna definição do agente."""
        return self._definitions.get(agent_id)
    
    def list_all(self) -> List[AgentDefinition]:
        """Lista todos os agentes registrados."""
        return list(self._definitions.values())
    
    def find_by_capability(self, capability: str) -> List[AgentDefinition]:
        """Encontra agentes por capability."""
        return [
            d for d in self._definitions.values()
            if capability in d.capabilities
        ]
    
    def find_by_permission(self, permission: str) -> List[AgentDefinition]:
        """Encontra agentes que requerem uma permissão."""
        return [
            d for d in self._definitions.values()
            if permission in d.required_permissions
        ]
    
    def get_system_agents(self) -> List[AgentDefinition]:
        """Retorna definições dos agentes do sistema."""
        return [
            AgentDefinition(
                agent_id="voice_copilot",
                name="AraOS Voice Copilot",
                version="1.0.0",
                capabilities=["voice", "clinical_summary"],
                required_permissions=["voice.use", "patient.read", "consultation.read"],
                description="Assistente de voz para consultas",
            ),
            AgentDefinition(
                agent_id="concierge",
                name="AraOS Concierge",
                version="1.0.0",
                capabilities=["chat", "scheduling", "notification"],
                required_permissions=["communication.send", "patient.read", "consultation.schedule"],
                description="Atendimento virtual multicanal",
            ),
            AgentDefinition(
                agent_id="intake",
                name="AraOS Intake Agent",
                version="1.0.0",
                capabilities=["chat", "document_processing", "intake"],
                required_permissions=["patient.read", "patient.write", "document.upload"],
                description="Coleta de informações do paciente",
            ),
            AgentDefinition(
                agent_id="followup",
                name="AraOS Follow-up Agent",
                version="1.0.0",
                capabilities=["chat", "notification", "follow_up"],
                required_permissions=["communication.send", "patient.read", "consultation.read"],
                description="Acompanhamento pós-consulta",
            ),
            AgentDefinition(
                agent_id="specialty_agent",
                name="AraOS Specialty Agent",
                version="1.0.0",
                capabilities=["decision_support", "clinical_summary"],
                required_permissions=["patient.read", "evolution.read", "diagnosis.read"],
                description="Suporte especializado (preparação)",
            ),
        ]
    
    def register_system_agents(self) -> None:
        """Registra agentes padrão do sistema."""
        for agent in self.get_system_agents():
            self.register(agent)
