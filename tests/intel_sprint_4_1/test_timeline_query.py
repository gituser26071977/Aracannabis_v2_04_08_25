"""
test_timeline_query.py — InMemoryTimelineQuery tests.

Cobre:
    - for_patient: ordenação por sequence ASC, filtros (window/event_types/episode)
    - for_aggregate: retorna apenas eventos do aggregate
    - count: contagem por tenant/patient
    - Integração com ClinicalEventPublisher (publish → query)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.timeline.application.query import InMemoryTimelineQuery
from araos.clinical.timeline.domain.window import TimeWindow


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _publish(publisher, **kwargs) -> str:
    """Helper para publicar evento com defaults sensatos."""
    defaults = dict(
        tenant_id="t1",
        patient_id="p1",
        event_type="DIAGNOSIS_CONFIRMED",
        event_datetime=_now(),
        source_module="neurodevelopmental",
        payload={"condition_code": "TEA_F84.0"},
        aggregate_type="diagnosis",
        aggregate_id="diag-1",
        created_by="doc-1",
    )
    defaults.update(kwargs)
    return publisher.publish(**defaults)


def REDACTED(
    publisher, timeline_query
):
    e1 = _publish(publisher, event_type="DIAGNOSIS_HYPOTHESIZED", aggregate_id="d1")
    e2 = _publish(publisher, event_type="DIAGNOSIS_CONFIRMED", aggregate_id="d1")
    e3 = _publish(publisher, event_type="OUTCOME_IMPROVEMENT", aggregate_id="o1")

    entries = timeline_query.for_patient("t1", "p1")
    assert len(entries) == 3
    # Ordenado por sequence ASC
    assert entries[0].event_id == e1
    assert entries[1].event_id == e2
    assert entries[2].event_id == e3
    assert [e.sequence for e in entries] == sorted(e.sequence for e in entries)


def test_query_filters_by_event_type(publisher, timeline_query):
    _publish(publisher, event_type="DIAGNOSIS_HYPOTHESIZED")
    _publish(publisher, event_type="OUTCOME_IMPROVEMENT")
    _publish(publisher, event_type="OUTCOME_WORSENING")

    only_outcomes = timeline_query.for_patient(
        "t1", "p1", event_types=["OUTCOME_*"],
    )
    assert len(only_outcomes) == 2
    assert all(e.event_type.startswith("OUTCOME") for e in only_outcomes)


def REDACTED(publisher, timeline_query):
    _publish(publisher, event_type="DIAGNOSIS_HYPOTHESIZED")
    _publish(publisher, event_type="DIAGNOSIS_CONFIRMED")

    only_confirmed = timeline_query.for_patient(
        "t1", "p1", event_types=["DIAGNOSIS_CONFIRMED"],
    )
    assert len(only_confirmed) == 1
    assert only_confirmed[0].event_type == "DIAGNOSIS_CONFIRMED"


def test_query_filters_by_window(publisher, timeline_query):
    t0 = _now()
    t1 = t0 + timedelta(days=10)
    t2 = t0 + timedelta(days=20)
    t3 = t0 + timedelta(days=30)

    _publish(publisher, event_datetime=t1)
    _publish(publisher, event_datetime=t2)
    _publish(publisher, event_datetime=t3)

    window = TimeWindow.between(
        t0 + timedelta(days=5),
        t0 + timedelta(days=25),
        label="filtered_window",
    )
    entries = timeline_query.for_patient("t1", "p1", window=window)
    assert len(entries) == 2
    assert entries[0].event_datetime == t1
    assert entries[1].event_datetime == t2


def test_query_window_excludes_outside(publisher, timeline_query):
    t0 = _now()
    _publish(publisher, event_datetime=t0)
    _publish(publisher, event_datetime=t0 + timedelta(days=100))

    window = TimeWindow.between(t0 - timedelta(days=10), t0 + timedelta(days=10))
    entries = timeline_query.for_patient("t1", "p1", window=window)
    assert len(entries) == 1


def test_query_filters_by_episode_id(event_store, timeline_query):
    """Injeta eventos direto no store com episode_id setado (Sprint 4.2
    vai popular via aggregate flow; aqui apenas validamos o filtro)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for i in range(3):
        event_store._events.append({       # type: ignore[attr-defined]
            "event_id": f"ev-{i}",
            "sequence": i + 1,
            "event_type": "ASSESSMENT_APPLIED",
            "aggregate_type": "assessment",
            "aggregate_id": f"a-{i}",
            "event_datetime": now,
            "transaction_time": now,
            "recorded_at": now,
            "aggregate_version": 1,
            "actor_id": "doc-1",
            "tenant_id": "t1",
            "patient_id": "p1",
            "payload": {},
            "metadata": {},
            "episode_id": "ep-1" if i < 2 else "ep-2",
        })

    ep1 = timeline_query.for_patient("t1", "p1", episode_id="ep-1")
    ep2 = timeline_query.for_patient("t1", "p1", episode_id="ep-2")
    assert len(ep1) == 2
    assert len(ep2) == 1


def test_query_for_aggregate(publisher, timeline_query):
    _publish(publisher, aggregate_type="diagnosis", aggregate_id="d1")
    _publish(publisher, aggregate_type="diagnosis", aggregate_id="d1")
    _publish(publisher, aggregate_type="intervention", aggregate_id="i1")

    d1 = timeline_query.for_aggregate("t1", "diagnosis", "d1")
    assert len(d1) == 2
    assert all(e.aggregate_id == "d1" for e in d1)


def test_query_count(publisher, timeline_query):
    assert timeline_query.count("t1", "p1") == 0
    _publish(publisher)
    _publish(publisher)
    assert timeline_query.count("t1", "p1") == 2


def test_query_tenant_isolation(publisher, timeline_query):
    _publish(publisher, tenant_id="t1")
    _publish(publisher, tenant_id="t2")
    t1 = timeline_query.for_patient("t1", "p1")
    t2 = timeline_query.for_patient("t2", "p1")
    assert len(t1) == 1
    assert len(t2) == 1


def test_query_respects_limit(publisher, timeline_query):
    for _ in range(20):
        _publish(publisher)
    entries = timeline_query.for_patient("t1", "p1", limit=5)
    assert len(entries) == 5


def test_query_skips_malformed_events(publisher, timeline_query):
    """Eventos válidos passam; event_datetime ausente não chega ao TimelineQuery
    (crasha antes no store). Validamos apenas que timeline_query lida bem
    com payload estranho vindo de eventos válidos."""
    e1 = _publish(publisher, payload={"weird": "data"})
    entries = timeline_query.for_patient("t1", "p1")
    assert len(entries) == 1
    assert entries[0].event_id == e1


def REDACTED():
    from araos.clinical.timeline.application.query import TimelineQuery
    assert issubclass(InMemoryTimelineQuery, TimelineQuery)


def REDACTED(timeline_query):
    assert timeline_query.for_patient("nonexistent", "p1") == []
    assert timeline_query.count("nonexistent") == 0