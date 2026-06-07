"""
AraOS Platform — Event Bus (The Nervous System).

Sistema nervoso central da plataforma.
Comunicação, observabilidade, auditoria, rastreabilidade.

Stack: Redis Streams (baixa complexidade, alta compatibilidade futura).
"""

from .envelope import EventEnvelopeV2, EventPriority, EventCategory
from .publisher import RedisEventPublisher
from .consumer import RedisEventConsumer
from .bus import AraOSEventBus
from .router import EventRouter
from .registry import HandlerRegistry
from .store import EventStore
from .dlq import DeadLetterQueue
from .correlation import CorrelationEngine
from .replay import EventReplay
from .metrics import EventMetrics
from .pipeline import EventAuditPipeline

__all__ = [
    "EventEnvelopeV2",
    "EventPriority",
    "EventCategory",
    "RedisEventPublisher",
    "RedisEventConsumer",
    "AraOSEventBus",
    "EventRouter",
    "HandlerRegistry",
    "EventStore",
    "DeadLetterQueue",
    "CorrelationEngine",
    "EventReplay",
    "EventMetrics",
    "EventAuditPipeline",
]
