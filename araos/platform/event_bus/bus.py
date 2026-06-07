"""
AraOS Platform — Event Bus.

Interface principal do sistema nervoso.
Integra publisher, consumer, store, DLQ, correlation, replay.

Uso:
    bus = AraOSEventBus(redis_client, db_session)
    
    # Publicar
    await bus.publish(event)
    
    # Consumir
    await bus.subscribe(["PATIENT_CREATED"], "audit-group", handler)
    
    # Replay
    events = await bus.replay("patient", "pat_123")
"""

from typing import List, Callable, Optional, Dict, Any, Awaitable

from .envelope import EventEnvelopeV2
from .publisher import RedisEventPublisher
from .consumer import RedisEventConsumer
from .store import EventStore
from .dlq import DeadLetterQueue
from .correlation import CorrelationEngine
from .replay import EventReplay
from .metrics import EventMetrics
from .pipeline import EventAuditPipeline


Handler = Callable[[EventEnvelopeV2], Awaitable[None]]


class AraOSEventBus:
    """
    Event Bus central da plataforma AraOS.
    
    Responsabilidades:
        - Publicar eventos
        - Consumir eventos
        - Roteamento por tipo
        - Persistência no EventStore
        - DLQ para falhas
        - Correlação de eventos
        - Replay de eventos
        - Métricas
        - Pipeline de auditoria automática
    """
    
    def __init__(
        self,
        redis_client,
        db_session,
        secret_key: Optional[str] = None,
    ):
        self.publisher = RedisEventPublisher(redis_client)
        self.consumer = RedisEventConsumer(redis_client)
        self.store = EventStore(db_session)
        self.dlq = DeadLetterQueue(db_session)
        self.correlation = CorrelationEngine(db_session)
        self.replay = EventReplay(db_session)
        self.metrics = EventMetrics(redis_client)
        self.audit_pipeline = EventAuditPipeline(db_session)
    
    # ─── Publicação ──────────────────────────────────────────────────
    
    async def publish(self, event: EventEnvelopeV2) -> str:
        """
        Publica evento no bus.
        
        Fluxo:
            1. Valida evento
            2. Persiste no EventStore
            3. Publica no Redis Stream
            4. Atualiza correlação
            5. Gera métricas
            6. Pipeline de auditoria (se crítico)
        """
        # 1. Validar
        self._validate_event(event)
        
        # 2. Persistir
        await self.store.save(event)
        
        # 3. Publicar no Redis
        message_id = await self.publisher.publish(event)
        
        # 4. Correlação
        await self.correlation.track(event)
        
        # 5. Métricas
        await self.metrics.record_published(event)
        
        # 6. Pipeline de auditoria
        await self.audit_pipeline.process(event)
        
        return message_id
    
    async def publish_many(self, events: List[EventEnvelopeV2]) -> List[str]:
        """Publica múltiplos eventos."""
        ids = []
        for event in events:
            event_id = await self.publish(event)
            ids.append(event_id)
        return ids
    
    # ─── Consumo ─────────────────────────────────────────────────────
    
    async def subscribe(
        self,
        event_types: List[str],
        consumer_group: str,
        handler: Handler,
        auto_dlq: bool = True,
    ) -> None:
        """
        Registra consumidor com DLQ automática.
        
        Args:
            event_types: Tipos de evento a consumir
            consumer_group: Nome do grupo
            handler: Handler async
            auto_dlq: Se True, falhas vão para DLQ
        """
        async def wrapped_handler(event: EventEnvelopeV2):
            try:
                await handler(event)
                await self.metrics.record_consumed(event, consumer_group)
            except Exception as e:
                await self.metrics.record_failed(event, consumer_group, str(e))
                if auto_dlq:
                    await self.dlq.enqueue(event, str(e), consumer_group)
                raise
        
        await self.consumer.subscribe(event_types, consumer_group, wrapped_handler)
    
    async def consume(
        self,
        consumer_group: str,
        consumer_name: str,
    ) -> List[EventEnvelopeV2]:
        """Consome eventos pendentes."""
        return await self.consumer.consume(consumer_group, consumer_name)
    
    # ─── Replay ──────────────────────────────────────────────────────
    
    async def replay(
        self,
        aggregate_type: str,
        aggregate_id: str,
        from_timestamp: Optional[int] = None,
    ) -> List[EventEnvelopeV2]:
        """
        Replay de eventos para reconstrução de estado.
        
        Args:
            aggregate_type: Tipo do aggregate (patient, consultation)
            aggregate_id: ID do aggregate
            from_timestamp: Timestamp inicial (opcional)
        
        Returns:
            Lista de eventos ordenados
        """
        return await self.replay.replay(aggregate_type, aggregate_id, from_timestamp)
    
    async def get_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[EventEnvelopeV2]:
        """Retorna histórico completo de eventos para um aggregate."""
        return await self.replay.get_history(aggregate_type, aggregate_id)
    
    # ─── Correlação ──────────────────────────────────────────────────
    
    async def get_correlation_chain(
        self,
        correlation_id: str,
    ) -> List[EventEnvelopeV2]:
        """
        Retorna todos os eventos de uma jornada.
        
        Exemplo:
            WHATSAPP_RECEIVED → DOCUMENT_UPLOADED → CONSULTATION_SCHEDULED
        """
        return await self.correlation.get_chain(correlation_id)
    
    async def get_causation_tree(
        self,
        event_id: str,
    ) -> Dict[str, Any]:
        """
        Retorna árvore de causalidade de um evento.
        """
        return await self.correlation.get_tree(event_id)
    
    # ─── DLQ ─────────────────────────────────────────────────────────
    
    async def get_dlq(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retorna eventos na DLQ."""
        return await self.dlq.list_events(limit)
    
    async def retry_dlq(self, event_id: str) -> bool:
        """Reprocessa evento da DLQ."""
        return await self.dlq.retry(event_id, self)
    
    # ─── Métricas ────────────────────────────────────────────────────
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do event bus."""
        return await self.metrics.get_summary()
    
    # ─── Validação ───────────────────────────────────────────────────
    
    def _validate_event(self, event: EventEnvelopeV2) -> None:
        """Valida evento antes de publicar."""
        from araos.platform.events.catalog import is_valid_event_type
        from araos.platform.shared.errors import EventValidationError
        
        if not event.event_type:
            raise EventValidationError("event_type is required")
        
        if not event.tenant_id:
            raise EventValidationError("tenant_id is required")
        
        if not is_valid_event_type(event.event_type):
            raise EventValidationError(
                f"event_type '{event.event_type}' not registered in catalog"
            )
    
    # ─── Health ──────────────────────────────────────────────────────
    
    async def health(self) -> Dict[str, bool]:
        """Healthcheck do event bus."""
        return {
            "publisher": await self.publisher.health(),
            "store": await self.store.health(),
        }
