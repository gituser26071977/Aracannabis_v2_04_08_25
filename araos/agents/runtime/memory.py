"""
AraOS Agents — Agent Memory.

Memória operacional dos agentes.

Armazena:
    - última execução
    - último evento
    - último paciente
    - estado atual

NÃO é memória de IA/LLM.
É memória operacional do runtime.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, JSON

from araos.platform.tenant.models import Base


def now_utc():
    return datetime.now(timezone.utc)


class AgentMemoryRecord(Base):
    """Registro de memória operacional de um agente."""
    __tablename__ = "araos_agent_memory"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(100), nullable=False, index=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    
    # Últimos valores conhecidos
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    last_event_id = Column(String(36), nullable=True)
    last_event_type = Column(String(100), nullable=True)
    last_patient_id = Column(String(36), nullable=True, index=True)
    last_consultation_id = Column(String(36), nullable=True)
    
    # Estado atual
    current_state = Column(JSON, nullable=False, default=dict)
    
    # Histórico de execuções recentes (últimas 50)
    execution_history = Column(JSON, nullable=False, default=list)
    
    # Metadados
    memory_metadata = Column(JSON, nullable=True, default=dict)
    
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


@dataclass
class AgentMemory:
    """
    Memória operacional de um agente.
    
    Fornece acesso rápido ao contexto operacional sem consultar
    múltiplas fontes.
    """
    
    agent_id: str
    tenant_id: str
    last_execution_at: Optional[datetime] = None
    last_event_id: Optional[str] = None
    last_event_type: Optional[str] = None
    last_patient_id: Optional[str] = None
    last_consultation_id: Optional[str] = None
    current_state: Dict[str, Any] = field(default_factory=dict)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def record_execution(
        self,
        event_id: Optional[str] = None,
        event_type: Optional[str] = None,
        patient_id: Optional[str] = None,
        consultation_id: Optional[str] = None,
        state_update: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Registra uma execução na memória."""
        self.last_execution_at = now_utc()
        if event_id:
            self.last_event_id = event_id
        if event_type:
            self.last_event_type = event_type
        if patient_id:
            self.last_patient_id = patient_id
        if consultation_id:
            self.last_consultation_id = consultation_id
        if state_update:
            self.current_state.update(state_update)
        
        # Adicionar ao histórico
        self.execution_history.append({
            "timestamp": self.last_execution_at.isoformat(),
            "event_id": event_id,
            "event_type": event_type,
            "patient_id": patient_id,
        })
        
        # Manter apenas últimas 50
        self.execution_history = self.execution_history[-50:]
    
    def get_last_patient(self) -> Optional[str]:
        """Retorna último paciente atendido."""
        return self.last_patient_id
    
    def get_current_state(self, key: str, default: Any = None) -> Any:
        """Retorna valor do estado atual."""
        return self.current_state.get(key, default)
    
    def set_current_state(self, key: str, value: Any) -> None:
        """Define valor no estado atual."""
        self.current_state[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tenant_id": self.tenant_id,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "last_event_id": self.last_event_id,
            "last_event_type": self.last_event_type,
            "last_patient_id": self.last_patient_id,
            "last_consultation_id": self.last_consultation_id,
            "current_state": self.current_state,
            "execution_count": len(self.execution_history),
        }


class MemoryStore:
    """
    Store de memória operacional.
    
    Persiste e carrega AgentMemory do banco.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def load(self, agent_id: str, tenant_id: str) -> AgentMemory:
        """Carrega memória do agente."""
        record = self.db.query(AgentMemoryRecord).filter(
            AgentMemoryRecord.agent_id == agent_id,
            AgentMemoryRecord.tenant_id == tenant_id,
        ).first()
        
        if not record:
            return AgentMemory(agent_id=agent_id, tenant_id=tenant_id)
        
        return AgentMemory(
            agent_id=record.agent_id,
            tenant_id=record.tenant_id,
            last_execution_at=record.last_execution_at,
            last_event_id=record.last_event_id,
            last_event_type=record.last_event_type,
            last_patient_id=record.last_patient_id,
            last_consultation_id=record.last_consultation_id,
            current_state=record.current_state or {},
            execution_history=record.execution_history or [],
        )
    
    def save(self, memory: AgentMemory) -> None:
        """Persiste memória do agente."""
        import uuid
        
        record = self.db.query(AgentMemoryRecord).filter(
            AgentMemoryRecord.agent_id == memory.agent_id,
            AgentMemoryRecord.tenant_id == memory.tenant_id,
        ).first()
        
        if record:
            record.last_execution_at = memory.last_execution_at
            record.last_event_id = memory.last_event_id
            record.last_event_type = memory.last_event_type
            record.last_patient_id = memory.last_patient_id
            record.last_consultation_id = memory.last_consultation_id
            record.current_state = memory.current_state
            record.execution_history = memory.execution_history
        else:
            record = AgentMemoryRecord(
                id=str(uuid.uuid4()),
                agent_id=memory.agent_id,
                tenant_id=memory.tenant_id,
                last_execution_at=memory.last_execution_at,
                last_event_id=memory.last_event_id,
                last_event_type=memory.last_event_type,
                last_patient_id=memory.last_patient_id,
                last_consultation_id=memory.last_consultation_id,
                current_state=memory.current_state,
                execution_history=memory.execution_history,
            )
            self.db.add(record)
        
        self.db.commit()
