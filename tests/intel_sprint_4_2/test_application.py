"""
Testes unitários — Application Layer (Service + RuleEngine + Suggester + Query).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pytest

from araos.clinical.context.application import (
    ClinicalContextService,
    CreateContextCommand,
    InMemoryClinicalContextQuery,
    RuleEngine,
    RuleEvaluationResult,
    default_rules,
)
from araos.clinical.context.application.builtin_rules import (
    BehavioralCrisisRule,
    CrisisEpisodeRule,
    FamilyEngagementRule,
    MedicationStartRule,
    SchoolTransitionRule,
    SleepPatternRule,
)
from araos.clinical.context.application.rule_engine import Rule
from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import RelationshipType
from araos.clinical.context.domain.context_status import ContextStatus
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.context.domain.rule import ContextSuggestion
from araos.clinical.timeline.domain.window import TimeWindow


def _ctx_kwargs(**overrides) -> Dict[str, Any]:
    base = dict(
        context_id="ctx_x",
        tenant_id="t1",
        patient_id="p1",
        context_type=ContextType.CLINICAL_EPISODE,
        status=ContextStatus.PLANNED,
        origin=ContextOrigin.MANUAL,
        title="t",
        description="",
        start_date=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
        confidence_score=1.0,
        created_at=datetime(2026, 7, 18, 10, 0, tzinfo=timezone.utc),
        created_by="user-1",
    )
    base.update(overrides)
    return base


def _make_ctx(**overrides) -> ClinicalContext:
    return ClinicalContext(**_ctx_kwargs(**overrides))


def _make_suggestion(**overrides) -> ContextSuggestion:
    base = dict(
        suggestion_id="sug_x",
        context_type=ContextType.MEDICATION_CONTEXT,
        title="Início medicação",
        description="desc",
        reason="because",
        confidence=0.9,
        rule_id="test_rule",
        contributing_event_ids=["e1"],
        suggested_window=TimeWindow(
            start=datetime(2026, 7, 18, tzinfo=timezone.utc),
            end=datetime(2026, 10, 18, tzinfo=timezone.utc),
        ),
        supporting_data={},
        assumptions=["a"],
        limitations=["l"],
    )
    base.update(overrides)
    return ContextSuggestion(**base)


# ─── Service: Create ───────────────────────────────────────


class TestClinicalContextServiceCreate:
    def test_create_manual_yields_planned(self, ctx_service):
        ctx = ctx_service.create(CreateContextCommand(
            tenant_id="t1",
            patient_id="p1",
            context_type=ContextType.CLINICAL_EPISODE,
            title="Crise comportamental",
            start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            created_by="doc1",
        ))
        assert ctx.status == ContextStatus.PLANNED
        assert ctx.aggregate_version == 1

    def REDACTED(self, ctx_service):
        ctx = ctx_service.create(CreateContextCommand(
            tenant_id="t1",
            patient_id="p1",
            context_type=ContextType.MEDICATION_CONTEXT,
            title="Sugestão med",
            start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            created_by="system",
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.8,
        ))
        assert ctx.status == ContextStatus.SUGGESTED
        assert ctx.origin == ContextOrigin.RULE_ENGINE

    def REDACTED(self, ctx_service):
        with pytest.raises(ValueError, match="requires confidence_score"):
            ctx_service.create(CreateContextCommand(
                tenant_id="t1",
                patient_id="p1",
                context_type=ContextType.MEDICATION_CONTEXT,
                title="Bug",
                start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
                created_by="system",
                origin=ContextOrigin.RULE_ENGINE,
                confidence_score=1.0,
            ))

    def test_create_publishes_event(self, publisher, ctx_service):
        initial_events = publisher.store.append if hasattr(publisher.store, 'append') else None
        # Os eventos são publicados pelo publisher injetado
        ctx = ctx_service.create(CreateContextCommand(
            tenant_id="t1",
            patient_id="p1",
            context_type=ContextType.CLINICAL_EPISODE,
            title="Eps",
            start_date=datetime(2026, 7, 18, tzinfo=timezone.utc),
            created_by="doc1",
        ))
        store = publisher.store
        events = store.query(tenant_id="t1", patient_id="p1")
        assert any(e["event_type"] == "CLINICAL_CONTEXT_CREATED" for e in events)

    def test_create_from_suggestion(self, ctx_service):
        s = _make_suggestion()
        ctx = ctx_service.create_from_suggestion(
            suggestion=s,
            tenant_id="t1",
            patient_id="p1",
            created_by="doc1",
        )
        assert ctx.status == ContextStatus.SUGGESTED
        assert ctx.origin == ContextOrigin.RULE_ENGINE
        assert ctx.confidence_score == 0.9
        assert ctx.suggestion_id == "sug_x"
        assert ctx.source_event_ids == ["e1"]


# ─── Service: Transitions ─────────────────────────────────


class REDACTED:
    def test_activate(self, ctx_service):
        ctx = _make_ctx()
        new_ctx = ctx_service.activate(ctx, actor_id="doc1")
        assert new_ctx.status == ContextStatus.ACTIVE
        assert new_ctx.confirmed_by == "doc1"

    def test_activate_from_active_fails(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.ACTIVE, confirmed_by="doc1")
        with pytest.raises(ValueError):
            ctx_service.activate(ctx, actor_id="doc2")

    def test_close(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.ACTIVE, confirmed_by="doc1")
        new_ctx = ctx_service.close(
            ctx, actor_id="doc1", new_status=ContextStatus.COMPLETED,
            end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
            summary="Patient improved",
        )
        assert new_ctx.status == ContextStatus.COMPLETED
        assert new_ctx.end_date is not None
        assert "closed: Patient improved" in new_ctx.observations

    def test_close_invalid_status(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.ACTIVE, confirmed_by="doc1")
        with pytest.raises(ValueError, match="invalid close status"):
            ctx_service.close(
                ctx, actor_id="doc1", new_status=ContextStatus.ACTIVE,
            )

    def test_reopen_only_completed(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.ACTIVE, confirmed_by="doc1")
        with pytest.raises(ValueError, match="can only reopen"):
            ctx_service.reopen(ctx, actor_id="doc1")

    def test_reopen(self, ctx_service):
        ctx = _make_ctx(
            status=ContextStatus.COMPLETED,
            end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
        )
        new_ctx = ctx_service.reopen(ctx, actor_id="doc1", reason="relapse")
        assert new_ctx.status == ContextStatus.ACTIVE
        assert new_ctx.reason == "relapse"

    def test_reject_only_suggested(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.PLANNED)
        with pytest.raises(ValueError, match="can only reject"):
            ctx_service.reject(ctx, actor_id="doc1", reason="x")

    def test_reject(self, ctx_service):
        ctx = _make_ctx(
            status=ContextStatus.SUGGESTED,
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.8,
        )
        new_ctx = ctx_service.reject(ctx, actor_id="doc1", reason="irrelevante")
        assert new_ctx.status == ContextStatus.REJECTED

    def test_confirm_suggestion(self, ctx_service):
        ctx = _make_ctx(
            status=ContextStatus.SUGGESTED,
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.8,
        )
        new_ctx = ctx_service.confirm_suggestion(ctx, actor_id="doc1")
        assert new_ctx.status == ContextStatus.ACTIVE

    def test_confirm_with_type_override(self, ctx_service):
        ctx = _make_ctx(
            status=ContextStatus.SUGGESTED,
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.8,
        )
        new_ctx = ctx_service.confirm_suggestion(
            ctx, actor_id="doc1",
            confirmed_type=ContextType.FAMILY_CONTEXT,
        )
        assert new_ctx.context_type == ContextType.FAMILY_CONTEXT

    def test_confirm_only_suggested(self, ctx_service):
        ctx = _make_ctx(status=ContextStatus.PLANNED)
        with pytest.raises(ValueError):
            ctx_service.confirm_suggestion(ctx, actor_id="doc1")

    def test_update(self, ctx_service):
        ctx = _make_ctx()
        new_ctx = ctx_service.update(ctx, actor_id="doc1", changes={
            "title": "Novo título",
            "description": "Atualizado",
        })
        assert new_ctx.title == "Novo título"
        assert new_ctx.description == "Atualizado"

    def test_update_terminal_rejected(self, ctx_service):
        # COMPLETED abre para ACTIVE (reopen) — não é terminal pelo property.
        # Use CANCELLED para forçar o caminho terminal strict:
        ctx = _make_ctx(
            status=ContextStatus.CANCELLED,
            end_date=datetime(2026, 7, 19, tzinfo=timezone.utc),
        )
        with pytest.raises(ValueError, match="terminal"):
            ctx_service.update(ctx, actor_id="doc1", changes={"title": "x"})

    def test_update_filters_invalid_fields(self, ctx_service):
        ctx = _make_ctx()
        # Passando campo não permitido — sem efeito, retorna mesmo contexto
        new_ctx = ctx_service.update(
            ctx, actor_id="doc1",
            changes={"forbidden_field": "x"},
        )
        assert new_ctx.context_id == ctx.context_id


# ─── Service: Relationships ───────────────────────────────


class REDACTED:
    def test_link(self, ctx_service):
        rel = ctx_service.link(
            tenant_id="t1",
            source_context_id="c1",
            target_context_id="c2",
            relationship_type=RelationshipType.INFLUENCED,
            created_by="doc1",
            evidence_event_ids=["e1"],
            patient_id="p1",
        )
        assert rel.relationship_type == RelationshipType.INFLUENCED
        assert rel.evidence_event_ids == ["e1"]

    def test_unlink_publishes_event(self, ctx_service, publisher):
        rel = ctx_service.link(
            tenant_id="t1",
            source_context_id="c1",
            target_context_id="c2",
            relationship_type=RelationshipType.RELATED_TO,
            created_by="doc1",
            patient_id="p1",
        )
        ctx_service.unlink(rel, actor_id="doc1", patient_id="p1")
        events = publisher.store.query(tenant_id="t1")
        assert any(e["event_type"] == "CLINICAL_CONTEXT_UNLINKED" for e in events)


# ─── Rule Engine ──────────────────────────────────────────


class TestRuleEngine:
    def test_defaults_loads_6_rules(self):
        rules = default_rules()
        assert len(rules) == 6
        rule_ids = {r.rule_id for r in rules}
        assert "medication_start" in rule_ids
        assert "school_change" in rule_ids
        assert "family_meeting" in rule_ids
        assert "crisis_event" in rule_ids
        assert "behavioral_crisis" in rule_ids
        assert "sleep_pattern" in rule_ids

    def test_evaluate_with_no_events(self, rule_engine):
        result = rule_engine.evaluate("t1", "p1", [], [])
        assert result.suggestions == []
        assert result.rules_evaluated == 6
        assert result.events_analyzed == 0

    def test_evaluate_medication_start(self, rule_engine):
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"medication_name": "Risperidona"},
        }]
        result = rule_engine.evaluate("t1", "p1", events, [])
        assert any(
            s.context_type == ContextType.MEDICATION_CONTEXT
            for s in result.suggestions
        )

    def test_evaluate_crisis_event(self, rule_engine):
        events = [{
            "event_id": "e1",
            "event_type": "CRISIS_RECORDED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {},
        }]
        result = rule_engine.evaluate("t1", "p1", events, [])
        assert any(
            s.context_type == ContextType.CLINICAL_EPISODE
            for s in result.suggestions
        )

    def test_evaluate_school_change(self, rule_engine):
        events = [{
            "event_id": "e1",
            "event_type": "SCHOOL_CHANGED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"from_school": "Escola A", "to_school": "Escola B"},
        }]
        result = rule_engine.evaluate("t1", "p1", events, [])
        assert any(
            s.context_type == ContextType.SCHOOL_CONTEXT
            for s in result.suggestions
        )

    def REDACTED(self, rule_engine):
        # 2+ OUTCOME_WORSENING em 14d
        from datetime import datetime, timedelta, timezone
        base = datetime(2026, 7, 1, tzinfo=timezone.utc)
        events = []
        for i in range(2):
            dt = base + timedelta(days=i * 5)
            events.append({
                "event_id": f"e{i}",
                "event_type": "OUTCOME_WORSENING",
                "event_datetime": dt.isoformat(),
                "patient_id": "p1",
                "tenant_id": "t1",
                "payload": {},
            })
        result = rule_engine.evaluate("t1", "p1", events, [])
        # Pode vir clustered — checa que sugestão existe
        s = next(
            (s for s in result.suggestions
             if s.context_type == ContextType.CLINICAL_EPISODE
             and "comportamental" in s.title.lower()),
            None,
        )
        assert s is not None

    def REDACTED(self, rule_engine):
        # 3+ SLEEP_CHANGED em 30d
        from datetime import datetime, timedelta, timezone
        base = datetime(2026, 7, 1, tzinfo=timezone.utc)
        events = []
        for i in range(3):
            dt = base + timedelta(days=i * 7)
            events.append({
                "event_id": f"e{i}",
                "event_type": "SLEEP_CHANGED",
                "event_datetime": dt.isoformat(),
                "patient_id": "p1",
                "tenant_id": "t1",
                "payload": {},
            })
        result = rule_engine.evaluate("t1", "p1", events, [])
        sleep_sug = next(
            (s for s in result.suggestions
             if s.context_type == ContextType.SLEEP_PATTERN),
            None,
        )
        assert sleep_sug is not None

    def test_register_custom_rule(self, rule_engine):
        class CustomRule(Rule):
            rule_id = "custom"
            description = "test"
            min_confidence = 0.5

            def evaluate(self, events, contexts):
                return [
                    _make_suggestion(
                        suggestion_id="sug_custom",
                        title="Custom",
                    ),
                ]

        rule_engine.register(CustomRule())
        result = rule_engine.evaluate("t1", "p1", [{}], [])
        assert any(s.suggestion_id == "sug_custom" for s in result.suggestions)

    def REDACTED(self, rule_engine):
        class LowConfRule(Rule):
            rule_id = "low_conf"
            description = "low"
            min_confidence = 0.9

            def evaluate(self, events, contexts):
                return [
                    _make_suggestion(
                        suggestion_id="low",
                        title="low",
                        confidence=0.7,
                    ),
                ]

        engine = RuleEngine(rules=[LowConfRule()])
        result = engine.evaluate("t1", "p1", [{}], [])
        # 0.7 < min_confidence 0.9 → filtrada
        assert all(s.suggestion_id != "low" for s in result.suggestions)

    def test_evaluate_deduplication(self, rule_engine):
        """Mesma (type, events) dedup → 1 sugestão."""
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"medication_name": "Risperidona"},
        }]
        result = rule_engine.evaluate("t1", "p1", events, [])
        med_sug = [s for s in result.suggestions
                   if s.context_type == ContextType.MEDICATION_CONTEXT]
        assert len(med_sug) == 1

    def REDACTED(self, rule_engine):
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"medication_name": "Risperidona"},
        }]
        existing = [_make_ctx(
            context_type=ContextType.MEDICATION_CONTEXT,
            source_event_ids=["e1"],
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.95,
            status=ContextStatus.SUGGESTED,
        )]
        result = rule_engine.evaluate("t1", "p1", events, existing)
        med_sug = [s for s in result.suggestions
                   if s.context_type == ContextType.MEDICATION_CONTEXT]
        assert med_sug == []


class TestRuleEvaluationResult:
    def test_to_dict(self):
        r = RuleEvaluationResult(
            tenant_id="t1",
            patient_id="p1",
            suggestions=[
                _make_suggestion(),
            ],
            rules_evaluated=6,
            rules_fired=["medication_start"],
            events_analyzed=5,
            contexts_considered=2,
        )
        d = r.to_dict()
        assert d["n_suggestions"] == 1
        assert d["rules_evaluated"] == 6
        assert "suggestions" in d


# ─── Suggester ─────────────────────────────────────────────


class TestContextSuggester:
    def test_suggest_creates_explanations(self, suggester, suggestion_registry):
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"medication_name": "CBD 50mg"},
        }]
        suggestions = suggester.suggest("t1", "p1", events, [], analyst="doc1")
        assert len(suggestions) >= 1
        # Explanation registrada
        all_exps = []
        for t in [suggester._registry]:
            # type: ignore
            pass
        # registry count increment
        assert suggestion_registry.count("t1") >= 1

    def test_suggest_without_publisher(self, rule_engine, suggestion_registry):
        from araos.clinical.context.application import ContextSuggester
        sg = ContextSuggester(
            rule_engine=rule_engine,
            explanation_registry=suggestion_registry,
            event_publisher=None,
        )
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {"medication_name": "X"},
        }]
        result = sg.suggest("t1", "p1", events, [])
        assert isinstance(result, list)

    def test_suggest_no_matches(self, suggester):
        events = [{
            "event_id": "e_unknown",
            "event_type": "SOMETHING_UNKNOWN",
            "event_datetime": "2026-07-18T10:00:00Z",
            "patient_id": "p1",
            "tenant_id": "t1",
            "payload": {},
        }]
        result = suggester.suggest("t1", "p1", events, [])
        assert result == []


# ─── Query ───────────────────────────────────────────────


class TestInMemoryClinicalContextQuery:
    def test_for_patient_filters(self, inmem_query):
        c1 = _make_ctx(context_id="c1", patient_id="p1",
                       status=ContextStatus.PLANNED)
        c2 = _make_ctx(context_id="c2", patient_id="p1",
                       status=ContextStatus.ACTIVE, confirmed_by="d1")
        c3 = _make_ctx(context_id="c3", patient_id="p2",
                       status=ContextStatus.PLANNED)
        for c in (c1, c2, c3):
            inmem_query.add(c)

        result = inmem_query.for_patient("t1", "p1")
        assert {c.context_id for c in result} == {"c1", "c2"}

        result_status = inmem_query.for_patient("t1", "p1", status=ContextStatus.PLANNED)
        assert {c.context_id for c in result_status} == {"c1"}

    def test_get_returns_none_when_missing(self, inmem_query):
        assert inmem_query.get("t1", "missing") is None

    def test_active_at(self, inmem_query):
        ctx = _make_ctx(
            context_id="c1",
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 30, tzinfo=timezone.utc),
            status=ContextStatus.ACTIVE, confirmed_by="d1",
        )
        inmem_query.add(ctx)
        result = inmem_query.active_at("t1", "p1", datetime(2026, 7, 15, tzinfo=timezone.utc))
        assert len(result) == 1
        result_none = inmem_query.active_at("t1", "p1", datetime(2026, 8, 15, tzinfo=timezone.utc))
        assert result_none == []

    def test_co_occurred(self, inmem_query):
        c1 = _make_ctx(
            context_id="c1",
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 20, tzinfo=timezone.utc),
            status=ContextStatus.COMPLETED,
        )
        c2 = _make_ctx(
            context_id="c2",
            start_date=datetime(2026, 7, 10, tzinfo=timezone.utc),
            status=ContextStatus.ACTIVE, confirmed_by="d1",
        )
        inmem_query.add(c1)
        inmem_query.add(c2)
        pairs = inmem_query.co_occurred(
            "t1", "p1",
            datetime(2026, 7, 12, tzinfo=timezone.utc),
            datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert len(pairs) == 2    # (c1,c2) + (c2,c1)

    def test_influenced_outcome(self, inmem_query):
        ctx = _make_ctx(context_id="c1", linked_outcome_ids=["o1", "o2"])
        inmem_query.add(ctx)
        result = inmem_query.influenced_outcome("t1", "o1")
        assert len(result) == 1
        result_none = inmem_query.influenced_outcome("t1", "o3")
        assert result_none == []

    def test_preceded_improvement(self, inmem_query):
        improvements = [
            {"event_type": "OUTCOME_IMPROVEMENT", "event_datetime": "2026-07-18T10:00:00Z",
             "tenant_id": "t1", "patient_id": "p1", "event_id": "ev1"},
        ]
        inmem_query.set_events(improvements)
        ctx = _make_ctx(
            context_id="c1",
            start_date=datetime(2026, 6, 1, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 10, tzinfo=timezone.utc),
            status=ContextStatus.COMPLETED,
        )
        inmem_query.add(ctx)
        result = inmem_query.preceded_improvement("t1", "p1", window_days=30)
        assert len(result) == 1

    def REDACTED(self, inmem_query):
        inmem_query.set_events([])
        result = inmem_query.preceded_improvement("t1", "p1", window_days=30)
        assert result == []

    def test_active_during(self, inmem_query):
        evs = [{
            "event_type": "INTERVENTION_STARTED",
            "aggregate_id": "intv1",
            "tenant_id": "t1", "patient_id": "p1",
            "event_datetime": "2026-07-01T00:00:00Z",
            "event_id": "e1",
        }]
        inmem_query.set_events(evs)
        ctx = _make_ctx(
            context_id="c1",
            start_date=datetime(2026, 6, 25, tzinfo=timezone.utc),
            status=ContextStatus.ACTIVE, confirmed_by="d1",
        )
        inmem_query.add(ctx)
        result = inmem_query.active_during("t1", "intv1")
        assert len(result) == 1


# ─── Built-in Rules específicos ─────────────────────────────


class TestBuiltinRules:
    def REDACTED(self):
        r = MedicationStartRule()
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {"medication_name": "X"},
        }]
        result = r.evaluate(events, [])
        assert len(result) == 1
        assert result[0].context_type == ContextType.MEDICATION_CONTEXT

    def test_medication_rule_dedup(self):
        r = MedicationStartRule()
        events = [{
            "event_id": "e1",
            "event_type": "MEDICATION_STARTED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {"medication_name": "X"},
        }]
        existing = [_make_ctx(
            context_type=ContextType.MEDICATION_CONTEXT,
            source_event_ids=["e1"],
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=0.9,
            status=ContextStatus.SUGGESTED,
        )]
        result = r.evaluate(events, existing)
        assert result == []

    def REDACTED(self):
        r = CrisisEpisodeRule()
        events = [{
            "event_id": "e1",
            "event_type": "DIAGNOSIS_ADDED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {},
        }]
        assert r.evaluate(events, []) == []

    def test_family_rule_fires(self):
        r = FamilyEngagementRule()
        events = [{
            "event_id": "e1",
            "event_type": "FAMILY_MEETING",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {"topic": "Adesão"},
        }]
        result = r.evaluate(events, [])
        assert len(result) == 1
        assert result[0].confidence == 0.85

    def test_school_rule_fires(self):
        r = SchoolTransitionRule()
        events = [{
            "event_id": "e1",
            "event_type": "SCHOOL_CHANGED",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {"from_school": "A", "to_school": "B"},
        }]
        result = r.evaluate(events, [])
        assert len(result) == 1

    def REDACTED(self):
        r = BehavioralCrisisRule()
        events = [{
            "event_id": "e1",
            "event_type": "OUTCOME_WORSENING",
            "event_datetime": "2026-07-18T10:00:00Z",
            "payload": {},
        }]
        # 1 evento < threshold 2
        assert r.evaluate(events, []) == []

    def test_sleep_pattern_below_threshold(self):
        r = SleepPatternRule()
        events = [
            {"event_id": "e1", "event_type": "SLEEP_CHANGED", "event_datetime": "2026-07-01T00:00:00Z", "payload": {}},
            {"event_id": "e2", "event_type": "SLEEP_CHANGED", "event_datetime": "2026-07-02T00:00:00Z", "payload": {}},
        ]
        assert r.evaluate(events, []) == []

    def REDACTED(self):
        """Eventos espaçados mais que 14d não formam cluster."""
        r = BehavioralCrisisRule()
        events = [
            {"event_id": "e1", "event_type": "OUTCOME_WORSENING",
             "event_datetime": "2026-07-01T00:00:00Z", "payload": {}},
            {"event_id": "e2", "event_type": "OUTCOME_WORSENING",
             "event_datetime": "2026-08-01T00:00:00Z", "payload": {}},    # >14d
        ]
        assert r.evaluate(events, []) == []
