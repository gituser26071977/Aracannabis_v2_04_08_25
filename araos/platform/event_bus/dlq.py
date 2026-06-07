"""
AraOS Platform — Dead Letter Queue.

Armazena eventos que falharam no processamento.
Suporta retry, análise e reprocessamento.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer
from sqlalchemy.orm import Session

from araos.platform.tenant.models import Base


class DeadLetterEvent(Base):
    """Evento na DLQ."""
    __tablename__ = "araos_event_dlq"
    
    id = Column(String(36), primary_key=True)
    event_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    
    payload = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=False)
    error_stack = Column(Text, nullable=True)
    
    consumer_group = Column(String(100), nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    
    status = Column(String(20), nullable=False, default="pending")
    # pending, retrying, failed_permanently, resolved
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    event_metadata = Column(JSON, nullable=True, default=dict)


class DeadLetterQueue:
    """
    Dead Letter Queue para eventos falhos.
    
    Responsabilidades:
        - Armazenar eventos que falharam
        - Suportar retry com backoff
        - Análise de padrões de falha
        - Reprocessamento manual
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def enqueue(
        self,
        event,
        error_message: str,
        consumer_group: str,
        error_stack: Optional[str] = None,
    ) -> str:
        """
        Adiciona evento à DLQ.
        """
        dlq_entry = DeadLetterEvent(
            id=str(__import__('uuid').uuid4()),
            event_id=event.event_id,
            event_type=event.event_type,
            tenant_id=event.tenant_id,
            payload=event.to_dict(),
            error_message=error_message,
            error_stack=error_stack,
            consumer_group=consumer_group,
            retry_count=event.retry_count,
        )
        
        self.db.add(dlq_entry)
        self.db.commit()
        
        return dlq_entry.id
    
    async def list_events(
        self,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Lista eventos na DLQ."""
        query = self.db.query(DeadLetterEvent)
        
        if status:
            query = query.filter(DeadLetterEvent.status == status)
        if tenant_id:
            query = query.filter(DeadLetterEvent.tenant_id == tenant_id)
        
        records = query.order_by(DeadLetterEvent.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": r.id,
                "event_id": r.event_id,
                "event_type": r.event_type,
                "tenant_id": r.tenant_id,
                "error_message": r.error_message,
                "consumer_group": r.consumer_group,
                "retry_count": r.retry_count,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
    
    async def retry(self, dlq_id: str, event_bus) -> bool:
        """
        Reprocessa evento da DLQ.
        
        Args:
            dlq_id: ID do registro na DLQ
            event_bus: Instância do event bus para republicar
        
        Returns:
            True se reprocessamento iniciado
        """
        record = self.db.query(DeadLetterEvent).filter(DeadLetterEvent.id == dlq_id).first()
        if not record:
            return False
        
        if record.retry_count >= record.max_retries:
            record.status = "failed_permanently"
            self.db.commit()
            return False
        
        # Republicar evento
        from .envelope import EventEnvelopeV2
        event = EventEnvelopeV2.from_dict(record.payload)
        event.retry_count = record.retry_count + 1
        
        await event_bus.publish(event)
        
        record.retry_count += 1
        record.status = "retrying"
        self.db.commit()
        
        return True
    
    async def resolve(self, dlq_id: str) -> bool:
        """Marca evento como resolvido manualmente."""
        record = self.db.query(DeadLetterEvent).filter(DeadLetterEvent.id == dlq_id).first()
        if not record:
            return False
        
        record.status = "resolved"
        record.resolved_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    async def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas da DLQ."""
        counts = {}
        for status in ["pending", "retrying", "failed_permanently", "resolved"]:
            counts[status] = self.db.query(DeadLetterEvent).filter(
                DeadLetterEvent.status == status
            ).count()
        return counts
