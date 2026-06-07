"""
AraOS Platform — Event Envelope V2.

Evolução do envelope de eventos para rastreamento completo.

Novos campos:
    - correlation_id: rastreia jornada completa
    - causation_id: identifica evento que causou este
    - event_category: operational | clinical | system | security
    - priority: normal | high | critical
"""

import uuid
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

from araos.platform.identity.context import IdentityContext, ActorType


class EventPriority(str, Enum):
    """Prioridade do evento."""
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    """Categoria do evento."""
    OPERATIONAL = "operational"   # Login, deploy, health
    CLINICAL = "clinical"         # Diagnóstico, medicação, evolução
    SYSTEM = "system"             # Inicialização, manutenção
    SECURITY = "security"         # Auth, LGPD, audit
    COMMUNICATION = "communication"  # WhatsApp, email, SMS
    FINANCIAL = "financial"       # Pagamento, fatura


@dataclass
class EventEnvelopeV2:
    """
    Envelope canônico V2 de eventos AraOS.
    
    Todo evento na plataforma usa EXATAMENTE este formato.
    
    Fields:
        event_id: UUID4 único do evento
        event_type: tipo do evento (ex: PATIENT_CREATED)
        event_version: versão do schema do evento (ex: "1.0")
        event_category: categoria para separação conceitual
        
        tenant_id: ID da organização
        
        correlation_id: ID que liga todos os eventos de uma jornada
        causation_id: ID do evento que causou este evento
        
        actor_id: ID do ator que gerou o evento
        actor_type: tipo do ator (user, agent, service_account, system)
        
        timestamp: epoch em milissegundos
        
        payload: dados do evento
        metadata: metadados técnicos
        
        priority: prioridade de processamento
        retry_count: tentativas de processamento
    """
    
    event_type: str
    tenant_id: str
    payload: Dict[str, Any]
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_version: str = "1.0"
    event_category: EventCategory = EventCategory.OPERATIONAL
    
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None
    
    timestamp: int = field(default_factory=lambda: int(time.time() * 1000))
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    priority: EventPriority = EventPriority.NORMAL
    retry_count: int = 0
    
    def __post_init__(self):
        # correlation_id herda de causation_id se não definido
        if self.correlation_id is None:
            self.correlation_id = self.causation_id or self.event_id
    
    def with_causation(self, parent_event: "EventEnvelopeV2") -> "EventEnvelopeV2":
        """
        Cria novo evento com causation link para evento pai.
        
        Uso:
            child_event = EventEnvelopeV2(...).with_causation(parent_event)
        """
        self.causation_id = parent_event.event_id
        self.correlation_id = parent_event.correlation_id or parent_event.event_id
        return self
    
    def with_identity(self, identity: IdentityContext) -> "EventEnvelopeV2":
        """
        Preenche actor fields a partir de IdentityContext.
        
        Uso:
            event = EventEnvelopeV2(...).with_identity(request.identity_context)
        """
        self.actor_id = identity.actor_id
        self.actor_type = identity.actor_type.value
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict (JSON-safe)."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "event_category": self.event_category.value,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "retry_count": self.retry_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventEnvelopeV2":
        """Deserializa de dict."""
        return cls(
            event_type=data["event_type"],
            tenant_id=data["tenant_id"],
            payload=data.get("payload", {}),
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_version=data.get("event_version", "1.0"),
            event_category=EventCategory(data.get("event_category", "operational")),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            actor_id=data.get("actor_id"),
            actor_type=data.get("actor_type"),
            timestamp=data.get("timestamp", int(time.time() * 1000)),
            metadata=data.get("metadata", {}),
            priority=EventPriority(data.get("priority", "normal")),
            retry_count=data.get("retry_count", 0),
        )
    
    def is_clinical(self) -> bool:
        """Verifica se evento é clínico."""
        return self.event_category == EventCategory.CLINICAL
    
    def is_critical(self) -> bool:
        """Verifica se evento é crítico."""
        return self.priority == EventPriority.CRITICAL
    
    def __str__(self) -> str:
        return f"Event({self.event_type}:{self.event_id[:8]} tenant={self.tenant_id})"


# ═══════════════════════════════════════════════════════════════════════
# CLINICAL EVENT STREAM
# ═══════════════════════════════════════════════════════════════════════

class ClinicalEvent:
    """
    Eventos clínicos separados conceitualmente.
    
    Usados para:
        - Clinical Intelligence futura
        - Timeline do paciente
        - Reconstrução de prontuário
        - Análise de padrões
    """
    
    # Diagnóstico
    DIAGNOSIS_ADDED = "DIAGNOSIS_ADDED"
    DIAGNOSIS_UPDATED = "DIAGNOSIS_UPDATED"
    
    # Medicação
    MEDICATION_PRESCRIBED = "MEDICATION_PRESCRIBED"
    MEDICATION_ADMINISTERED = "MEDICATION_ADMINISTERED"
    MEDICATION_STOPPED = "MEDICATION_STOPPED"
    
    # Exames
    EXAM_REQUESTED = "EXAM_REQUESTED"
    EXAM_RESULTED = "EXAM_RESULTED"
    EXAM_REVIEWED = "EXAM_REVIEWED"
    
    # Evoluções
    CLINICAL_NOTE_CREATED = "CLINICAL_NOTE_CREATED"
    CLINICAL_NOTE_UPDATED = "CLINICAL_NOTE_UPDATED"
    
    # Alergias
    ALLERGY_REGISTERED = "ALLERGY_REGISTERED"
    ALLERGY_REMOVED = "ALLERGY_REMOVED"
    
    # Protocolos
    PROTOCOL_APPLIED = "PROTOCOL_APPLIED"
    PROTOCOL_COMPLETED = "PROTOCOL_COMPLETED"
    
    # Consulta
    CONSULTATION_STARTED = "CONSULTATION_STARTED"
    CONSULTATION_FINISHED = "CONSULTATION_FINISHED"
    
    ALL_CLINICAL_EVENTS = [
        DIAGNOSIS_ADDED, DIAGNOSIS_UPDATED,
        MEDICATION_PRESCRIBED, MEDICATION_ADMINISTERED, MEDICATION_STOPPED,
        EXAM_REQUESTED, EXAM_RESULTED, EXAM_REVIEWED,
        CLINICAL_NOTE_CREATED, CLINICAL_NOTE_UPDATED,
        ALLERGY_REGISTERED, ALLERGY_REMOVED,
        PROTOCOL_APPLIED, PROTOCOL_COMPLETED,
        CONSULTATION_STARTED, CONSULTATION_FINISHED,
    ]
    
    @classmethod
    def is_clinical(cls, event_type: str) -> bool:
        return event_type in cls.ALL_CLINICAL_EVENTS
