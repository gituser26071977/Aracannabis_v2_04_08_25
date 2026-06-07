"""
AraOS Platform — Event Store.

Persistência durável de eventos em PostgreSQL.

Usado para:
    - Replay de eventos
    - Audit
    - Debugging
    - Event Sourcing (preparação)
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime, JSON, Index
from sqlalchemy.orm import Session

from araos.platform.tenant.models import Base
from .envelope import EventEnvelopeV2, EventCategory


class EventRecord(Base):
    """Registro de evento persistido."""
    __tablename__ = "araos_event_store"
    
    id = Column(String(36), primary_key=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_version = Column(String(10), nullable=False, default="1.0")
    event_category = Column(String(20), nullable=False, default="operational")
    
    tenant_id = Column(String(36), nullable=False, index=True)
    
    correlation_id = Column(String(36), nullable=True, index=True)
    causation_id = Column(String(36), nullable=True, index=True)
    
    actor_id = Column(String(36), nullable=True)
    actor_type = Column(String(50), nullable=True)
    
    aggregate_type = Column(String(50), nullable=True, index=True)
    aggregate_id = Column(String(36), nullable=True, index=True)
    
    timestamp = Column(BigInteger, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    event_metadata = Column(JSON, nullable=True, default=dict)
    
    priority = Column(String(20), nullable=False, default="normal")
    retry_count = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_event_store_tenant_type", "tenant_id", "event_type"),
        Index("ix_event_store_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_event_store_timestamp", "timestamp"),
    )


class EventStore:
    """
    Store durável de eventos.
    
    Persiste todos os eventos em PostgreSQL para:
        - Replay
        - Audit
        - Debugging
        - Event Sourcing futuro
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def save(self, event: EventEnvelopeV2) -> str:
        """Persiste evento no banco."""
        # Extrair aggregate do payload se disponível
        aggregate_type = event.payload.get("_aggregate_type", "")
        aggregate_id = event.payload.get("_aggregate_id", "")
        
        record = EventRecord(
            id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            event_category=event.event_category.value,
            tenant_id=event.tenant_id,
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            actor_id=event.actor_id,
            actor_type=event.actor_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            timestamp=event.timestamp,
            payload=event.payload,
            metadata=event.metadata,
            priority=event.priority.value,
            retry_count=event.retry_count,
        )
        
        self.db.add(record)
        self.db.commit()
        
        return event.event_id
    
    async def get_by_id(self, event_id: str) -> Optional[EventEnvelopeV2]:
        """Busca evento por ID."""
        record = self.db.query(EventRecord).filter(EventRecord.id == event_id).first()
        return self._to_envelope(record) if record else None
    
    async def get_by_correlation(
        self,
        correlation_id: str,
    ) -> List[EventEnvelopeV2]:
        """Busca eventos por correlation_id."""
        records = self.db.query(EventRecord).filter(
            EventRecord.correlation_id == correlation_id,
        ).order_by(EventRecord.timestamp).all()
        return [self._to_envelope(r) for r in records]
    
    async def get_by_aggregate(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_timestamp: Optional[int] = None,
    ) -> List[EventEnvelopeV2]:
        """Busca eventos de um aggregate."""
        query = self.db.query(EventRecord).filter(
            EventRecord.aggregate_type == aggregate_type,
            EventRecord.aggregate_id == aggregate_id,
        )
        if from_timestamp:
            query = query.filter(EventRecord.timestamp >= from_timestamp)
        
        records = query.order_by(EventRecord.timestamp).all()
        return [self._to_envelope(r) for r in records]
    
    async def get_by_tenant(
        self,
        tenant_id: str,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EventEnvelopeV2]:
        """Busca eventos de um tenant."""
        query = self.db.query(EventRecord).filter(
            EventRecord.tenant_id == tenant_id,
        )
        if event_type:
            query = query.filter(EventRecord.event_type == event_type)
        
        records = query.order_by(EventRecord.timestamp.desc()).offset(offset).limit(limit).all()
        return [self._to_envelope(r) for r in records]
    
    async def health(self) -> bool:
        """Healthcheck do store."""
        try:
            self.db.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def _to_envelope(self, record: EventRecord) -> EventEnvelopeV2:
        """Converte EventRecord para EventEnvelopeV2."""
        return EventEnvelopeV2(
            event_type=record.event_type,
            tenant_id=record.tenant_id,
            payload=record.payload or {},
            event_id=record.id,
            event_version=record.event_version,
            event_category=EventCategory(record.event_category),
            correlation_id=record.correlation_id,
            causation_id=record.causation_id,
            actor_id=record.actor_id,
            actor_type=record.actor_type,
            timestamp=record.timestamp,
            metadata=record.event_metadata or {},
            priority=EventPriority(record.priority),
            retry_count=record.retry_count,
        )


# Import tardio para evitar circular
from .envelope import EventPriority
