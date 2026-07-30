"""
AraOS Clinical Observability — Instrumentation cross-cutting.

Cross-cutting concerns para produção:
    - Metrics: counters, timers, gauges (in-memory; adapter Prometheus-ready).
    - Correlation IDs: thread-local + propagation por headers HTTP/event payload.
    - Structured Logging: logger adapter que injeta contexto automaticamente.

INVARIANTE FUNDAMENTAL:

    Toda métrica emitida deve ser determinística e thread-safe.
    Correlation IDs devem propagar por TODA a cadeia (HTTP → publisher
    → store → projection → log).

ADR-0003 — Observability (a ser registrado quando estabilizado).
"""
from .correlation import (
    CorrelationContext,
    current_correlation_id,
    new_correlation_id,
    set_correlation_id,
)
from .logging import StructuredLogger, get_logger
from .metrics import (
    METRIC_AGGREGATE_VERSION,
    METRIC_DEAD_EVENTS,
    METRIC_INVALID_EVENTS,
    METRIC_PENDING_EVENTS,
    METRIC_PROCESSED_EVENTS,
    METRIC_PROJECTION_LAG,
    METRIC_PUBLISHED_EVENTS,
    METRIC_REPLAY_COUNT,
    METRIC_REPLAY_DURATION,
    MetricsRecorder,
    get_metrics,
    reset_metrics,
)

__all__ = [
    "MetricsRecorder",
    "get_metrics",
    "reset_metrics",
    "METRIC_AGGREGATE_VERSION",
    "METRIC_DEAD_EVENTS",
    "METRIC_INVALID_EVENTS",
    "METRIC_PENDING_EVENTS",
    "METRIC_PROCESSED_EVENTS",
    "METRIC_PROJECTION_LAG",
    "METRIC_PUBLISHED_EVENTS",
    "METRIC_REPLAY_COUNT",
    "METRIC_REPLAY_DURATION",
    "CorrelationContext",
    "current_correlation_id",
    "new_correlation_id",
    "set_correlation_id",
    "StructuredLogger",
    "get_logger",
]
