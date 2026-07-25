"""
AraOS Clinical — Clinical Timeline Engine (Sprint 4.1).

Read-side temporal motor para reconstrução completa da história clínica
do paciente. Todo evento clínico carrega:

    - event_datetime        → valid_time (quando o evento CLÍNICO aconteceu)
    - recorded_at           → transaction_time (quando foi publicado)
    - aggregate_version
    - episode_id (opcional) → link se atribuído a um episódio (Sprint 4.2)
    - correlation_id        → propagação cross-cutting

Reutiliza ClinicalEventStore (Sprint 3.1) como source-of-truth.
NÃO duplica dados — apenas lê + agrega + projeta.

API pública (Sprint 4.1):
    TimelineEntry          — value object imutável (bitemporal)
    TimeWindow             — janela temporal para filtros
    VariableSpec           — spec de variável clínica
    TimelineQuery (ABC)    — interface de leitura
    InMemoryTimelineQuery  — impl para testes (delega ao EventStore)

Mantém compat: `ClinicalTimeline` (legacy) e `TimelineEntry` (legacy ORM model)
ainda são exportados para callers existentes.
"""

from araos.clinical.timeline.domain.entries import TimelineEntry as DomainTimelineEntry
from araos.clinical.timeline.domain.window import TimeWindow
from araos.clinical.timeline.domain.variable import VariableSpec
from araos.clinical.timeline.application.query import (
    TimelineQuery,
    InMemoryTimelineQuery,
)

# Compat shim — legacy import path ainda funciona
from araos.clinical.timeline.models import TimelineEntry, ClinicalTimeline

TimelineEntry = DomainTimelineEntry  # type: ignore[misc,assignment]

__all__ = [
    "TimelineEntry",
    "DomainTimelineEntry",
    "TimeWindow",
    "VariableSpec",
    "TimelineQuery",
    "InMemoryTimelineQuery",
    "ClinicalTimeline",
]