"""
Testes dos helpers internos do store (via SqlAlchemy store).

Cobre funções utilitárias:
    - _matches (wildcard support)
    - _sort_events
    - _isoformat, _parse_iso
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from araos.clinical.event_store.store import (
    SqlAlchemyClinicalEventStore,
    _isoformat,
    _matches,
    _parse_iso,
    _sort_events,
)


# ═══════════════════════════════════════════════════════════════════════
# _matches
# ═══════════════════════════════════════════════════════════════════════


class TestMatches:
    def test_exact_match(self):
        assert _matches("SCALE_APPLIED", "SCALE_APPLIED") is True

    def test_no_match(self):
        assert _matches("SCALE_APPLIED", "DIAGNOSIS_ADDED") is False

    def test_wildcard_match(self):
        assert _matches("DIAGNOSIS_ADDED", "DIAGNOSIS_*") is True

    def test_wildcard_no_match(self):
        assert _matches("SCALE_APPLIED", "DIAGNOSIS_*") is False

    def REDACTED(self):
        # Wildcard segue semântica SQL LIKE: '*' inclui sequência vazia.
        assert _matches("DIAGNOSIS_", "DIAGNOSIS_*") is True

    def test_wildcard_partial_prefix(self):
        assert _matches("DIAGNOSIS_ADDED", "DIAG*") is True


# ═══════════════════════════════════════════════════════════════════════
# _sort_events
# ═══════════════════════════════════════════════════════════════════════


class TestSortEvents:
    def _event(self, dt_str: str, created_str: str) -> dict:
        return {
            "event_datetime": dt_str,
            "created_at": created_str,
        }

    def test_asc_default(self):
        events = [
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T10:00:00+00:00"),
            self._event("2026-07-15T09:00:00+00:00", "2026-07-15T09:00:00+00:00"),
        ]
        sorted_events = _sort_events(events, "event_datetime ASC")
        assert sorted_events[0]["event_datetime"].startswith("2026-07-15T09")

    def test_desc(self):
        events = [
            self._event("2026-07-15T09:00:00+00:00", "2026-07-15T09:00:00+00:00"),
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T10:00:00+00:00"),
        ]
        sorted_events = _sort_events(events, "event_datetime DESC")
        assert sorted_events[0]["event_datetime"].startswith("2026-07-15T10")

    def test_created_at_asc(self):
        events = [
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T10:00:00+00:00"),
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T09:00:00+00:00"),
        ]
        sorted_events = _sort_events(events, "created_at ASC")
        assert sorted_events[0]["created_at"].startswith("2026-07-15T09")

    def test_created_at_desc(self):
        events = [
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T09:00:00+00:00"),
            self._event("2026-07-15T10:00:00+00:00", "2026-07-15T10:00:00+00:00"),
        ]
        sorted_events = _sort_events(events, "created_at DESC")
        assert sorted_events[0]["created_at"].startswith("2026-07-15T10")


# ═══════════════════════════════════════════════════════════════════════
# _isoformat
# ═══════════════════════════════════════════════════════════════════════


class TestIsoformat:
    def test_naive_becomes_utc(self):
        dt = datetime(2026, 7, 15, 10, 0)
        result = _isoformat(dt)
        assert "+00:00" in result

    def test_aware_preserved(self):
        dt = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)
        result = _isoformat(dt)
        assert "+00:00" in result
        assert "2026-07-15" in result


# ═══════════════════════════════════════════════════════════════════════
# _parse_iso
# ═══════════════════════════════════════════════════════════════════════


class TestParseIso:
    def test_valid_iso(self):
        result = _parse_iso("2026-07-15T10:00:00+00:00")
        assert result is not None
        assert result.year == 2026

    def test_iso_with_z(self):
        result = _parse_iso("2026-07-15T10:00:00Z")
        assert result is not None
        assert result.year == 2026

    def test_empty_returns_none(self):
        assert _parse_iso("") is None

    def test_invalid_returns_none(self):
        assert _parse_iso("not-a-date") is None


# ═══════════════════════════════════════════════════════════════════════
# Publisher: cover the publish_sync vs publish branch
# ═══════════════════════════════════════════════════════════════════════


class TestPublisherBusBranches:
    def REDACTED(self):
        """Cobre o branch publish_sync."""
        from araos.clinical.event_store.publisher import ClinicalEventPublisher
        from araos.clinical.event_store.store import InMemoryClinicalEventStore

        class SyncBus:
            def __init__(self):
                self.called_with = None

            def publish_sync(self, envelope):
                self.called_with = envelope

        bus = SyncBus()
        store = InMemoryClinicalEventStore()
        publisher = ClinicalEventPublisher(store=store, bus=bus)
        publisher.publish(
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert bus.called_with is not None
        assert bus.called_with.event_type == "SCALE_APPLIED"

    def test_publish_with_publish_method(self):
        """Cobre o branch publish (sem publish_sync)."""
        from araos.clinical.event_store.publisher import ClinicalEventPublisher
        from araos.clinical.event_store.store import InMemoryClinicalEventStore

        class AsyncStyleBus:
            def __init__(self):
                self.called_with = None

            def publish(self, envelope):
                self.called_with = envelope
                return "result"  # pode ser coroutine, não importa

        bus = AsyncStyleBus()
        store = InMemoryClinicalEventStore()
        publisher = ClinicalEventPublisher(store=store, bus=bus)
        publisher.publish(
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert bus.called_with is not None

    def REDACTED(self):
        """Cobre o caminho onde bus existe mas não tem publish nem publish_sync."""
        from araos.clinical.event_store.publisher import ClinicalEventPublisher
        from araos.clinical.event_store.store import InMemoryClinicalEventStore

        class EmptyBus:
            pass

        bus = EmptyBus()
        store = InMemoryClinicalEventStore()
        publisher = ClinicalEventPublisher(store=store, bus=bus)
        # Não deve lançar — apenas não chama nada
        eid = publisher.publish(
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert eid is not None
