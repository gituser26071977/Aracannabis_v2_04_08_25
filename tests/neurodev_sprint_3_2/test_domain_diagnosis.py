"""
Testes DDD do Diagnosis (state machine + multi-classificação).

Valida:
    - Todas as 12 transições válidas da matriz.
    - Transições inválidas levantam InvalidDiagnosisTransitionError.
    - Invariantes: CONFIRMED exige evidence + classification.
    - source_event_ids sempre presente.
    - Multi-classificação simultânea (CID + DSM).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from araos.specialties.neurodevelopmental.domain.classification import (
    ClassificationType,
    DiagnosisClassification,
)
from araos.specialties.neurodevelopmental.domain.condition import CID10Code, ConditionCode, DSM5Code
from araos.specialties.neurodevelopmental.domain.diagnosis import (
    Diagnosis,
    DiagnosisState,
    InvalidDiagnosisTransitionError,
)
from araos.specialties.neurodevelopmental.domain.services import (
    DiagnosisTransitionService,
    VALID_TRANSITIONS,
)


# ─── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def tea_code() -> ConditionCode:
    return ConditionCode("TEA_F84.0")


@pytest.fixture
def tda_h_code() -> ConditionCode:
    return ConditionCode("TDAH_F90.0")


@pytest.fixture
def cid10_classification() -> DiagnosisClassification:
    return DiagnosisClassification.of(
        cid10=CID10Code("F84.0"),
        added_in_event_id="evt-cid",
    )


@pytest.fixture
def multi_classification() -> DiagnosisClassification:
    """CID-10 + DSM-5-TR simultaneamente (ADR-0002 §2.7)."""
    base = DiagnosisClassification.of(
        cid10=CID10Code("F84.0"),
        added_in_event_id="evt-cid",
    )
    return base.with_added(
        type=ClassificationType.DSM5_TR,
        code="299.00",
        added_in_event_id="evt-dsm",
        is_primary=False,
    )


@pytest.fixture
def evidence() -> dict:
    return {
        "assessment_ids": ["assess-1", "assess-2"],
        "criteria_met": ["A1", "A2", "B1", "B3"],
        "clinical_notes": "Critérios preenchidos conforme ADI-R + ADOS-2",
    }


@pytest.fixture
def hypothesis_diag(tea_code: ConditionCode) -> Diagnosis:
    return Diagnosis.hypothesise(
        identity_id="identity-1",
        condition_code=tea_code,
        hypothesised_by="prof-1",
        source_event_id="evt-hyp",
        reason="Suspeita clínica aos 18 meses",
        onset_date="2024-01-15",
    )


# ─── Testes de construção ───────────────────────────────────────────────


def REDACTED(hypothesis_diag):
    assert hypothesis_diag.state == DiagnosisState.HYPOTHESIS
    assert hypothesis_diag.hypothesised_at is not None
    assert hypothesis_diag.onset_date == "2024-01-15"
    assert hypothesis_diag.rationale == "Suspeita clínica aos 18 meses"


def REDACTED():
    with pytest.raises(ValueError, match="source_event_ids"):
        Diagnosis(
            id="diag-x",
            identity_id="identity-1",
            condition_code=ConditionCode("TEA_F84.0"),
            state=DiagnosisState.HYPOTHESIS,
            source_event_ids=[],
        )


# ─── State machine: transições válidas ───────────────────────────────────


def test_hypothesis_to_investigating(hypothesis_diag):
    hypothesis_diag.start_investigation(event_id="evt-inv")
    assert hypothesis_diag.state == DiagnosisState.INVESTIGATING
    assert "evt-hyp" in hypothesis_diag.source_event_ids
    assert "evt-inv" in hypothesis_diag.source_event_ids


def REDACTED(hypothesis_diag):
    """Investigating → Hypothesis é permitido (refinar hipótese)."""
    hypothesis_diag.start_investigation(event_id="evt-inv")
    assert DiagnosisState.HYPOTHESIS in VALID_TRANSITIONS[DiagnosisState.INVESTIGATING]


def REDACTED(
    hypothesis_diag, cid10_classification, evidence
):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
        severity="moderate",
    )
    assert hypothesis_diag.state == DiagnosisState.CONFIRMED
    assert hypothesis_diag.severity == "moderate"
    assert hypothesis_diag.confirmed_at is not None


def test_investigating_to_confirmed(
    hypothesis_diag, cid10_classification, evidence
):
    hypothesis_diag.start_investigation(event_id="evt-inv")
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    assert hypothesis_diag.state == DiagnosisState.CONFIRMED


def test_confirmed_to_revised(hypothesis_diag, cid10_classification, evidence, tda_h_code):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.revise(
        event_id="evt-rev",
        new_condition_code=tda_h_code,
        revised_by="prof-1",
        reason="Comorbidade identificada",
    )
    assert hypothesis_diag.state == DiagnosisState.REVISED
    assert str(hypothesis_diag.condition_code) == "TDAH_F90.0"
    assert hypothesis_diag.previous_condition_code == "TEA_F84.0"


def test_confirmed_to_in_remission(hypothesis_diag, cid10_classification, evidence):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.mark_in_remission(
        event_id="evt-rem",
        remission_type="partial",
        marked_by="prof-1",
    )
    assert hypothesis_diag.state == DiagnosisState.IN_REMISSION
    assert hypothesis_diag.remission_type == "partial"


def REDACTED(
    hypothesis_diag, cid10_classification, evidence
):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.mark_in_remission(
        event_id="evt-rem",
        remission_type="partial",
        marked_by="prof-1",
    )
    # Recidiva: remissão → confirmado
    hypothesis_diag.confirm(
        event_id="evt-conf-2",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    assert hypothesis_diag.state == DiagnosisState.CONFIRMED


def test_hypothesis_to_discarded(hypothesis_diag):
    hypothesis_diag.discard(
        event_id="evt-disc",
        discarded_by="prof-1",
        reason="Avaliação subsequente não confirmou",
    )
    assert hypothesis_diag.state == DiagnosisState.DISCARDED
    assert hypothesis_diag.is_terminal()


def test_investigating_to_discarded(hypothesis_diag):
    hypothesis_diag.start_investigation(event_id="evt-inv")
    hypothesis_diag.discard(
        event_id="evt-disc",
        discarded_by="prof-1",
        reason="Evidência insuficiente após 6 meses",
    )
    assert hypothesis_diag.state == DiagnosisState.DISCARDED


def REDACTED(hypothesis_diag, cid10_classification, evidence):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.discard(
        event_id="evt-disc",
        discarded_by="prof-1",
        reason="Erro diagnóstico tardio identificado",
    )
    assert hypothesis_diag.state == DiagnosisState.DISCARDED


def test_revised_to_in_remission(hypothesis_diag, cid10_classification, evidence, tda_h_code):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.revise(
        event_id="evt-rev",
        new_condition_code=tda_h_code,
        revised_by="prof-1",
        reason="Refinamento",
    )
    hypothesis_diag.mark_in_remission(
        event_id="evt-rem",
        remission_type="complete",
        marked_by="prof-1",
    )
    assert hypothesis_diag.state == DiagnosisState.IN_REMISSION
    assert hypothesis_diag.remission_type == "complete"


def test_revised_to_discarded(hypothesis_diag, cid10_classification, evidence, tda_h_code):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    hypothesis_diag.revise(
        event_id="evt-rev",
        new_condition_code=tda_h_code,
        revised_by="prof-1",
        reason="Reavaliação",
    )
    hypothesis_diag.discard(
        event_id="evt-disc",
        discarded_by="prof-1",
        reason="Não confirmado após revisão",
    )
    assert hypothesis_diag.state == DiagnosisState.DISCARDED


# ─── State machine: transições inválidas ─────────────────────────────────


def REDACTED(hypothesis_diag, evidence):
    hypothesis_diag.discard(
        event_id="evt-disc",
        discarded_by="prof-1",
        reason="x",
    )
    # DISCARDED → qualquer estado deve falhar
    with pytest.raises(InvalidDiagnosisTransitionError):
        hypothesis_diag.confirm(
            event_id="evt-conf",
            confirmed_by="prof-1",
            confirmation_evidence=evidence,
        )


def REDACTED(hypothesis_diag):
    with pytest.raises(InvalidDiagnosisTransitionError):
        hypothesis_diag.revise(
            event_id="evt-rev",
            new_condition_code=ConditionCode("TDAH_F90.0"),
            revised_by="prof-1",
            reason="x",
        )


def REDACTED(hypothesis_diag):
    with pytest.raises(InvalidDiagnosisTransitionError):
        hypothesis_diag.mark_in_remission(
            event_id="evt-rem",
            remission_type="partial",
            marked_by="prof-1",
        )


def REDACTED():
    with pytest.raises(InvalidDiagnosisTransitionError) as exc_info:
        raise InvalidDiagnosisTransitionError("hypothesis", "in_remission")
    assert exc_info.value.from_state == "hypothesis"
    assert exc_info.value.to_state == "in_remission"


# ─── Invariantes ─────────────────────────────────────────────────────────


def test_confirmed_requires_evidence(hypothesis_diag, cid10_classification):
    hypothesis_diag.classification = cid10_classification
    with pytest.raises(ValueError, match="confirmation_evidence"):
        hypothesis_diag.confirm(
            event_id="evt-conf",
            confirmed_by="prof-1",
            confirmation_evidence={},  # vazio!
        )


def REDACTED(hypothesis_diag, evidence):
    # Sem classification
    with pytest.raises(ValueError, match="classification"):
        hypothesis_diag.confirm(
            event_id="evt-conf",
            confirmed_by="prof-1",
            confirmation_evidence=evidence,
        )


def REDACTED(hypothesis_diag, cid10_classification, evidence, tda_h_code):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    # Limpa classificação
    hypothesis_diag.classification = DiagnosisClassification.empty()
    with pytest.raises(ValueError):
        hypothesis_diag.revise(
            event_id="evt-rev",
            new_condition_code=tda_h_code,
            revised_by="prof-1",
            reason="x",
        )


def test_invalid_remission_type_raises(hypothesis_diag, cid10_classification, evidence):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    with pytest.raises(ValueError, match="remission_type"):
        hypothesis_diag.mark_in_remission(
            event_id="evt-rem",
            remission_type="invalid",
            marked_by="prof-1",
        )


# ─── Multi-classificação ─────────────────────────────────────────────────


def REDACTED(
    hypothesis_diag, multi_classification, evidence
):
    hypothesis_diag.classification = multi_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    # Verifica multi-classificação
    assert multi_classification.has_any()
    assert len(multi_classification.entries) == 2
    codes = {e.code for e in multi_classification.entries}
    assert codes == {"F84.0", "299.00"}
    types = {e.type for e in multi_classification.entries}
    assert types == {ClassificationType.CID10, ClassificationType.DSM5_TR}


def REDACTED(
    hypothesis_diag, cid10_classification, multi_classification, evidence
):
    hypothesis_diag.classification = cid10_classification
    hypothesis_diag.confirm(
        event_id="evt-conf",
        confirmed_by="prof-1",
        confirmation_evidence=evidence,
    )
    # Adiciona DSM-5-TR após confirmação
    hypothesis_diag.add_classification(event_id="evt-dsm", classification=multi_classification)
    assert len(hypothesis_diag.classification.entries) == 2


def REDACTED():
    with pytest.raises(ValueError, match="at least one"):
        DiagnosisClassification.empty().validate()


def REDACTED():
    base = DiagnosisClassification.of(cid10=CID10Code("F84.0"))
    two_primary = base.with_added(
        type=ClassificationType.CID10, code="F84.1", added_in_event_id="x", is_primary=True
    )
    with pytest.raises(ValueError, match="primary"):
        two_primary.validate()


# ─── Domain Service ──────────────────────────────────────────────────────


def REDACTED():
    assert DiagnosisTransitionService.validate(
        DiagnosisState.HYPOTHESIS, DiagnosisState.CONFIRMED
    )
    assert DiagnosisTransitionService.validate(
        DiagnosisState.CONFIRMED, DiagnosisState.IN_REMISSION
    )
    assert DiagnosisTransitionService.validate(
        DiagnosisState.IN_REMISSION, DiagnosisState.CONFIRMED
    )
    assert not DiagnosisTransitionService.validate(
        DiagnosisState.HYPOTHESIS, DiagnosisState.IN_REMISSION
    )
    assert not DiagnosisTransitionService.validate(
        DiagnosisState.DISCARDED, DiagnosisState.CONFIRMED
    )


def REDACTED():
    assert DiagnosisTransitionService.can_transition(
        DiagnosisState.HYPOTHESIS, DiagnosisState.INVESTIGATING
    )
    assert not DiagnosisTransitionService.can_transition(
        DiagnosisState.HYPOTHESIS, DiagnosisState.REVISED
    )


def REDACTED():
    targets = DiagnosisTransitionService.allowed_targets(DiagnosisState.HYPOTHESIS)
    assert DiagnosisState.INVESTIGATING in targets
    assert DiagnosisState.CONFIRMED in targets
    assert DiagnosisState.DISCARDED in targets
    assert DiagnosisState.IN_REMISSION not in targets


def REDACTED():
    assert DiagnosisTransitionService.is_terminal(DiagnosisState.DISCARDED)
    assert not DiagnosisTransitionService.is_terminal(DiagnosisState.CONFIRMED)
    assert DiagnosisTransitionService.is_active(DiagnosisState.CONFIRMED)
    assert DiagnosisTransitionService.is_active(DiagnosisState.INVESTIGATING)
    assert not DiagnosisTransitionService.is_active(DiagnosisState.DISCARDED)
    assert not DiagnosisTransitionService.is_active(DiagnosisState.IN_REMISSION)


# ─── Serialização ────────────────────────────────────────────────────────


def REDACTED(hypothesis_diag):
    data = hypothesis_diag.to_dict()
    assert data["state"] == "hypothesis"
    assert data["condition_code"] == "TEA_F84.0"
    assert data["onset_date"] == "2024-01-15"
    assert data["source_event_ids"] == ["evt-hyp"]
    assert "confirmed_at" in data
    assert data["confirmed_at"] is None
