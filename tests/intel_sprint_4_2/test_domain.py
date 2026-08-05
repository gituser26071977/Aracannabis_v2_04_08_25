"""
Testes unitários — Domain Layer do Clinical Context Engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import (
    ContextRelationship,
    RelationshipType,
)
from araos.clinical.context.domain.context_status import (
    TERMINAL_STATUSES,
    ContextStatus,
    is_terminal,
    requires_confirmation,
    requires_end_date,
)
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.context.domain.rule import ContextSuggestion, Rule
from araos.clinical.timeline.domain.window import TimeWindow


# ─── ContextType ─────────────────────────────────────────────


class TestContextType:
    def test_has_all_ten_types(self):
        assert ContextType.CLINICAL_EPISODE.value == "clinical_episode"
        assert ContextType.MEDICATION_CONTEXT.value == "medication_context"
        assert ContextType.SCHOOL_CONTEXT.value == "school_context"
        assert ContextType.FAMILY_CONTEXT.value == "family_context"
        assert ContextType.ENVIRONMENTAL_CONTEXT.value == "environmental_context"
        assert ContextType.DEVELOPMENTAL_MILESTONE.value == "developmental_milestone"
        assert ContextType.BEHAVIORAL_PHASE.value == "behavioral_phase"
        assert ContextType.SLEEP_PATTERN.value == "sleep_pattern"
        assert ContextType.EDUCATIONAL_TRANSITION.value == "educational_transition"
        assert ContextType.SOCIAL_CONTEXT.value == "social_context"

    def test_count(self):
        assert len(list(ContextType)) == 10


# ─── ContextOrigin + is_automated ────────────────────────────


class TestContextOrigin:
    def test_count(self):
        assert len(list(ContextOrigin)) == 5

    def test_manual_is_not_automated(self):
        assert ContextOrigin.MANUAL.is_automated is False
        assert ContextOrigin.IMPORT.is_automated is False
        assert ContextOrigin.RESEARCH.is_automated is False

    def test_rule_engine_is_automated(self):
        assert ContextOrigin.RULE_ENGINE.is_automated is True

    def REDACTED(self):
        assert ContextOrigin.ARTIFICIAL_INTELLIGENCE.is_automated is True


# ─── ContextStatus state machine ─────────────────────────────


class TestContextStatusStateMachine:
    def test_seven_statuses(self):
        assert len(list(ContextStatus)) == 7

    def REDACTED(self):
        allowed = ContextStatus.valid_transitions()[ContextStatus.PLANNED]
        assert ContextStatus.SUGGESTED in allowed
        assert ContextStatus.ACTIVE in allowed
        assert ContextStatus.CANCELLED in allowed

    def REDACTED(self):
        allowed = ContextStatus.valid_transitions()[ContextStatus.SUGGESTED]
        assert ContextStatus.ACTIVE in allowed
        assert ContextStatus.REJECTED in allowed
        assert ContextStatus.PLANNED in allowed

    def test_valid_transitions_from_active(self):
        allowed = ContextStatus.valid_transitions()[ContextStatus.ACTIVE]
        assert ContextStatus.COMPLETED in allowed
        assert ContextStatus.CANCELLED in allowed
        assert ContextStatus.ARCHIVED in allowed

    def test_only_completed_can_reopen(self):
        allowed = ContextStatus.valid_transitions()[ContextStatus.COMPLETED]
        assert ContextStatus.ACTIVE in allowed
        assert len(allowed) == 1

    def REDACTED(self):
        # COMPLETED → Active é válido (reopen). Só os 3 abaixo são terminal strict.
        for terminal in (ContextStatus.CANCELLED, ContextStatus.ARCHIVED,
                         ContextStatus.REJECTED):
            allowed = ContextStatus.valid_transitions()[terminal]
            assert allowed == set()

    def test_terminal_statuses_frozenset(self):
        # implementa como escrevemos — inclui COMPLETED (reabertura é especial)
        assert TERMINAL_STATUSES == frozenset({
            ContextStatus.COMPLETED,
            ContextStatus.CANCELLED,
            ContextStatus.ARCHIVED,
            ContextStatus.REJECTED,
        })

    def test_is_terminal_helper(self):
        assert is_terminal(ContextStatus.CANCELLED) is True
        assert is_terminal(ContextStatus.PLANNED) is False

    def test_requires_end_date(self):
        assert requires_end_date(ContextStatus.COMPLETED) is True
        assert requires_end_date(ContextStatus.CANCELLED) is True
        assert requires_end_date(ContextStatus.ARCHIVED) is True
        assert requires_end_date(ContextStatus.ACTIVE) is False

    def test_requires_confirmation(self):
        # ACTIVE/COMPLETED exigem confirmed_by
        assert requires_confirmation(ContextStatus.ACTIVE) is True
        assert requires_confirmation(ContextStatus.COMPLETED) is True
        assert requires_confirmation(ContextStatus.PLANNED) is False

    def test_can_transition_to_method(self):
        assert ContextStatus.PLANNED.can_transition_to(ContextStatus.ACTIVE)
        assert not ContextStatus.PLANNED.can_transition_to(ContextStatus.COMPLETED)


# ─── ClinicalContext aggregate ───────────────────────────────


def _make_ctx(**overrides) -> ClinicalContext:
    base = dict(
        context_id="ctx_test_1",
        tenant_id="t1",
        patient_id="p1",
        context_type=ContextType.CLINICAL_EPISODE,
        status=ContextStatus.PLANNED,
        origin=ContextOrigin.MANUAL,
        title="Contexto de teste",
        description="",
        start_date=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
        confidence_score=1.0,
        created_at=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
        created_by="user-1",
    )
    base.update(overrides)
    return ClinicalContext(**base)


class TestClinicalContextCreation:
    def test_minimal_valid_context(self):
        ctx = _make_ctx()
        assert ctx.context_id == "ctx_test_1"
        assert ctx.is_open is True
        assert ctx.aggregate_version == 1

    def test_empty_title_rejected(self):
        with pytest.raises(ValueError, match="title is required"):
            _make_ctx(title="")

    def test_empty_patient_id_rejected(self):
        with pytest.raises(ValueError, match="patient_id is required"):
            _make_ctx(patient_id="")

    def test_empty_tenant_id_rejected(self):
        with pytest.raises(ValueError, match="tenant_id is required"):
            _make_ctx(tenant_id="")

    def test_empty_created_by_rejected(self):
        with pytest.raises(ValueError, match="created_by is required"):
            _make_ctx(created_by="")

    def test_naive_datetime_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            _make_ctx(start_date=datetime(2026, 7, 18, 10, 0))

    def test_end_before_start_rejected(self):
        with pytest.raises(ValueError, match="end_date .* < start_date"):
            _make_ctx(
                end_date=datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="confidence_score must be"):
            _make_ctx(confidence_score=1.5)
        with pytest.raises(ValueError, match="confidence_score must be"):
            _make_ctx(confidence_score=-0.1)

    def REDACTED(self):
        with pytest.raises(ValueError, match="manual origin requires"):
            _make_ctx(origin=ContextOrigin.MANUAL, confidence_score=0.9)

    def test_completed_requires_end_date(self):
        with pytest.raises(ValueError, match="end_date is required for status"):
            _make_ctx(status=ContextStatus.COMPLETED)

    def test_cancelled_requires_end_date(self):
        with pytest.raises(ValueError, match="end_date is required for status"):
            _make_ctx(status=ContextStatus.CANCELLED)

    def test_archived_requires_end_date(self):
        with pytest.raises(ValueError, match="end_date is required for status"):
            _make_ctx(status=ContextStatus.ARCHIVED)

    def REDACTED(self):
        with pytest.raises(ValueError, match="rejected context cannot have confirmed_by"):
            _make_ctx(
                status=ContextStatus.REJECTED,
                end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
                confirmed_by="x",
            )

    def REDACTED(self):
        # MANUAL origin com status SUGGESTED → precisa passar confiança cheia
        # mas conflita com regra manual. Usar IMPORT (não-automated) com baixa
        # confiança não passa na invariante.
        with pytest.raises(ValueError):
            _make_ctx(
                status=ContextStatus.SUGGESTED,
                origin=ContextOrigin.IMPORT,
                confidence_score=0.7,
            )


class REDACTED:
    def test_planned_to_active(self):
        ctx = _make_ctx()
        new_ctx = ctx.transition_to(ContextStatus.ACTIVE, actor_id="doc1")
        assert new_ctx.status == ContextStatus.ACTIVE
        assert new_ctx.confirmed_by == "doc1"
        assert new_ctx.confirmed_at is not None
        assert new_ctx.aggregate_version == ctx.aggregate_version + 1

    def test_planned_to_cancelled(self):
        ctx = _make_ctx()
        end = datetime(2026, 7, 19, tzinfo=timezone.utc)
        new_ctx = ctx.transition_to(
            ContextStatus.CANCELLED, actor_id="doc1", end_date=end,
        )
        assert new_ctx.status == ContextStatus.CANCELLED
        assert new_ctx.end_date == end

    def test_invalid_transition_raises(self):
        ctx = _make_ctx()
        with pytest.raises(ValueError, match="invalid transition"):
            ctx.transition_to(
                ContextStatus.COMPLETED,
                actor_id="doc1",
                end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
            )

    def test_completed_reopens_to_active(self):
        ctx = _make_ctx(
            status=ContextStatus.COMPLETED,
            end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
        )
        new_ctx = ctx.transition_to(ContextStatus.ACTIVE, actor_id="doc1")
        assert new_ctx.status == ContextStatus.ACTIVE

    def REDACTED(self):
        ctx = _make_ctx(
            status=ContextStatus.SUGGESTED,
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.9,
        )
        new_ctx = ctx.transition_to(
            ContextStatus.REJECTED, actor_id="doc1", reason="irrelevante",
        )
        assert new_ctx.status == ContextStatus.REJECTED
        assert new_ctx.rejected_by == "doc1"
        assert new_ctx.rejected_at is not None


class TestClinicalContextTemporal:
    def test_is_active_on_before_start(self):
        ctx = _make_ctx()
        before = ctx.start_date - timedelta(days=1)
        assert ctx.is_active_on(before) is False

    def test_is_active_on_at_start(self):
        ctx = _make_ctx()
        assert ctx.is_active_on(ctx.start_date) is True

    def test_is_active_on_inside_window(self):
        ctx = _make_ctx(
            end_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )
        middle = ctx.start_date + timedelta(days=1)
        assert ctx.is_active_on(middle) is True

    def test_is_active_on_after_end(self):
        ctx = _make_ctx(
            end_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
            status=ContextStatus.COMPLETED,
        )
        after = ctx.end_date + timedelta(days=1)
        assert ctx.is_active_on(after) is False

    def test_is_active_on_terminal_status(self):
        ctx = _make_ctx(
            status=ContextStatus.CANCELLED,
            end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
        )
        assert ctx.is_active_on(ctx.start_date + timedelta(hours=1)) is False

    def test_duration_days_with_end(self):
        # 18/07 10:00 → 28/07 10:00 = exatamente 10 dias
        ctx = _make_ctx(
            end_date=datetime(2026, 7, 28, 10, 0, tzinfo=timezone.utc),
        )
        assert ctx.duration_days == pytest.approx(10.0, abs=0.01)

    def test_duration_days_without_end(self):
        ctx = _make_ctx()
        assert ctx.duration_days is None

    def test_link_entity_idempotent(self):
        ctx = _make_ctx()
        ctx2 = ctx.link_entity("event", "e1")
        ctx3 = ctx2.link_entity("event", "e1")
        assert ctx2.linked_event_ids == ["e1"]
        assert ctx3.linked_event_ids == ["e1"]

    def test_unlink_entity(self):
        ctx = _make_ctx().link_entity("event", "e1").link_entity("event", "e2")
        new_ctx = ctx.unlink_entity("event", "e1")
        assert new_ctx.linked_event_ids == ["e2"]

    def test_link_invalid_entity_kind(self):
        ctx = _make_ctx()
        with pytest.raises(ValueError, match="unsupported entity_kind"):
            ctx.link_entity("nonexistent", "x")


class TestClinicalContextSerialization:
    def test_to_dict_round_trip(self):
        ctx = _make_ctx(
            description="test",
            reason="because",
            observations=["a", "b"],
            source_event_ids=["e1", "e2"],
            linked_diagnosis_ids=["d1"],
            professionals=["doc1"],
            suggestion_id="sug_x",
        )
        d = ctx.to_dict()
        assert d["context_id"] == "ctx_test_1"
        assert d["context_type"] == "clinical_episode"
        # Status values are Title-cased ("Planned")
        assert d["status"] == "Planned"
        assert d["origin"] == "manual"
        assert d["observations"] == ["a", "b"]
        assert d["source_event_ids"] == ["e1", "e2"]
        assert d["linked_diagnosis_ids"] == ["d1"]
        assert d["suggestion_id"] == "sug_x"
        assert d["is_open"] is True
        assert "start_date" in d
        assert isinstance(d["start_date"], str)


# ─── ContextRelationship ────────────────────────────────────


class TestContextRelationship:
    def _make_rel(self, **overrides):
        base = dict(
            relationship_id="r1",
            tenant_id="t1",
            source_context_id="c1",
            target_context_id="c2",
            relationship_type=RelationshipType.INFLUENCED,
            confidence=0.8,
            created_at=datetime.now(timezone.utc),
            created_by="user1",
        )
        base.update(overrides)
        return ContextRelationship(**base)

    def test_create_valid(self):
        rel = self._make_rel()
        assert rel.relationship_type == RelationshipType.INFLUENCED
        assert rel.confidence == 0.8

    def test_self_loop_rejected(self):
        with pytest.raises(ValueError, match="self-loop"):
            self._make_rel(target_context_id="c1")

    def test_confidence_out_of_range(self):
        with pytest.raises(ValueError, match="confidence"):
            self._make_rel(confidence=1.5)

    def test_negative_confidence_rejected(self):
        with pytest.raises(ValueError, match="confidence"):
            self._make_rel(confidence=-0.1)

    def test_naive_datetime_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            self._make_rel(created_at=datetime.now())

    def REDACTED(self):
        with pytest.raises(ValueError, match="relationship_id"):
            self._make_rel(relationship_id="")

    def test_empty_tenant_id_rejected(self):
        with pytest.raises(ValueError, match="tenant_id"):
            self._make_rel(tenant_id="")

    def test_empty_source_rejected(self):
        with pytest.raises(ValueError, match="source_context_id"):
            self._make_rel(source_context_id="")

    def test_empty_target_rejected(self):
        with pytest.raises(ValueError, match="target_context_id"):
            self._make_rel(target_context_id="")

    def test_empty_created_by_rejected(self):
        with pytest.raises(ValueError, match="created_by"):
            self._make_rel(created_by="")

    def test_relationship_types_count(self):
        assert len(list(RelationshipType)) == 6

    def test_to_dict(self):
        rel = self._make_rel(evidence_event_ids=["e1", "e2"])
        d = rel.to_dict()
        assert d["relationship_id"] == "r1"
        assert d["relationship_type"] == "influenced"
        assert d["evidence_event_ids"] == ["e1", "e2"]


# ─── Rule ABC + ContextSuggestion ────────────────────────────


class TestRuleABC:
    def test_rule_must_implement_evaluate(self):
        class BadRule(Rule):
            rule_id = "bad"

        with pytest.raises(TypeError):
            BadRule()

    def test_concrete_rule(self):
        class GoodRule(Rule):
            rule_id = "test_rule"
            description = "test"
            min_confidence = 0.5

            def evaluate(self, events, existing_contexts):
                return [
                    ContextSuggestion(
                        suggestion_id="s1",
                        context_type=ContextType.CLINICAL_EPISODE,
                        title="suggestion",
                        description="desc",
                        reason="because",
                        confidence=0.7,
                        rule_id=self.rule_id,
                        contributing_event_ids=["e1"],
                        suggested_window=TimeWindow(
                            start=datetime(2026, 7, 1, tzinfo=timezone.utc),
                            end=datetime(2026, 7, 8, tzinfo=timezone.utc),
                        ),
                        assumptions=["a"],
                        limitations=["l"],
                    ),
                ]

        rule = GoodRule()
        result = rule.evaluate([], [])
        assert len(result) == 1
        assert result[0].context_type == ContextType.CLINICAL_EPISODE

    def test_context_suggestion_invariants(self):
        with pytest.raises(ValueError, match="contributing_event_ids"):
            ContextSuggestion(
                suggestion_id="s1",
                context_type=ContextType.CLINICAL_EPISODE,
                title="t",
                description="d",
                reason="r",
                confidence=0.7,
                rule_id="r",
                contributing_event_ids=[],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=["l"],
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="confidence"):
            ContextSuggestion(
                suggestion_id="s1",
                context_type=ContextType.CLINICAL_EPISODE,
                title="t",
                description="d",
                reason="r",
                confidence=1.5,
                rule_id="r",
                contributing_event_ids=["e1"],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=["l"],
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="limitations"):
            ContextSuggestion(
                suggestion_id="s1",
                context_type=ContextType.CLINICAL_EPISODE,
                title="t",
                description="d",
                reason="r",
                confidence=0.7,
                rule_id="r",
                contributing_event_ids=["e1"],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=[],
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="suggestion_id"):
            ContextSuggestion(
                suggestion_id="",
                context_type=ContextType.CLINICAL_EPISODE,
                title="t",
                description="d",
                reason="r",
                confidence=0.7,
                rule_id="r",
                contributing_event_ids=["e1"],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=["l"],
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="rule_id"):
            ContextSuggestion(
                suggestion_id="s1",
                context_type=ContextType.CLINICAL_EPISODE,
                title="t",
                description="d",
                reason="r",
                confidence=0.7,
                rule_id="",
                contributing_event_ids=["e1"],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=["l"],
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="title"):
            ContextSuggestion(
                suggestion_id="s1",
                context_type=ContextType.CLINICAL_EPISODE,
                title="",
                description="d",
                reason="r",
                confidence=0.7,
                rule_id="r",
                contributing_event_ids=["e1"],
                suggested_window=TimeWindow(
                    start=datetime.now(timezone.utc),
                    end=datetime.now(timezone.utc),
                ),
                assumptions=["a"],
                limitations=["l"],
            )

    def REDACTED(self):
        # limite inferior 0.0 — aceito
        s = ContextSuggestion(
            suggestion_id="s1",
            context_type=ContextType.CLINICAL_EPISODE,
            title="t",
            description="d",
            reason="r",
            confidence=0.0,
            rule_id="r",
            contributing_event_ids=["e1"],
            suggested_window=TimeWindow(
                start=datetime.now(timezone.utc),
                end=datetime.now(timezone.utc),
            ),
            assumptions=["a"],
            limitations=["l"],
        )
        assert s.confidence == 0.0

    def test_context_suggestion_to_dict(self):
        s = ContextSuggestion(
            suggestion_id="s1",
            context_type=ContextType.MEDICATION_CONTEXT,
            title="t",
            description="d",
            reason="r",
            confidence=0.7,
            rule_id="r",
            contributing_event_ids=["e1"],
            suggested_window=TimeWindow(
                start=datetime(2026, 7, 1, tzinfo=timezone.utc),
                end=datetime(2026, 7, 8, tzinfo=timezone.utc),
            ),
            assumptions=["a"],
            limitations=["l"],
        )
        d = s.to_dict()
        assert d["suggestion_id"] == "s1"
        assert d["context_type"] == "medication_context"
        assert d["confidence"] == 0.7
        assert d["contributing_event_ids"] == ["e1"]
        assert d["suggested_window"]["start"] == "2026-07-01T00:00:00+00:00"


# ─── TimeWindow dependency ──────────────────────────────────


class TestTimeWindow:
    def test_timewindow_creation(self):
        w = TimeWindow(
            start=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end=datetime(2026, 7, 8, tzinfo=timezone.utc),
            label="test",
        )
        assert w.label == "test"

    def test_timewindow_naive_rejected(self):
        with pytest.raises(ValueError):
            TimeWindow(
                start=datetime(2026, 7, 1),
                end=datetime(2026, 7, 8, tzinfo=timezone.utc),
            )
