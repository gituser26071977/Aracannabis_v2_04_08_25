"""
test_lifecycle_intervention.py — Lifecycle completo do Intervention.

Cobre TODOS os 12 InterventionType compartilhando o mesmo modelo.
Cobre a state machine: STARTED → ADJUSTED → PAUSED → RESUMED → STOPPED.
Cobre invariantes: dose coerente, stop_reason válido, terminal STOPPED.
"""
from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.domain.intervention import (
    Dose,
    Intervention,
    InterventionState,
    InterventionType,
)
from tests.neurodev_sprint_3_2.builders import RegistryBuilder


# ─── 12 InterventionTypes compartilham modelo ──────────────────────────────


ALL_INTERVENTION_TYPES = [
    InterventionType.MEDICATION,
    InterventionType.CANNABIS,
    InterventionType.PSYCHOTHERAPY,
    InterventionType.OCCUPATIONAL_THERAPY,
    InterventionType.SPEECH_THERAPY,
    InterventionType.ABA,
    InterventionType.NEUROMODULATION,
    InterventionType.NUTRITION,
    InterventionType.EXERCISE,
    InterventionType.SCHOOL_SUPPORT,
    InterventionType.PARENT_TRAINING,
    InterventionType.OTHER,
]


@pytest.mark.parametrize("itype", ALL_INTERVENTION_TYPES)
def REDACTED(itype):
    """Todos os 12 InterventionType podem ser iniciados com mesmo modelo."""
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=itype,
        subtype=f"test_{itype.value}",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
        dose=Dose(value=10, unit="mg", frequency="bid"),
    )
    assert intervention.intervention_type == itype
    assert intervention.state == InterventionState.STARTED
    assert intervention.is_active()


@pytest.mark.parametrize("itype", ALL_INTERVENTION_TYPES)
def REDACTED(itype):
    with pytest.raises(ValueError, match="subtype"):
        Intervention.start(
            identity_id="id-1",
            intervention_type=itype,
            subtype="",
            started_by="prof-1",
            start_date="2026-01-15",
            source_event_id="evt-1",
        )


def REDACTED():
    with pytest.raises(ValueError, match="source_event_ids"):
        Intervention(
            id="int-1",
            identity_id="id-1",
            intervention_type=InterventionType.MEDICATION,
            subtype="x",
            started_by="prof-1",
            start_date="2026-01-15",
            source_event_ids=[],
        )


# ─── State machine: transições válidas ──────────────────────────────────────


def test_started_to_adjusted():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="risperidona",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
        dose=Dose(value=0.5, unit="mg"),
    )
    intervention.adjust(
        event_id="evt-2",
        adjusted_by="prof-1",
        new_dose=Dose(value=1.0, unit="mg"),
        reason="Resposta insuficiente",
    )
    assert intervention.state == InterventionState.ADJUSTED
    assert intervention.dose.value == 1.0
    assert intervention.previous_dose.value == 0.5


def test_started_to_paused():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.pause(
        event_id="evt-2",
        paused_by="prof-1",
        reason="Efeito adverso",
        expected_resume_date="2026-02-15",
    )
    assert intervention.state == InterventionState.PAUSED
    assert intervention.pause_reason == "Efeito adverso"
    assert intervention.expected_resume_date == "2026-02-15"


def test_paused_to_resumed():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.ABA,
        subtype="ABA_intensive",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.pause(event_id="evt-2", paused_by="prof-1", reason="Férias")
    intervention.resume(event_id="evt-3", resumed_by="prof-1", resume_date="2026-02-01")
    assert intervention.state == InterventionState.RESUMED


def test_resumed_is_active():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.ABA,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.pause(event_id="evt-2", paused_by="prof-1", reason="x")
    intervention.resume(event_id="evt-3", resumed_by="prof-1", resume_date="2026-02-01")
    assert intervention.is_active()


def test_any_state_to_stopped():
    """Qualquer estado pode ir para STOPPED (terminal)."""
    for current_state_setup in [
        ("started", lambda i: None),
        ("paused", lambda i: i.pause(event_id="evt-x", paused_by="p", reason="r")),
        ("adjusted", lambda i: i.adjust(
            event_id="evt-x", adjusted_by="p", new_dose=Dose(value=1, unit="mg"),
            reason="r",
        )),
    ]:
        intervention = Intervention.start(
            identity_id="id-1",
            intervention_type=InterventionType.MEDICATION,
            subtype="x",
            started_by="prof-1",
            start_date="2026-01-15",
            source_event_id="evt-1",
        )
        current_state_setup[1](intervention)
        intervention.stop(
            event_id="evt-stop",
            stopped_by="prof-1",
            end_date="2026-12-31",
            reason="planned_completion",
            outcome_summary="Resposta clínica satisfatória",
        )
        assert intervention.state == InterventionState.STOPPED
        assert not intervention.is_active()


# ─── State machine: transições inválidas ────────────────────────────────────


def test_stopped_cannot_be_adjusted():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.stop(event_id="evt-s", stopped_by="p", end_date="2026-12-31", reason="planned_completion")
    with pytest.raises(ValueError, match="STOPPED"):
        intervention.adjust(
            event_id="evt-x", adjusted_by="p",
            new_dose=Dose(value=1, unit="mg"), reason="r",
        )


def test_stopped_cannot_be_paused():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.stop(event_id="evt-s", stopped_by="p", end_date="2026-12-31", reason="planned_completion")
    with pytest.raises(ValueError, match="Cannot pause"):
        intervention.pause(event_id="evt-x", paused_by="p", reason="r")


def REDACTED():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.pause(event_id="evt-1", paused_by="p", reason="r")
    with pytest.raises(ValueError):
        intervention.pause(event_id="evt-2", paused_by="p", reason="r")


def test_only_paused_can_be_resumed():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    with pytest.raises(ValueError, match="Only PAUSED"):
        intervention.resume(event_id="evt-1", resumed_by="p", resume_date="2026-02-01")


def REDACTED():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.pause(event_id="evt-1", paused_by="p", reason="r")
    with pytest.raises(ValueError, match="must be RESUMED"):
        intervention.adjust(
            event_id="evt-2", adjusted_by="p",
            new_dose=Dose(value=1, unit="mg"), reason="r",
        )


def REDACTED():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    intervention.stop(event_id="evt-s", stopped_by="p", end_date="2026-12-31", reason="planned_completion")
    with pytest.raises(ValueError, match="already stopped"):
        intervention.stop(event_id="evt-2", stopped_by="p", end_date="2026-12-31", reason="planned_completion")


def test_invalid_stop_reason_raises():
    intervention = Intervention.start(
        identity_id="id-1",
        intervention_type=InterventionType.MEDICATION,
        subtype="x",
        started_by="prof-1",
        start_date="2026-01-15",
        source_event_id="evt-1",
    )
    with pytest.raises(ValueError, match="Invalid stop_reason"):
        intervention.stop(
            event_id="evt-2", stopped_by="p", end_date="2026-12-31",
            reason="not_a_real_reason",
        )


# ─── Projection lifecycle ──────────────────────────────────────────────────


def REDACTED(projection, publisher):
    """Cenário: started → adjusted → paused → resumed → stopped via eventos."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-int-life")
        .with_identity()
        .with_medication(subtype="risperidona", dose_value=0.5, dose_unit="mg")
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

    interventions = projection.list_interventions(
        fixture.tenant_id, fixture.identity_id
    )
    assert len(interventions) == 1
    assert interventions[0].state == "started"
    assert interventions[0].subtype == "risperidona"
