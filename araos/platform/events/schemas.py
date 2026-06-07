"""
AraOS Platform — Event Schemas.

Modelo único e canônico para TODOS os eventos da plataforma.
Todos os produtores e consumidores devem usar exatamente este formato.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4


@dataclass
class EventMetadata:
    """
    Metadados de um evento.
    
    Opcional para produtores, preenchido automaticamente pelo Event Bus.
    """
    source: str = ""  # Nome do módulo (siap, voice, smart_flow, concierge)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    environment: str = "production"  # production, staging, development


@dataclass
class EventPayload:
    """
    Payload de um evento.
    
    Deve ser serializável como JSON.
    Não deve conter dados sensíveis desnecessários (LGPD).
    """
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventEnvelope:
    """
    Envelope padrão de todo evento na plataforma ARAOS.
    
    Este é o ÚNICO formato permitido. Nenhum módulo pode publicar
    eventos em formatos diferentes.
    
    Exemplo:
        event = EventEnvelope(
            event_type="PATIENT_CREATED",
            tenant_id="org_123",
            actor_id="user_456",
            actor_type="doctor",
            aggregate_type="patient",
            aggregate_id="pat_789",
            payload=EventPayload(data={"name": "João", "cpf": "***"}),
        )
    """
    
    # Identificação do evento
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = ""  # Ex: PATIENT_CREATED, VOICE_SESSION_STARTED
    event_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Contexto de tenant e ator
    tenant_id: str = ""
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # doctor, patient, system, agent, sensor
    session_id: Optional[str] = None
    
    # Aggregate (entidade de domínio)
    aggregate_type: str = ""  # patient, consultation, document, voice_session
    aggregate_id: str = ""
    
    # Dados
    payload: EventPayload = field(default_factory=EventPayload)
    
    # Metadados
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    # Controle de processamento
    priority: int = 0  # 0=normal, 1=high, 2=critical
    retry_count: int = 0
    max_retries: int = 3
    
    def validate(self) -> None:
        """
        Valida o envelope antes de publicação.
        
        Raises:
            EventValidationError: se campos obrigatórios estiverem ausentes
        """
        from araos.platform.shared.errors import EventValidationError
        
        if not self.event_type:
            raise EventValidationError("event_type is required")
        
        if not self.tenant_id:
            raise EventValidationError("tenant_id is required")
        
        if not self.aggregate_type:
            raise EventValidationError("aggregate_type is required")
        
        if not self.aggregate_id:
            raise EventValidationError("aggregate_id is required")
        
        # Valida formato do event_type
        if "_" not in self.event_type:
            raise EventValidationError(
                f"event_type must follow DOMAIN_ACTION pattern: {self.event_type}"
            )
        
        # Valida que event_type está no catálogo
        from .catalog import is_valid_event_type
        if not is_valid_event_type(self.event_type):
            raise EventValidationError(
                f"event_type '{self.event_type}' not registered in catalog. "
                f"Register it in araos.platform.events.catalog"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict (JSON-serializable)."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "session_id": self.session_id,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload.data,
            "metadata": {
                "source": self.metadata.source,
                "ip_address": self.metadata.ip_address,
                "user_agent": self.metadata.user_agent,
                "trace_id": self.metadata.trace_id,
                "correlation_id": self.metadata.correlation_id,
                "request_id": self.metadata.request_id,
                "environment": self.metadata.environment,
            },
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelope":
        """Deserializa de dict."""
        metadata = EventMetadata(**data.get("metadata", {}))
        payload = EventPayload(data=data.get("payload", {}))
        
        return cls(
            event_id=data.get("event_id", str(uuid4())),
            event_type=data["event_type"],
            event_version=data.get("event_version", "1.0"),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            tenant_id=data["tenant_id"],
            actor_id=data.get("actor_id"),
            actor_type=data.get("actor_type"),
            session_id=data.get("session_id"),
            aggregate_type=data["aggregate_type"],
            aggregate_id=data["aggregate_id"],
            payload=payload,
            metadata=metadata,
            priority=data.get("priority", 0),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )
