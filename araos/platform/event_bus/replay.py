"""
AraOS Platform — Event Replay.

Arquitetura para reconstrução de estado a partir de eventos.

Suporta:
    - Reconstruir timeline de paciente
    - Reconstruir histórico de consulta
    - Reconstruir fluxo de Smart Flow
    - Reconstruir ações do Voice

Mesmo que inicialmente seja apenas interface preparada,
a arquitetura deve suportar Event Sourcing futuro.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

from .envelope import EventEnvelopeV2


@dataclass
class ReplayResult:
    """Resultado de um replay."""
    aggregate_type: str
    aggregate_id: str
    events: List[EventEnvelopeV2]
    state_snapshot: Optional[Dict[str, Any]] = None
    
    @property
    def event_count(self) -> int:
        return len(self.events)
    
    @property
    def time_span_ms(self) -> int:
        if len(self.events) < 2:
            return 0
        return self.events[-1].timestamp - self.events[0].timestamp


class EventReplay:
    """
    Replay de eventos para reconstrução de estado.
    
    Conceitos:
        - Aggregate: entidade de domínio (patient, consultation)
        - Event Stream: sequência de eventos do aggregate
        - Projection: estado reconstruído
        - Snapshot: cache do estado em um ponto do tempo
    
    Uso:
        replay = EventReplay(db_session)
        
        # Reconstruir paciente
        result = await replay.replay("patient", "pat_123")
        for event in result.events:
            apply_event(state, event)
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def replay(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> ReplayResult:
        """
        Replay de eventos para um aggregate.
        
        Args:
            aggregate_type: Tipo do aggregate
            aggregate_id: ID do aggregate
            from_timestamp: Timestamp inicial (epoch ms)
            to_timestamp: Timestamp final (epoch ms)
        
        Returns:
            ReplayResult com eventos ordenados
        """
        from .store import EventRecord
        
        query = self.db.query(EventRecord).filter(
            EventRecord.aggregate_type == aggregate_type,
            EventRecord.aggregate_id == aggregate_id,
        )
        
        if from_timestamp:
            query = query.filter(EventRecord.timestamp >= from_timestamp)
        if to_timestamp:
            query = query.filter(EventRecord.timestamp <= to_timestamp)
        
        records = query.order_by(EventRecord.timestamp).all()
        
        from .store import EventStore
        store = EventStore(self.db)
        events = [store._to_envelope(r) for r in records]
        
        return ReplayResult(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            events=events,
        )
    
    async def get_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[EventEnvelopeV2]:
        """Retorna histórico completo de eventos."""
        result = await self.replay(aggregate_type, aggregate_id)
        return result.events
    
    async def get_timeline(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retorna timeline visualizável.
        
        Formato:
            [
                {"time": "2026-06-07T10:00:00", "event": "PATIENT_CREATED", "data": {...}},
                {"time": "2026-06-07T10:05:00", "event": "CONSULTATION_STARTED", "data": {...}},
            ]
        """
        result = await self.replay(aggregate_type, aggregate_id)
        
        return [
            {
                "time": self._format_time(e.timestamp),
                "event_type": e.event_type,
                "event_id": e.event_id,
                "actor_id": e.actor_id,
                "actor_type": e.actor_type,
                "payload_summary": self._summarize_payload(e.payload),
            }
            for e in result.events
        ]
    
    async def build_projection(
        self,
        aggregate_type: str,
        aggregate_id: str,
        projector: Callable[[Dict[str, Any], EventEnvelopeV2], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Reconstrói estado aplicando projector a cada evento.
        
        Args:
            aggregate_type: Tipo do aggregate
            aggregate_id: ID do aggregate
            projector: Função (state, event) -> new_state
        
        Returns:
            Estado final reconstruído
        """
        result = await self.replay(aggregate_type, aggregate_id)
        
        state = {}
        for event in result.events:
            state = projector(state, event)
        
        return state
    
    def _format_time(self, timestamp_ms: int) -> str:
        """Formata timestamp para ISO string."""
        from datetime import datetime
        return datetime.utcfromtimestamp(timestamp_ms / 1000).isoformat() + "Z"
    
    def _summarize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cria sumário do payload (remove dados sensíveis)."""
        # Remover campos sensíveis
        sensitive = {"password", "cpf", "rg", "senha", "token", "api_key"}
        return {
            k: "***" if k.lower() in sensitive else v
            for k, v in payload.items()
        }
