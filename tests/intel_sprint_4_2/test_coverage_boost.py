"""
Testes adicionais — cobrem handlers.py e active_projection.py para ≥95%.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import pytest
from sqlalchemy import text


def _ev(event_type: str, payload: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    base = {
        "id": kwargs.get("event_id", f"e-{event_type}-{kwargs.get('seq', 1)}"),
        "sequence": kwargs.get("seq", 1),
        "tenant_id": kwargs.get("tenant_id", "t1"),
        "patient_id": kwargs.get("patient_id", "p1"),
        "event_type": event_type,
        "event_datetime": "2026-07-18T10:00:00+00:00",
        "source_module": "intelligence",
        "created_at": "2026-07-18T10:00:00+00:00",
        "payload": payload,
    }
    base.update(kwargs)
    return base


# ─── Handlers — direct unit coverage ─────────────────────────────


class TestHandlersDirect:
    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_suggested,
        )
        with session_factory() as s:
            handle_clinical_context_suggested(s, _ev(
                "CLINICAL_CONTEXT_SUGGESTED", {"rule_id": None},
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_suggested,
        )
        # No tenant_id
        with session_factory() as s:
            handle_clinical_context_suggested(s, _ev(
                "CLINICAL_CONTEXT_SUGGESTED", {"rule_id": "r1"},
                tenant_id="",
            ))
            s.commit()

    def REDACTED(
        self, session_factory,
    ):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_suggested,
        )
        ev1 = _ev(
            "CLINICAL_CONTEXT_SUGGESTED",
            {"rule_id": "r1", "suggestion_id": "s1"},
            event_id="ev1", seq=1,
        )
        ev2 = _ev(
            "CLINICAL_CONTEXT_SUGGESTED",
            {"rule_id": "r1", "suggestion_id": "s1"},
            event_id="ev1", seq=1,
        )
        with session_factory() as s:
            handle_clinical_context_suggested(s, ev1)
            s.commit()
            handle_clinical_context_suggested(s, ev2)
            s.commit()

    def test_handle_created_no_context_id(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED", {"context_id": None},
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
        )
        ev = _ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-x",
                "context_type": "clinical_episode",
                "status": "Planned",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
            seq=1,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, ev)
            s.commit()
            handle_clinical_context_created(s, ev)
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            REDACTED,
        )
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_ACTIVATED",
                {"context_id": None, "new_status": "Active"},
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            REDACTED,
        )
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_ACTIVATED",
                {"context_id": "c-x"},
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            REDACTED,
        )
        # First create a context
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-x",
                    "context_type": "clinical_episode",
                    "status": "Planned",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            # Now try invalid status
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_ACTIVATED",
                {"context_id": "c-x", "new_status": "INVALID"},
                seq=2,
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-y",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_CLOSED",
                {
                    "context_id": "c-y",
                    "new_status": "Completed",
                    "end_date": "2026-07-19T10:00:00+00:00",
                    "actor_id": "doc1",
                },
                seq=2,
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-z",
                    "context_type": "clinical_episode",
                    "status": "Suggested",
                    "origin": "rule_engine",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_REJECTED",
                {
                    "context_id": "c-z",
                    "new_status": "Rejected",
                    "actor_id": "doc1",
                },
                seq=2,
            ))
            s.commit()

    def test_handle_updated_no_context(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_updated,
        )
        with session_factory() as s:
            handle_clinical_context_updated(s, _ev(
                "CLINICAL_CONTEXT_UPDATED", {"context_id": None},
            ))
            s.commit()

    def test_handle_updated_full_path(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            handle_clinical_context_updated,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-u",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            handle_clinical_context_updated(s, _ev(
                "CLINICAL_CONTEXT_UPDATED",
                {
                    "context_id": "c-u",
                    "title": "T2",
                    "description": "D2",
                    "observations": ["o1"],
                    "professionals": ["d1"],
                    "linked_event_ids": ["e1"],
                    "linked_diagnosis_ids": [],
                    "linked_phenotype_ids": [],
                    "linked_intervention_ids": [],
                    "linked_outcome_ids": [],
                    "linked_assessment_ids": [],
                    "changed_fields": [
                        "title", "description", "observations", "professionals",
                        "linked_event_ids", "linked_diagnosis_ids",
                        "linked_phenotype_ids", "linked_intervention_ids",
                        "linked_outcome_ids", "linked_assessment_ids",
                    ],
                    "actor_id": "doc1",
                },
                seq=2,
            ))
            s.commit()

    def test_handle_linked_no_rel_id(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_linked,
        )
        with session_factory() as s:
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {"relationship_id": None},
            ))
            s.commit()

    def test_handle_linked_full_path(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_linked,
        )
        with session_factory() as s:
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-x",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                    "confidence": 0.7,
                    "evidence_event_ids": ["e1"],
                    "created_by": "doc1",
                },
            ))
            s.commit()
            # Idempotent: same rel_id
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-x",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                },
            ))
            s.commit()

    def test_handle_unlinked_no_rel_id(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_unlinked,
        )
        with session_factory() as s:
            handle_clinical_context_unlinked(s, _ev(
                "CLINICAL_CONTEXT_UNLINKED",
                {"relationship_id": None},
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_linked,
            handle_clinical_context_unlinked,
        )
        with session_factory() as s:
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-x",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                },
                tenant_id="t1",
            ))
            s.commit()
            handle_clinical_context_unlinked(s, _ev(
                "CLINICAL_CONTEXT_UNLINKED",
                {
                    "relationship_id": "rel-x",
                    "tenant_id": "t2",  # mismatched
                },
                tenant_id="t1",
            ))
            s.commit()

    def test_handle_unlinked_real_path(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_linked,
            handle_clinical_context_unlinked,
        )
        with session_factory() as s:
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-y",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                },
                tenant_id="t1",
            ))
            s.commit()
            handle_clinical_context_unlinked(s, _ev(
                "CLINICAL_CONTEXT_UNLINKED",
                {"relationship_id": "rel-y", "tenant_id": "t1"},
                tenant_id="t1",
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            REDACTED,
        )
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_TYPE_CONFIRMED",
                {"context_id": None},
            ))
            s.commit()

    def test_handle_type_confirmed_full(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-w",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_TYPE_CONFIRMED",
                {
                    "context_id": "c-w",
                    "confirmed_type": "family_context",
                },
                seq=2,
            ))
            s.commit()

    def REDACTED(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-v",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_TYPE_CONFIRMED",
                {
                    "context_id": "c-v",
                    "confirmed_type": "invalid_type",
                },
                seq=2,
            ))
            s.commit()

    def test_coerce_helpers(self):
        from araos.clinical.context.projections.handlers import (
            _coerce_status_value,
            _coerce_type_value,
            _coerce_origin_value,
            _ensure_aware,
        )
        from araos.clinical.context.domain.context_status import ContextStatus
        from araos.clinical.context.domain.context_type import ContextType
        from araos.clinical.context.domain.context_origin import ContextOrigin

        assert _coerce_status_value(None, "default") == "default"
        assert _coerce_status_value("Planned") == ContextStatus.PLANNED.value
        assert _coerce_status_value("INVALID", "fallback") == "fallback"
        assert _coerce_type_value(None) is None
        assert _coerce_type_value("clinical_episode") == ContextType.CLINICAL_EPISODE.value
        assert _coerce_type_value("BOGUS", "x") == "x"
        assert _coerce_origin_value(None) is None
        assert _coerce_origin_value("manual") == ContextOrigin.MANUAL.value
        assert _coerce_origin_value("BOGUS", "y") == "y"
        assert _ensure_aware(None) is None
        assert _ensure_aware("2026-07-18T10:00:00Z") is not None
        assert _ensure_aware("not-a-date") is None
        # Already aware
        aware = datetime(2026, 7, 18, tzinfo=timezone.utc)
        assert _ensure_aware(aware) is aware
        # Naive → becomes aware
        naive = datetime(2026, 7, 18)
        out = _ensure_aware(naive)
        assert out.tzinfo is not None

    def test_get_status_helper(self):
        from araos.clinical.context.projections.handlers import _get_status
        from araos.clinical.context.domain.context_status import ContextStatus

        assert _get_status(None) is None
        assert _get_status(ContextStatus.PLANNED) == ContextStatus.PLANNED
        assert _get_status("Planned") == ContextStatus.PLANNED
        assert _get_status("BOGUS") is None


# ─── Active projection coverage ─────────────────────────────────


class TestActiveProjection:
    def _make(self, session_factory):
        from araos.clinical.context.projections import ActiveContextProjection
        return ActiveContextProjection(session_factory)

    def test_apply_unsupported_event_type(self, session_factory):
        p = self._make(session_factory)
        ev = _ev("UNKNOWN", {"context_id": "c"})
        assert p.apply(ev) is False

    def REDACTED(self, session_factory):
        p = self._make(session_factory)
        ev = _ev("CLINICAL_CONTEXT_CREATED", {"context_id": None})
        ev["tenant_id"] = None
        assert p.apply(ev) is False

    def test_apply_suggested_returns_true(self, session_factory):
        p = self._make(session_factory)
        ev = _ev(
            "CLINICAL_CONTEXT_SUGGESTED",
            {"rule_id": "r1", "context_id": "c1"},
        )
        assert p.apply(ev) is True

    def REDACTED(self, session_factory):
        p = self._make(session_factory)
        ev = _ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c1",
                "context_type": "clinical_episode",
                "status": "Completed",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        )
        assert p.apply(ev) is False

    def test_insert_active(self, session_factory):
        p = self._make(session_factory)
        ev = _ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-active-1",
                "context_type": "clinical_episode",
                "status": "Planned",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        )
        assert p.apply(ev) is True
        items = p.list_active_for_patient("t1", "p1")
        assert any(i["context_id"] == "c-active-1" for i in items)

    def test_resync_to_active(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        p = self._make(session_factory)
        # First insert as Planned
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-rs",
                    "context_type": "clinical_episode",
                    "status": "Planned",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
        # Apply created to active projection
        p.apply(_ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-rs",
                "context_type": "clinical_episode",
                "status": "Planned",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        ))
        # Now activate
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_ACTIVATED",
                {
                    "context_id": "c-rs",
                    "new_status": "Active",
                    "actor_id": "doc1",
                },
                seq=2,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_ACTIVATED",
            {
                "context_id": "c-rs",
                "new_status": "Active",
                "actor_id": "doc1",
            },
        ))
        items = p.list_active_for_patient("t1", "p1")
        assert any(
            i["context_id"] == "c-rs" and i["status"] == "Active"
            for i in items
        )

    def test_resync_to_inactive_removes(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        p = self._make(session_factory)
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-cl",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-cl",
                "context_type": "clinical_episode",
                "status": "Active",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        ))
        # Close
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_CLOSED",
                {
                    "context_id": "c-cl",
                    "new_status": "Completed",
                },
                seq=2,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_CLOSED",
            {
                "context_id": "c-cl",
                "new_status": "Completed",
            },
        ))
        items = p.list_active_for_patient("t1", "p1")
        assert not any(i["context_id"] == "c-cl" for i in items)

    def REDACTED(self, session_factory):
        p = self._make(session_factory)
        ev = _ev(
            "CLINICAL_CONTEXT_ACTIVATED",
            {"context_id": "c-missing", "new_status": "Active"},
        )
        assert p.apply(ev) is False

    def test_rejected_deletes(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        p = self._make(session_factory)
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-rj",
                    "context_type": "clinical_episode",
                    "status": "Suggested",
                    "origin": "rule_engine",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-rj",
                "context_type": "clinical_episode",
                "status": "Suggested",
                "origin": "rule_engine",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        ))
        with session_factory() as s:
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_REJECTED",
                {
                    "context_id": "c-rj",
                    "new_status": "Rejected",
                    "actor_id": "doc1",
                },
                seq=2,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_REJECTED",
            {"context_id": "c-rj", "new_status": "Rejected"},
        ))
        items = p.list_active_for_patient("t1", "p1")
        assert not any(i["context_id"] == "c-rj" for i in items)

    def test_relationship_events_noop(self, session_factory):
        p = self._make(session_factory)
        assert p.apply(_ev(
            "CLINICAL_CONTEXT_LINKED",
            {"relationship_id": "r1", "context_id": "c1"},
        )) is True
        assert p.apply(_ev(
            "CLINICAL_CONTEXT_UNLINKED",
            {"relationship_id": "r1", "context_id": "c1"},
        )) is True

    def test_type_confirmed_resyncs(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
            REDACTED,
        )
        p = self._make(session_factory)
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-tc",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
            REDACTED(s, _ev(
                "CLINICAL_CONTEXT_TYPE_CONFIRMED",
                {
                    "context_id": "c-tc",
                    "confirmed_type": "family_context",
                },
                seq=2,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-tc",
                "context_type": "clinical_episode",
                "status": "Active",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        ))
        p.apply(_ev(
            "CLINICAL_CONTEXT_TYPE_CONFIRMED",
            {
                "context_id": "c-tc",
                "confirmed_type": "family_context",
            },
        ))
        items = p.list_active_for_patient("t1", "p1")
        assert any(
            i["context_id"] == "c-tc" and i["context_type"] == "family_context"
            for i in items
        )

    def test_updated_resyncs(self, session_factory):
        from araos.clinical.context.projections.handlers import (
            handle_clinical_context_created,
        )
        p = self._make(session_factory)
        with session_factory() as s:
            handle_clinical_context_created(s, _ev(
                "CLINICAL_CONTEXT_CREATED",
                {
                    "context_id": "c-up",
                    "context_type": "clinical_episode",
                    "status": "Active",
                    "origin": "manual",
                    "title": "T",
                    "start_date": "2026-07-18T10:00:00+00:00",
                },
                seq=1,
            ))
            s.commit()
        p.apply(_ev(
            "CLINICAL_CONTEXT_CREATED",
            {
                "context_id": "c-up",
                "context_type": "clinical_episode",
                "status": "Active",
                "origin": "manual",
                "title": "T",
                "start_date": "2026-07-18T10:00:00+00:00",
            },
        ))
        p.apply(_ev(
            "CLINICAL_CONTEXT_UPDATED",
            {"context_id": "c-up", "title": "T2", "changed_fields": ["title"]},
        ))

    def test_list_active_for_patient_empty(self, session_factory):
        p = self._make(session_factory)
        items = p.list_active_for_patient("t-unknown", "p-unknown")
        assert items == []


# ─── Query module coverage ─────────────────────────────────────


class TestInMemoryQuery:
    """Cobertura: cria contextos via construtor, não mexer em _by_patient."""

    def _ctx(self, ctx_id, **kw):
        from araos.clinical.context.domain.clinical_context import ClinicalContext
        from araos.clinical.context.domain.context_status import ContextStatus
        from araos.clinical.context.domain.context_type import ContextType
        from araos.clinical.context.domain.context_origin import ContextOrigin
        defaults = dict(
            context_id=ctx_id, tenant_id="t1", patient_id="p1",
            context_type=ContextType.CLINICAL_EPISODE,
            status=ContextStatus.ACTIVE, origin=ContextOrigin.MANUAL,
            title=ctx_id,
            start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            confidence_score=1.0,
            created_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
            created_by="d1",
        )
        defaults.update(kw)
        return ClinicalContext(**defaults)

    def test_for_patient_basic(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        q = InMemoryClinicalContextQuery([
            self._ctx("c1"),
            self._ctx("c2", patient_id="p2"),
        ])
        out = q.for_patient("t1", "p1")
        assert len(out) == 1
        assert out[0].context_id == "c1"

    def test_for_patient_filters(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        from araos.clinical.context.domain.context_status import ContextStatus
        from araos.clinical.context.domain.context_type import ContextType
        q = InMemoryClinicalContextQuery([
            self._ctx("c1", status=ContextStatus.ACTIVE),
            self._ctx(
                "c2",
                status=ContextStatus.COMPLETED,
                end_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
            ),
        ])
        out = q.for_patient("t1", "p1", status=ContextStatus.COMPLETED)
        assert len(out) == 1
        assert out[0].context_id == "c2"
        out = q.for_patient("t1", "p1", context_type=ContextType.CLINICAL_EPISODE)
        assert len(out) == 2

    def test_get(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        q = InMemoryClinicalContextQuery([self._ctx("c1")])
        assert q.get("t1", "c1").context_id == "c1"
        assert q.get("t1", "missing") is None
        assert q.get("t2", "c1") is None

    def test_active_at(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        from araos.clinical.context.domain.context_status import ContextStatus
        q = InMemoryClinicalContextQuery([
            self._ctx(
                "c1",
                status=ContextStatus.COMPLETED,
                start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
            ),
        ])
        out = q.active_at("t1", "p1", datetime(2026, 7, 15, tzinfo=timezone.utc))
        assert any(c.context_id == "c1" for c in out)

    def test_co_occurred(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        from araos.clinical.context.domain.context_type import ContextType
        q = InMemoryClinicalContextQuery([
            self._ctx(
                "c1",
                start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 7, 10, tzinfo=timezone.utc),
            ),
            self._ctx(
                "c2",
                context_type=ContextType.SLEEP_PATTERN,
                start_date=datetime(2026, 7, 5, tzinfo=timezone.utc),
                end_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            ),
        ])
        pairs = q.co_occurred(
            "t1", "p1",
            datetime(2026, 7, 1, tzinfo=timezone.utc),
            datetime(2026, 7, 10, tzinfo=timezone.utc),
        )
        assert len(pairs) >= 1

    def test_influenced_outcome(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        q = InMemoryClinicalContextQuery([
            self._ctx("c1", linked_outcome_ids=["o1"]),
            self._ctx("c2"),
        ])
        out = q.influenced_outcome("t1", "o1")
        assert any(c.context_id == "c1" for c in out)

    def REDACTED(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        q = InMemoryClinicalContextQuery([self._ctx("c1")])
        out = q.preceded_improvement("t1", "p1")
        assert out == []

    def REDACTED(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        from araos.clinical.context.domain.context_status import ContextStatus
        q = InMemoryClinicalContextQuery([
            self._ctx(
                "c1",
                status=ContextStatus.COMPLETED,
                start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 7, 25, tzinfo=timezone.utc),
            ),
        ])
        q.set_events([{
            "event_type": "OUTCOME_IMPROVEMENT",
            "tenant_id": "t1",
            "patient_id": "p1",
            "event_datetime": datetime(2026, 7, 30, tzinfo=timezone.utc),
        }])
        out = q.preceded_improvement("t1", "p1")
        assert any(c.context_id == "c1" for c in out)

    def test_active_during_no_events(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        q = InMemoryClinicalContextQuery([self._ctx("c1")])
        out = q.active_during("t1", "interv1")
        assert out == []

    def REDACTED(self):
        from araos.clinical.context.application.query import (
            InMemoryClinicalContextQuery,
        )
        # Context must overlap with intervention window [Jul 5, Jul 25].
        q = InMemoryClinicalContextQuery([
            self._ctx(
                "c1",
                patient_id="p1",
                start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 7, 30, tzinfo=timezone.utc),
            ),
        ])
        q.set_events([
            {
                "event_type": "INTERVENTION_STARTED",
                "tenant_id": "t1",
                "patient_id": "p1",
                "aggregate_id": "interv1",
                "event_datetime": datetime(2026, 7, 5, tzinfo=timezone.utc),
            },
            {
                "event_type": "INTERVENTION_STOPPED",
                "tenant_id": "t1",
                "aggregate_id": "interv1",
                "event_datetime": datetime(2026, 7, 25, tzinfo=timezone.utc),
            },
        ])
        out = q.active_during("t1", "interv1")
        assert any(c.context_id == "c1" for c in out)


# ─── Service coverage ──────────────────────────────────────────


class TestServiceEdgeCases:
    def REDACTED(self):
        from araos.clinical.context.application.context_service import (
            ClinicalContextService,
            CreateContextCommand,
        )
        from araos.clinical.context.domain.context_type import ContextType

        class BrokenPub:
            def publish(self, **kwargs):
                raise RuntimeError("boom")

        svc = ClinicalContextService(event_publisher=BrokenPub())
        cmd = CreateContextCommand(
            tenant_id="t1", patient_id="p1",
            context_type=ContextType.CLINICAL_EPISODE,
            title="T",
            start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            created_by="d1",
        )
        ctx = svc.create(cmd)
        assert ctx is not None


# ─── Relationship projection coverage ──────────────────────────


class TestRelationshipProjectionCoverage:
    def _make(self, session_factory):
        from araos.clinical.context.projections import RelationshipProjection
        return RelationshipProjection(session_factory)

    def test_apply_unsupported_event(self, session_factory):
        p = self._make(session_factory)
        assert p.apply(_ev("UNKNOWN", {})) is False

    def test_apply_linked_and_unlinked(self, session_factory):
        p = self._make(session_factory)
        # linked
        ev_link = _ev(
            "CLINICAL_CONTEXT_LINKED",
            {
                "relationship_id": "rel-r",
                "source_context_id": "c1",
                "target_context_id": "c2",
                "relationship_type": "influenced",
                "confidence": 0.8,
                "created_by": "d1",
            },
            tenant_id="t1",
        )
        assert p.apply(ev_link) is True
        # unlinked
        ev_un = _ev(
            "CLINICAL_CONTEXT_UNLINKED",
            {"relationship_id": "rel-r", "tenant_id": "t1"},
            tenant_id="t1",
        )
        assert p.apply(ev_un) is True

    def REDACTED(self, session_factory):
        p = self._make(session_factory)
        # Outgoing edge
        with session_factory() as s:
            from araos.clinical.context.projections.handlers import (
                handle_clinical_context_linked,
            )
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-out",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                    "confidence": 0.7,
                    "created_by": "d1",
                },
                tenant_id="t1",
            ))
            s.commit()
            # Incoming edge (from c3 → c1)
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-in",
                    "source_context_id": "c3",
                    "target_context_id": "c1",
                    "relationship_type": "related_to",
                    "confidence": 0.6,
                    "created_by": "d1",
                },
                tenant_id="t1",
            ))
            s.commit()
        items = p.list_for_context("t1", "c1")
        assert len(items) == 2

    def test_neighbors_depth_zero(self, session_factory):
        p = self._make(session_factory)
        with session_factory() as s:
            from araos.clinical.context.projections.handlers import (
                handle_clinical_context_linked,
            )
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "rel-1",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                },
                tenant_id="t1",
            ))
            s.commit()
        # depth=0 → no neighbors
        out = p.neighbors("t1", "c1", depth=0)
        assert out == []

    def test_neighbors_depth_two(self, session_factory):
        p = self._make(session_factory)
        with session_factory() as s:
            from araos.clinical.context.projections.handlers import (
                handle_clinical_context_linked,
            )
            for rel in [
                ("r1", "c1", "c2"),
                ("r2", "c2", "c3"),
                ("r3", "c3", "c4"),
            ]:
                handle_clinical_context_linked(s, _ev(
                    "CLINICAL_CONTEXT_LINKED",
                    {
                        "relationship_id": rel[0],
                        "source_context_id": rel[1],
                        "target_context_id": rel[2],
                        "relationship_type": "influenced",
                    },
                    tenant_id="t1",
                ))
                s.commit()
        out = p.neighbors("t1", "c1", depth=2)
        ids = {n["context_id"] for n in out}
        assert "c2" in ids
        assert "c3" in ids
        # c4 is depth=3, should NOT be in result with depth=2
        assert "c4" not in ids

    def test_neighbors_already_visited(self, session_factory):
        p = self._make(session_factory)
        with session_factory() as s:
            from araos.clinical.context.projections.handlers import (
                handle_clinical_context_linked,
            )
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "r-cycle",
                    "source_context_id": "c1",
                    "target_context_id": "c2",
                    "relationship_type": "influenced",
                },
                tenant_id="t1",
            ))
            s.commit()
            handle_clinical_context_linked(s, _ev(
                "CLINICAL_CONTEXT_LINKED",
                {
                    "relationship_id": "r-cycle2",
                    "source_context_id": "c2",
                    "target_context_id": "c1",
                    "relationship_type": "related_to",
                },
                tenant_id="t1",
            ))
            s.commit()
        # Cycle: c1 ↔ c2. Depth=3 shouldn't loop infinitely.
        out = p.neighbors("t1", "c1", depth=3)
        ids = {n["context_id"] for n in out}
        assert ids == {"c2"}

    def test_neighbors_empty(self, session_factory):
        p = self._make(session_factory)
        out = p.neighbors("t1", "nonexistent", depth=2)
        assert out == []

    def test_top_connected_basic(self, session_factory):
        p = self._make(session_factory)
        with session_factory() as s:
            from araos.clinical.context.projections.handlers import (
                handle_clinical_context_linked,
            )
            for i, tgt in enumerate(["c2", "c3", "c4"]):
                handle_clinical_context_linked(s, _ev(
                    "CLINICAL_CONTEXT_LINKED",
                    {
                        "relationship_id": f"r{i}",
                        "source_context_id": "c1",
                        "target_context_id": tgt,
                        "relationship_type": "influenced",
                    },
                    tenant_id="t1",
                ))
                s.commit()
        top = p.top_connected("t1", limit=10)
        assert len(top) >= 1
        assert top[0]["context_id"] == "c1"
        assert top[0]["out_degree"] == 3

    def test_top_connected_empty(self, session_factory):
        p = self._make(session_factory)
        out = p.top_connected("t-empty", limit=10)
        assert out == []