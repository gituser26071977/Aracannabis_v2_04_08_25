"""
test_timeline_domain.py — pure domain unit tests para Sprint 4.1.

Cobre:
    - TimelineEntry: construção, validação, from_event(), to_dict()
    - TimeWindow: invariantes, duration, contains(), last_days()
    - VariableSpec: invariantes, matches(), extract_value()

Domain é pure Python, zero infraestrutura — testes rápidos.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.timeline.domain.entries import TimelineEntry
from araos.clinical.timeline.domain.variable import (
    VariableSource,
    VariableSpec,
)
from araos.clinical.timeline.domain.window import TimeWindow


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ─── TimelineEntry ────────────────────────────────────────────────────


def _entry(**overrides) -> TimelineEntry:
    defaults = dict(
        event_id="ev-1",
        sequence=1,
        event_type="DIAGNOSIS_CONFIRMED",
        aggregate_type="diagnosis",
        aggregate_id="diag-1",
        event_datetime=_now(),
        recorded_at=_now(),
        aggregate_version=1,
        actor_id="doctor-1",
        payload={"condition_code": "TEA_F84.0"},
    )
    defaults.update(overrides)
    return TimelineEntry(**defaults)


def REDACTED():
    e = _entry()
    assert e.event_id == "ev-1"
    assert e.event_type == "DIAGNOSIS_CONFIRMED"
    assert e.sequence == 1
    assert e.episode_id is None
    assert e.correlation_id is None


def test_timeline_entry_immutable():
    e = _entry()
    with pytest.raises(Exception):    # FrozenInstanceError
        e.event_id = "mutated"  # type: ignore[misc]


def REDACTED():
    with pytest.raises(ValueError, match="event_id is required"):
        _entry(event_id="")


def REDACTED():
    with pytest.raises(ValueError, match="event_type is required"):
        _entry(event_type="")


def REDACTED():
    with pytest.raises(ValueError, match="event_datetime must be timezone-aware"):
        _entry(event_datetime=datetime.now())


def REDACTED():
    with pytest.raises(ValueError, match="recorded_at must be timezone-aware"):
        _entry(recorded_at=datetime.now())


def REDACTED():
    with pytest.raises(ValueError, match="sequence must be >= 0"):
        _entry(sequence=-1)


def REDACTED():
    with pytest.raises(ValueError, match="aggregate_version must be >= 1"):
        _entry(aggregate_version=0)


def REDACTED():
    e = _entry()
    d = e.to_dict()
    assert "T" in d["event_datetime"]    # ISO format
    assert d["event_id"] == "ev-1"
    assert d["payload"]["condition_code"] == "TEA_F84.0"


def REDACTED():
    ev = {
        "event_id": "ev-2",
        "sequence": 42,
        "event_type": "ASSESSMENT_APPLIED",
        "aggregate_type": "assessment",
        "aggregate_id": "ass-1",
        "event_datetime": "2026-07-15T10:00:00Z",
        "recorded_at": "2026-07-15T10:05:00Z",
        "aggregate_version": 3,
        "actor_id": "doc-1",
        "payload": {"scale_code": "CARS2"},
        "tenant_id": "t1",
        "patient_id": "p1",
        "correlation_id": "corr-1",
    }
    e = TimelineEntry.from_event(ev)
    assert e.event_id == "ev-2"
    assert e.sequence == 42
    assert e.aggregate_version == 3
    assert e.event_datetime.year == 2026
    assert e.event_datetime.tzinfo is not None
    assert e.tenant_id == "t1"
    assert e.correlation_id == "corr-1"


def REDACTED():
    """Aceita transaction_time/valid_time como aliases."""
    ev = {
        "id": "ev-3",
        "sequence": 1,
        "event_type": "X",
        "aggregate_type": "y",
        "aggregate_id": "z",
        "valid_time": "2026-01-01T00:00:00Z",
        "transaction_time": "2026-01-01T00:00:01Z",
        "aggregate_version": 1,
        "created_by": "actor-1",
    }
    e = TimelineEntry.from_event(ev)
    assert e.event_id == "ev-3"
    assert e.actor_id == "actor-1"


def REDACTED():
    ev = {"id": "x", "sequence": 1, "event_type": "X"}
    with pytest.raises(ValueError):
        TimelineEntry.from_event(ev)


def REDACTED():
    """Sprint 4.2 vai popular episode_id — domain já suporta."""
    e = _entry(episode_id="ep-1")
    assert e.episode_id == "ep-1"


# ─── TimeWindow ───────────────────────────────────────────────────────


def test_timewindow_basic():
    start = _now()
    end = start + timedelta(days=30)
    w = TimeWindow(start=start, end=end, label="month")
    assert w.duration_days == 30.0
    assert w.label == "month"


def test_timewindow_requires_tz_aware():
    with pytest.raises(ValueError, match="timezone-aware"):
        TimeWindow(start=datetime.now(), end=_now())


def REDACTED():
    with pytest.raises(ValueError, match="start must be <= end"):
        TimeWindow(start=_now() + timedelta(days=1), end=_now())


def test_timewindow_contains():
    start = _now()
    end = start + timedelta(days=10)
    w = TimeWindow(start=start, end=end)
    assert w.contains(start)
    assert w.contains(end)
    assert not w.contains(end + timedelta(days=1))


def REDACTED():
    w = TimeWindow(start=_now(), end=_now() + timedelta(days=1))
    assert w.contains(_now())


def test_timewindow_last_days():
    end = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    w = TimeWindow.last_days(7, end=end)
    assert w.duration_days == 7.0
    assert w.end == end
    assert "last_7_days" in (w.label or "")


def test_timewindow_to_dict():
    w = TimeWindow.between(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 12, 31, tzinfo=timezone.utc),
        label="year_2026",
    )
    d = w.to_dict()
    assert d["label"] == "year_2026"
    assert d["duration_days"] > 360


# ─── VariableSpec ─────────────────────────────────────────────────────


def _var(**overrides) -> VariableSpec:
    defaults = dict(
        name="CARS2_total",
        source=VariableSource.EVENT_PAYLOAD,
        source_event_type="ASSESSMENT_APPLIED",
        value_extractor="computed_scores.total",
        unit="points",
        filter_clause={"scale_code": "CARS2"},
    )
    defaults.update(overrides)
    return VariableSpec(**defaults)


def test_variable_spec_basic():
    v = _var()
    assert v.name == "CARS2_total"
    assert v.source_event_type == "ASSESSMENT_APPLIED"


def test_variable_spec_requires_name():
    with pytest.raises(ValueError, match="name is required"):
        _var(name="")


def REDACTED():
    with pytest.raises(ValueError, match="source_event_type is required"):
        _var(source_event_type="")


def REDACTED():
    with pytest.raises(ValueError, match="value_extractor is required"):
        _var(value_extractor="")


def test_variable_spec_matches_filter():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "CARS2", "computed_scores": {"total": 32}},
    }
    assert v.matches(event)


def REDACTED():
    v = _var()
    assert not v.matches({"event_type": "DIAGNOSIS_CONFIRMED", "payload": {}})


def REDACTED():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "ATEC", "computed_scores": {"total": 32}},
    }
    assert not v.matches(event)


def test_variable_spec_extract_value():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "CARS2", "computed_scores": {"total": 32.5}},
    }
    assert v.extract_value(event) == 32.5


def REDACTED():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "CARS2", "computed_scores": {}},
    }
    assert v.extract_value(event) is None


def REDACTED():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "CARS2", "computed_scores": {"total": "high"}},
    }
    assert v.extract_value(event) is None


def REDACTED():
    v = _var()
    event = {
        "event_type": "ASSESSMENT_APPLIED",
        "payload": {"scale_code": "ATEC", "computed_scores": {"total": 32}},
    }
    assert v.extract_value(event) is None


def test_variable_spec_to_dict():
    v = _var(description="total score")
    d = v.to_dict()
    assert d["name"] == "CARS2_total"
    assert d["unit"] == "points"
    assert d["description"] == "total score"
    assert d["filter_clause"] == {"scale_code": "CARS2"}