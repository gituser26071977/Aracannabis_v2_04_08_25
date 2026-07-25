"""
test_observability.py — Métricas, correlation IDs e logging estruturado.

Garante que:
    - Metrics são emitidas em pontos críticos (apply, replay).
    - Correlation IDs propagam corretamente.
    - StructuredLogger formata JSON com contexto.
    - dump_prometheus() retorna formato válido.
"""
from __future__ import annotations

import json
import logging
from unittest.mock import patch

import pytest

from araos.clinical.observability import (
    CorrelationContext,
    METRIC_DEAD_EVENTS,
    METRIC_PROCESSED_EVENTS,
    METRIC_PUBLISHED_EVENTS,
    METRIC_REPLAY_COUNT,
    METRIC_REPLAY_DURATION,
    StructuredLogger,
    clear_correlation_id,
    correlation_scope,
    current_correlation_id,
    get_logger,
    get_metrics,
    new_correlation_id,
    reset_metrics,
    set_correlation_id,
)
from araos.clinical.observability.metrics import MetricsRecorder
from tests.neurodev_sprint_3_2.builders import EventBuilder


# ─── Metrics ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset():
    reset_metrics()
    clear_correlation_id()
    yield
    reset_metrics()
    clear_correlation_id()


def test_metrics_recorder_counter():
    m = MetricsRecorder()
    m.counter_inc("foo")
    m.counter_inc("foo", n=5)
    assert m.counter_get("foo") == 6


def test_metrics_recorder_gauge():
    m = MetricsRecorder()
    m.gauge_set("bar", 10.0)
    assert m.gauge_get("bar") == 10.0
    m.gauge_inc("bar", 5.0)
    assert m.gauge_get("bar") == 15.0
    m.gauge_dec("bar", 3.0)
    assert m.gauge_get("bar") == 12.0


def test_metrics_recorder_timer():
    m = MetricsRecorder()
    with m.timer("replay"):
        sum(range(1000))
    snap = m.snapshot()
    assert "replay" in snap["histograms"]
    assert snap["histograms"]["replay"]["count"] == 1
    assert snap["histograms"]["replay"]["sum"] >= 0


def test_metrics_dump_prometheus():
    m = MetricsRecorder()
    m.counter_inc("test_counter", n=42)
    m.gauge_set("test_gauge", 3.14)
    output = m.dump_prometheus()
    assert "# TYPE test_counter counter" in output
    assert "test_counter 42" in output
    assert "# TYPE test_gauge gauge" in output
    assert "test_gauge 3.14" in output


def test_metrics_singleton():
    m1 = get_metrics()
    m2 = get_metrics()
    assert m1 is m2


def test_metrics_emitted_on_projection(projection):
    """Projection deve emitir métricas em apply_batch/replay_all."""
    event = (
        EventBuilder()
        .with_type("CLINICAL_IDENTITY_CREATED")
        .with_aggregate("clinical_identity", "id-1")
        .with_payload(patient_id="p-1", identity_id="id-1")
        .with_tenant("t-metrics")
        .build()
    )
    projection.apply(event)
    m = get_metrics()
    assert m.counter_get(METRIC_PROCESSED_EVENTS) >= 1


def test_replay_count_metric(projection, publisher):
    """replay_all() deve incrementar REPLAY_COUNT e registrar duração."""
    from datetime import datetime
    event = (
        EventBuilder()
        .with_type("CLINICAL_IDENTITY_CREATED")
        .with_aggregate("clinical_identity", "id-rp")
        .with_payload(patient_id="p-1", identity_id="id-rp")
        .with_tenant("t-rp-met")
        .build()
    )
    eid = publisher.publish(
        tenant_id="t-rp-met",
        patient_id="p-1",
        event_type=event["event_type"],
        event_datetime=datetime.fromisoformat(
            event["event_datetime"].replace("Z", "+00:00")
        ),
        source_module="neurodevelopmental",
        payload=event["payload"],
        aggregate_type=event["aggregate_type"],
        aggregate_id=event["aggregate_id"],
    )

    projection.replay_all("t-rp-met")
    m = get_metrics()
    assert m.counter_get(METRIC_REPLAY_COUNT) == 1
    snap = m.snapshot()
    assert METRIC_REPLAY_DURATION in snap["histograms"]
    assert snap["histograms"][METRIC_REPLAY_DURATION]["count"] >= 1


def test_dead_events_metric(projection):
    """Evento sem handler deve incrementar DEAD_EVENTS counter."""
    event = (
        EventBuilder()
        .with_type("UNKNOWN_EVENT_TYPE_FOR_TEST")
        .with_aggregate("unknown", "x-1")
        .with_payload({})
        .with_tenant("t-dead")
        .build()
    )
    projection.apply(event)
    m = get_metrics()
    assert m.counter_get(METRIC_DEAD_EVENTS) >= 1


# ─── Correlation IDs ──────────────────────────────────────────────────────


def REDACTED():
    cid = new_correlation_id()
    assert isinstance(cid, str)
    assert len(cid) == 36  # UUID4


def test_correlation_id_thread_local():
    set_correlation_id("cid-1")
    assert current_correlation_id() == "cid-1"
    clear_correlation_id()
    assert current_correlation_id() is None


def REDACTED():
    set_correlation_id("outer")
    with CorrelationContext("inner"):
        assert current_correlation_id() == "inner"
    # Outer restaurado após exit
    assert current_correlation_id() == "outer"
    clear_correlation_id()


def REDACTED():
    with CorrelationContext() as cid:
        assert cid is not None
        assert current_correlation_id() == cid


def test_correlation_scope_yields_id():
    with correlation_scope("scope-1") as cid:
        assert cid == "scope-1"
        assert current_correlation_id() == "scope-1"


# ─── StructuredLogger ────────────────────────────────────────────────────


def test_structured_logger_emits_json(caplog):
    caplog.set_level(logging.INFO)
    logger = get_logger("test.structured")
    logger.info("test_event", extra={"foo": "bar"})

    assert len(caplog.records) == 1
    record = caplog.records[0]
    # Logger format é o JSON string (chamamos info() com formatted string)
    payload = json.loads(record.getMessage())
    assert payload["message"] == "test_event"
    assert payload["foo"] == "bar"
    assert payload["level"] == "INFO"


def REDACTED(caplog):
    caplog.set_level(logging.INFO)
    logger = get_logger("test.corr")
    set_correlation_id("cid-abc")
    logger.info("event_with_corr")
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["correlation_id"] == "cid-abc"
    clear_correlation_id()


def test_structured_logger_warning(caplog):
    caplog.set_level(logging.WARNING)
    logger = get_logger("test.warn")
    logger.warning("warning_event")
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["level"] == "WARNING"


def test_structured_logger_error(caplog):
    caplog.set_level(logging.ERROR)
    logger = get_logger("test.err")
    logger.error("error_event", extra={"code": 500})
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["level"] == "ERROR"
    assert payload["code"] == 500


def REDACTED():
    l1 = get_logger("test.singleton")
    l2 = get_logger("test.singleton")
    assert l1 is l2


# ─── End-to-end: correlation propaga por apply ────────────────────────────


def REDACTED(projection, caplog):
    """
    Cenário: set correlation_id → apply() → log gerado deve conter correlation_id.
    """
    caplog.set_level(logging.INFO)
    set_correlation_id("cid-e2e")

    event = (
        EventBuilder()
        .with_type("CLINICAL_IDENTITY_CREATED")
        .with_aggregate("clinical_identity", "id-cid")
        .with_payload(patient_id="p-cid", identity_id="id-cid")
        .with_tenant("t-cid")
        .build()
    )
    projection.apply(event)

    # Procura log "event_applied" no caplog
    applied_logs = [
        r for r in caplog.records if "event_applied" in r.getMessage()
    ]
    assert applied_logs, "Expected at least one event_applied log"
    payload = json.loads(applied_logs[-1].getMessage())
    assert payload["correlation_id"] == "cid-e2e"
    clear_correlation_id()
