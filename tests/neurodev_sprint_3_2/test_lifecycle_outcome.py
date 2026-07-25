"""
test_lifecycle_outcome.py — Lifecycle completo do Outcome.

Cobre os 6 OutcomeType e suas invariantes:
    - improvement / worsening → magnitude
    - partial_response → responding/non_responding domains
    - remission → duration_months
    - adverse_event → severity + causality + description
    - no_change → duration_observed_months
"""
from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.domain.outcome import (
    Outcome,
    OutcomeCausality,
    OutcomeMagnitude,
    OutcomeSeverity,
    OutcomeType,
)
from tests.neurodev_sprint_3_2.builders import RegistryBuilder


# ─── Factories: cada tipo cria Outcome com campos válidos ──────────────────


def test_improvement_factory():
    outcome = Outcome.improvement(
        identity_id="id-1",
        observed_by="prof-1",
        evidence={"assessment_ids": ["a1"]},
        intervention_id="int-1",
        magnitude=OutcomeMagnitude.MODERATE,
        source_event_id="evt-1",
    )
    assert outcome.outcome_type == OutcomeType.IMPROVEMENT
    assert outcome.magnitude == OutcomeMagnitude.MODERATE
    assert outcome.intervention_id == "int-1"


def test_worsening_factory():
    outcome = Outcome.worsening(
        identity_id="id-1",
        observed_by="prof-1",
        evidence={"assessment_ids": ["a1"]},
        magnitude=OutcomeMagnitude.LARGE,
        source_event_id="evt-1",
    )
    assert outcome.outcome_type == OutcomeType.WORSENING
    assert outcome.magnitude == OutcomeMagnitude.LARGE


def test_adverse_event_factory():
    outcome = Outcome.adverse_event(
        identity_id="id-1",
        observed_by="prof-1",
        severity=OutcomeSeverity.MODERATE,
        description="Sonolência excessiva",
        intervention_id="int-1",
        causality=OutcomeCausality.PROBABLE,
        action_taken="Reduziu dose",
        source_event_id="evt-1",
    )
    assert outcome.outcome_type == OutcomeType.ADVERSE_EVENT
    assert outcome.severity == OutcomeSeverity.MODERATE
    assert outcome.causality == OutcomeCausality.PROBABLE
    assert outcome.description == "Sonolência excessiva"


def test_partial_response_factory():
    outcome = Outcome.partial_response(
        identity_id="id-1",
        observed_by="prof-1",
        intervention_id="int-1",
        evidence={"assessment_ids": ["a1"]},
        responding_domains=["social", "communication"],
        non_responding_domains=["sensory"],
        source_event_id="evt-1",
    )
    assert outcome.outcome_type == OutcomeType.PARTIAL_RESPONSE
    assert outcome.responding_domains == ["social", "communication"]


def test_remission_factory():
    outcome = Outcome.remission(
        identity_id="id-1",
        observed_by="prof-1",
        evidence={"assessment_ids": ["a1"]},
        duration_months=18,
        source_event_id="evt-1",
    )
    assert outcome.outcome_type == OutcomeType.REMISSION
    assert outcome.duration_months == 18


def test_no_change_factory():
    outcome = Outcome.no_change(
        identity_id="id-1",
        observed_by="prof-1",
        source_event_id="evt-1",
        duration_observed_months=6,
    )
    assert outcome.outcome_type == OutcomeType.NO_CHANGE


# ─── Enums ─────────────────────────────────────────────────────────────────


def test_all_outcome_types_covered():
    expected = {
        "improvement",
        "worsening",
        "partial_response",
        "remission",
        "no_change",
        "adverse_event",
    }
    actual = {t.value for t in OutcomeType}
    assert actual == expected


def REDACTED():
    severities = {s.value for s in OutcomeSeverity}
    assert "life_threatening" in severities
    assert "fatal" in severities


def REDACTED():
    assert len(list(OutcomeCausality)) == 5


# ─── Projection lifecycle ──────────────────────────────────────────────────


def REDACTED(projection, publisher):
    """
    Cenário rico: identity + 6 outcomes (um de cada tipo).
    Registry deve ter 6 outcome rows.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-out-6")
        .with_identity()
        .with_outcome(type="improvement")
        .with_outcome(type="worsening")
        .with_outcome(type="partial_response")
        .with_outcome(type="remission")
        .with_outcome(type="no_change")
        .with_outcome(type="adverse_event")
        .build()
    )
    from datetime import datetime

    for evt in fixture.events:
        publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=datetime.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    outcomes = projection.list_outcomes(fixture.tenant_id, fixture.identity_id)
    assert len(outcomes) == 6
    types = {o.outcome_type for o in outcomes}
    assert types == {
        "improvement",
        "worsening",
        "partial_response",
        "remission",
        "no_change",
        "adverse_event",
    }


def REDACTED(projection, publisher):
    """Outcome referencia Intervention via intervention_id."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-out-int")
        .with_identity()
        .with_medication(subtype="risperidona")
        .with_outcome(type="improvement", magnitude="moderate")
        .build()
    )
    from datetime import datetime

    for evt in fixture.events:
        publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=datetime.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    outcomes = projection.list_outcomes(fixture.tenant_id, fixture.identity_id)
    assert len(outcomes) == 1
    assert outcomes[0].outcome_type == "improvement"
    assert outcomes[0].magnitude == "moderate"
    # Outcome referencia a intervention
    assert outcomes[0].intervention_id is not None
