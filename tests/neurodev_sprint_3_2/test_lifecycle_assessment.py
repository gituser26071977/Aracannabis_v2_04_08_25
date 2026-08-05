"""
test_lifecycle_assessment.py — Lifecycle do Assessment.

Cobre:
    - apply(): cria versão 1.
    - amend(): cria nova versão (imutável).
    - source_event_ids obrigatório.
    - linked_diagnosis_ids conecta evidência ao diagnóstico.
    - Cenários reais: MCHAT-R/F, CARS2, ATEC, Vineland, SNAP-IV, SRS-2.
"""
from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.domain.assessment import (
    Assessment,
    AssessmentScore,
    AssessmentStatus,
)
from tests.neurodev_sprint_3_2.builders import RegistryBuilder


# ─── Constantes: escalas suportadas ────────────────────────────────────────


SUPPORTED_SCALES = [
    "MCHAT_R_F",  # TEA screening 16-30m
    "CARS2",      # TEA avaliação ≥2a
    "ATEC",       # TEA longitudinal 2-12a
    "VINELAND_3", # Adaptativo 0-90a
    "SNAP_IV",    # TDAH screening 6-17a
    "SRS_2",      # TEA social ≥2.5a
    "GAD7",       # Ansiedade (transversal)
    "PHQ9",       # Depressão (transversal)
]


# ─── Construction tests ────────────────────────────────────────────────────


@pytest.mark.parametrize("scale_code", SUPPORTED_SCALES)
def test_apply_each_supported_scale(scale_code):
    """Todas as 8 escalas podem ser aplicadas."""
    assessment = Assessment.apply(
        identity_id="id-1",
        scale_code=scale_code,
        scale_version="2024-01",
        applied_by="prof-1",
        raw_responses={"q1": 1, "q2": 0},
        computed_scores={"total": 5},
        interpretation={"band": "elevated"},
        source_event_id="evt-1",
    )
    assert assessment.scale_code == scale_code
    assert assessment.version == 1
    assert assessment.status == AssessmentStatus.FINAL


def REDACTED():
    with pytest.raises(ValueError, match="source_event_ids"):
        Assessment(
            id="assess-1",
            identity_id="id-1",
            scale_code="MCHAT_R_F",
            scale_version="2024-01",
            applied_by="prof-1",
            source_event_ids=[],
        )


def REDACTED():
    with pytest.raises(ValueError, match="scale_code"):
        Assessment(
            id="assess-1",
            identity_id="id-1",
            scale_code="",
            scale_version="2024-01",
            applied_by="prof-1",
            source_event_ids=["evt-1"],
        )


def REDACTED():
    with pytest.raises(ValueError, match="scale_version"):
        Assessment(
            id="assess-1",
            identity_id="id-1",
            scale_code="MCHAT_R_F",
            scale_version="",
            applied_by="prof-1",
            source_event_ids=["evt-1"],
        )


# ─── Amend (versionamento imutável) ────────────────────────────────────────


def test_amend_creates_new_version():
    a1 = Assessment.apply(
        identity_id="id-1",
        scale_code="MCHAT_R_F",
        scale_version="2024-01",
        applied_by="prof-1",
        raw_responses={"q1": 0, "q2": 0, "q3": 0},
        computed_scores={"total": 0},
        interpretation={"band": "low"},
        source_event_id="evt-1",
    )
    assert a1.version == 1

    a2 = a1.amend(
        event_id="evt-2",
        updated_by="prof-2",
        new_raw_responses={"q1": 1, "q2": 1, "q3": 0},
        new_computed_scores={"total": 2},
        new_interpretation={"band": "moderate"},
        reason="Re-correção após supervisão",
    )
    assert a2.version == 2
    assert a2.previous_version_id == str(a1.id)
    assert a2.status == AssessmentStatus.AMENDED
    # a1 permanece imutável
    assert a1.version == 1
    assert a1.status == AssessmentStatus.FINAL


def REDACTED():
    a1 = Assessment.apply(
        identity_id="id-1",
        scale_code="CARS2",
        scale_version="2024-01",
        applied_by="prof-1",
        raw_responses={},
        computed_scores={"total": 30},
        interpretation={},
        source_event_id="evt-1",
    )
    a2 = a1.amend(event_id="evt-2", updated_by="prof-2", reason="correção")
    assert a2.identity_id == a1.identity_id
    assert a2.scale_code == a1.scale_code
    assert a2.scale_version == a1.scale_version


def test_amend_chains_three_versions():
    a1 = Assessment.apply(
        identity_id="id-1",
        scale_code="ATEC",
        scale_version="2024-01",
        applied_by="prof-1",
        raw_responses={},
        computed_scores={},
        interpretation={},
        source_event_id="evt-1",
    )
    a2 = a1.amend(event_id="evt-2", updated_by="prof-1", reason="v2")
    a3 = a2.amend(event_id="evt-3", updated_by="prof-1", reason="v3")
    assert a1.version == 1
    assert a2.version == 2
    assert a3.version == 3
    assert a3.previous_version_id == str(a2.id)


# ─── AssessmentScore value object ──────────────────────────────────────────


def test_assessment_score_to_dict():
    score = AssessmentScore(
        subscale="social",
        value=15.0,
        min_value=0.0,
        max_value=30.0,
        interpretation="moderate",
    )
    d = score.to_dict()
    assert d["subscale"] == "social"
    assert d["value"] == 15.0
    assert d["interpretation"] == "moderate"


def REDACTED():
    a = Assessment.apply(
        identity_id="id-1",
        scale_code="MCHAT_R_F",
        scale_version="2024-01",
        applied_by="prof-1",
        raw_responses={},
        computed_scores={},
        interpretation={},
        source_event_id="evt-1",
        linked_diagnosis_ids=["diag-1", "diag-2"],
    )
    assert a.linked_diagnosis_ids == ["diag-1", "diag-2"]


# ─── Projection lifecycle ──────────────────────────────────────────────────


def REDACTED(projection, publisher):
    """
    Identity com múltiplas escalas aplicadas — Registry reflete todas.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-multi-assess")
        .with_identity()
        .with_assessment(scale_code="MCHAT_R_F", computed_score=8.0)
        .with_assessment(scale_code="CARS2", computed_score=32.0)
        .with_assessment(scale_code="ATEC", computed_score=85.0)
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

    assessments = projection.list_assessments(
        fixture.tenant_id, fixture.identity_id
    )
    assert len(assessments) == 3
    codes = {a.scale_code for a in assessments}
    assert codes == {"MCHAT_R_F", "CARS2", "ATEC"}


def REDACTED(projection, publisher):
    """
    Cenário: assessment aplicado (v1) e amended (v2).
    Cada versão é um evento separado; Registry preserva ambas.
    """
    from datetime import datetime

    fixture = (
        RegistryBuilder()
        .with_tenant("t-amend")
        .with_identity()
        .with_assessment(scale_code="MCHAT_R_F", computed_score=3.0)
        .build()
    )
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

    # Adiciona evento ASSESSMENT_UPDATED (amendment)
    assess_id = fixture.assessments[0]["aggregate_id"]
    publisher.publish(
        tenant_id=fixture.tenant_id,
        patient_id=fixture.patient_id,
        event_type="ASSESSMENT_UPDATED",
        event_datetime=datetime.now(tz=datetime.now().astimezone().tzinfo),
        source_module="neurodevelopmental",
        payload={
            "identity_id": fixture.identity_id,
            "updated_by": "prof-2",
            "raw_responses": {"q1": 1, "q2": 1, "q3": 1},
            "computed_scores": {"total": 5},
            "interpretation": {"band": "elevated"},
            "reason": "Re-correção",
        },
        aggregate_type="assessment",
        aggregate_id=assess_id,
        created_by="prof-2",
    )

    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    assessments = projection.list_assessments(
        fixture.tenant_id, fixture.identity_id
    )
    assert len(assessments) == 1
    assert assessments[0].scale_code == "MCHAT_R_F"
