"""
AraOS Platform — Correlation Engine.

Rastreia jornadas completas através de correlation_id.
Permite reconstruir qualquer fluxo distribuído.

Exemplo de jornada:
    WHATSAPP_MESSAGE_RECEIVED
    → DOCUMENT_UPLOADED
    → DOCUMENT_PROCESSED
    → CONSULTATION_SCHEDULED

Todos ligados pelo mesmo correlation_id.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import Session

from araos.platform.tenant.models import Base
from .envelope import EventEnvelopeV2


class CorrelationRecord(Base):
    """Registro de correlação entre eventos."""
    __tablename__ = "araos_event_correlations"
    
    id = Column(String(36), primary_key=True)
    correlation_id = Column(String(36), nullable=False, index=True)
    causation_id = Column(String(36), nullable=True, index=True)
    event_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    tenant_id = Column(String(36), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    event_metadata = Column(JSON, nullable=True, default=dict)


class CorrelationEngine:
    """
    Engine de correlação de eventos.
    
    Permite:
        - Rastrear jornada completa (correlation_id)
        - Reconstruir árvore de causalidade
        - Analisar fluxos entre módulos
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def track(self, event: EventEnvelopeV2) -> None:
        """
        Registra evento na cadeia de correlação.
        """
        if not event.correlation_id:
            return
        
        record = CorrelationRecord(
            id=str(__import__('uuid').uuid4()),
            correlation_id=event.correlation_id,
            causation_id=event.causation_id,
            event_id=event.event_id,
            event_type=event.event_type,
            tenant_id=event.tenant_id,
        )
        
        self.db.add(record)
        self.db.commit()
    
    async def get_chain(self, correlation_id: str) -> List[EventEnvelopeV2]:
        """
        Retorna todos os eventos de uma jornada.
        
        Ordenados por timestamp.
        """
        from .store import EventRecord
        
        records = self.db.query(EventRecord).join(
            CorrelationRecord,
            EventRecord.id == CorrelationRecord.event_id,
        ).filter(
            CorrelationRecord.correlation_id == correlation_id,
        ).order_by(EventRecord.timestamp).all()
        
        from .store import EventStore
        store = EventStore(self.db)
        return [store._to_envelope(r) for r in records]
    
    async def get_tree(self, event_id: str) -> Dict[str, Any]:
        """
        Retorna árvore de causalidade de um evento.
        
        Returns:
            {
                "event_id": "...",
                "event_type": "...",
                "children": [
                    {"event_id": "...", "children": [...]},
                ]
            }
        """
        # Buscar evento raiz
        root = self.db.query(CorrelationRecord).filter(
            CorrelationRecord.event_id == event_id,
        ).first()
        
        if not root:
            return {"event_id": event_id, "children": []}
        
        # Buscar todos os eventos da mesma correlation
        all_records = self.db.query(CorrelationRecord).filter(
            CorrelationRecord.correlation_id == root.correlation_id,
        ).all()
        
        # Construir árvore
        children_map: Dict[str, List[str]] = {}
        event_types: Dict[str, str] = {}
        
        for r in all_records:
            event_types[r.event_id] = r.event_type
            if r.causation_id:
                if r.causation_id not in children_map:
                    children_map[r.causation_id] = []
                children_map[r.causation_id].append(r.event_id)
        
        def build_tree(eid: str) -> Dict[str, Any]:
            return {
                "event_id": eid,
                "event_type": event_types.get(eid, "unknown"),
                "children": [build_tree(cid) for cid in children_map.get(eid, [])],
            }
        
        return build_tree(event_id)
    
    async def get_journey_summary(self, correlation_id: str) -> Dict[str, Any]:
        """
        Retorna resumo da jornada.
        """
        from .store import EventRecord
        
        records = self.db.query(EventRecord).join(
            CorrelationRecord,
            EventRecord.id == CorrelationRecord.event_id,
        ).filter(
            CorrelationRecord.correlation_id == correlation_id,
        ).order_by(EventRecord.timestamp).all()
        
        if not records:
            return {"correlation_id": correlation_id, "events": [], "duration_ms": 0}
        
        events = [
            {"event_id": r.id, "event_type": r.event_type, "timestamp": r.timestamp}
            for r in records
        ]
        
        duration = records[-1].timestamp - records[0].timestamp if len(records) > 1 else 0
        
        return {
            "correlation_id": correlation_id,
            "event_count": len(records),
            "events": events,
            "duration_ms": duration,
            "modules_involved": list(set(r.metadata.get("source", "unknown") for r in records)),
        }
