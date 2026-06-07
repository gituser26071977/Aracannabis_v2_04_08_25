"""
AraOS Platform — Event → Audit Pipeline.

Regra oficial: Eventos críticos geram auditoria automaticamente.

Não depende do desenvolvedor lembrar.
Automatiza a geração de audit entries a partir de eventos.

Eventos auditados automaticamente:
    - Clinical: MEDICATION_PRESCRIBED, DIAGNOSIS_ADDED, PRESCRIPTION_CREATED
    - Security: LOGIN_SUCCEEDED, LOGIN_FAILED, DATA_EXPORT_REQUESTED
    - Financial: PAYMENT_RECEIVED, INVOICE_CREATED
    - LGPD: DATA_PURGED, PATIENT_DELETED
"""

from typing import List, Dict, Any

from .envelope import EventEnvelopeV2, EventCategory, EventPriority


class EventAuditPipeline:
    """
    Pipeline automático: Evento → Audit Entry.
    
    Regra:
        Se evento é crítico OU de categoria security/clinical,
        gera entrada no Audit Ledger automaticamente.
    """
    
    # Eventos que SEMPRE geram auditoria
    ALWAYS_AUDIT = {
        "LOGIN_SUCCEEDED",
        "LOGIN_FAILED",
        "SESSION_REVOKED",
        "PASSWORD_CHANGED",
        "MFA_ENABLED",
        "DATA_EXPORT_REQUESTED",
        "DATA_PURGED",
        "PATIENT_DELETED",
        "PAYMENT_RECEIVED",
        "PAYMENT_FAILED",
        "INVOICE_CREATED",
        "MEDICATION_PRESCRIBED",
        "DIAGNOSIS_ADDED",
        "PRESCRIPTION_CREATED",
        "EVOLUTION_CREATED",
        "CONSULTATION_STARTED",
        "CONSULTATION_FINISHED",
        "USER_IMPERSONATE",
    }
    
    # Categorias que sempre geram auditoria
    AUDIT_CATEGORIES = {
        EventCategory.SECURITY.value,
    }
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def process(self, event: EventEnvelopeV2) -> bool:
        """
        Processa evento e gera auditoria se necessário.
        
        Returns:
            True se audit entry foi gerada
        """
        if not self._should_audit(event):
            return False
        
        await self._create_audit_entry(event)
        return True
    
    def _should_audit(self, event: EventEnvelopeV2) -> bool:
        """
        Determina se evento deve gerar auditoria.
        
        Critérios:
            1. Evento na lista ALWAYS_AUDIT
            2. Categoria security
            3. Prioridade critical
            4. Eventos clínicos (configurável)
        """
        if event.event_type in self.ALWAYS_AUDIT:
            return True
        
        if event.event_category.value in self.AUDIT_CATEGORIES:
            return True
        
        if event.priority == EventPriority.CRITICAL:
            return True
        
        # Eventos clínicos sempre auditados
        if event.event_category == EventCategory.CLINICAL:
            return True
        
        return False
    
    async def _create_audit_entry(self, event: EventEnvelopeV2) -> None:
        """Cria entrada no Audit Ledger."""
        from araos.platform.audit.ledger import AuditEntry
        from datetime import datetime
        
        entry = AuditEntry(
            entry_id=str(__import__('uuid').uuid4()),
            tenant_id=event.tenant_id,
            actor_id=event.actor_id or "system",
            actor_type=event.actor_type or "system",
            action=event.event_type,
            resource_type=event.payload.get("_aggregate_type", "event"),
            resource_id=event.payload.get("_aggregate_id", ""),
            before=None,  # Eventos não têm before/after, apenas o estado atual
            after=event.payload,
            changes_summary=f"Event: {event.event_type}",
            correlation_id=event.correlation_id,
            event_id=event.event_id,
            timestamp=datetime.utcnow(),
            ip_address=event.metadata.get("ip_address"),
            user_agent=event.metadata.get("user_agent"),
        )
        
        self.db.add(entry)
        self.db.commit()
    
    def add_always_audit(self, event_type: str) -> None:
        """Adiciona evento à lista de auditoria obrigatória."""
        self.ALWAYS_AUDIT.add(event_type)
    
    def remove_always_audit(self, event_type: str) -> None:
        """Remove evento da lista de auditoria obrigatória."""
        self.ALWAYS_AUDIT.discard(event_type)
