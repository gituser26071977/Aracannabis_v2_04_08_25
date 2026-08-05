"""
AraOS Neurodevelopmental — Diagnosis Application Service.

Orquestra ciclo de vida do Diagnosis:
    HYPOTHESIS → INVESTIGATING → CONFIRMED → REVISED/IN_REMISSION/DISCARDED

Toda transição = 1 Domain Event publicado no Event Store.

ADR-0002 §2.2.2: 'Diagnosis = ciclo de vida com 6 estados...
Cada mudança gera Clinical Event.'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.classification import (
    ClassificationEntry,
    ClassificationType,
    DiagnosisClassification,
)
from ..domain.condition import CID10Code, CID11Code, ConditionCode, DSM5Code
from ..domain.diagnosis import (
    Diagnosis,
    DiagnosisState,
    InvalidDiagnosisTransitionError,
)
from ..domain.events import (
    DiagnosisClassificationAdded,
    DiagnosisClassificationRemoved,
    DiagnosisConfirmed,
    DiagnosisDiscarded,
    DiagnosisHypothesised,
    DiagnosisInRemission,
    DiagnosisInvestigating,
    DiagnosisRevised,
)
from ..domain.ids import DiagnosisId, new_id
from ..domain.services import DiagnosisTransitionService


@dataclass
class DiagnosisCommandResult:
    """Resultado de uma operação sobre Diagnosis."""

    event_id: str
    diagnosis_id: str
    event_type: str
    occurred_at: datetime


class DiagnosisService:
    """Application service para Diagnosis."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    # ─── Commands ───────────────────────────────────────────────────────

    def hypothesize(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        condition_code: ConditionCode,
        hypothesised_by: str,
        reason: Optional[str] = None,
        onset_date: Optional[str] = None,
        classification: Optional[DiagnosisClassification] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Cria nova Diagnosis em estado HYPOTHESIS.

        Args:
            tenant_id: tenant do AraOS.
            patient_id: ID administrativo do paciente.
            identity_id: ClinicalIdentityId à qual pertence.
            condition_code: ConditionCode do catálogo.
            hypothesised_by: profissional.
            reason: justificativa clínica.
            onset_date: data de início clínico (ISO date).
            classification: classificação multi-sistema opcional.
        """
        when = event_datetime or datetime.now(timezone.utc)
        new_diagnosis_id = DiagnosisId(new_id())

        # 1. Construir payload com classificação serializada (se houver)
        classification_dict: Optional[Dict[str, Any]] = None
        if classification is not None and classification.has_any():
            classification_dict = {
                "entries": [
                    {
                        "type": e.type.value,
                        "code": e.code,
                        "is_primary": e.is_primary,
                    }
                    for e in classification.entries
                ]
            }

        event = DiagnosisHypothesised(
            aggregate_type="diagnosis",
            aggregate_id=str(new_diagnosis_id),
            actor_id=hypothesised_by,
            occurred_at=when,
            condition_code=str(condition_code),
            hypothesised_by=hypothesised_by,
            reason=reason,
            onset_date=onset_date,
            classification=classification_dict,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id
        payload["identity_id"] = identity_id  # thread para projection

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=str(new_diagnosis_id),
            created_by=hypothesised_by,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=str(new_diagnosis_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def start_investigation(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        current_state: DiagnosisState,
        investigation_plan: str,
        actor_id: str,
        expected_evidence: Optional[List[str]] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Transição HYPOTHESIS → INVESTIGATING.

        Args:
            current_state: estado atual do Diagnosis (validado pela matriz).
            investigation_plan: plano de investigação.
            expected_evidence: lista de critérios a coletar.
        """
        when = event_datetime or datetime.now(timezone.utc)
        DiagnosisTransitionService.validate(current_state, DiagnosisState.INVESTIGATING)

        event = DiagnosisInvestigating(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=actor_id,
            occurred_at=when,
            investigation_plan=investigation_plan,
            expected_evidence=expected_evidence,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=actor_id,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def confirm(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        current_state: DiagnosisState,
        confirmed_by: str,
        confirmation_evidence: Dict[str, Any],
        actor_id: str,
        severity: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Transição HYPOTHESIS/INVESTIGATING → CONFIRMED.

        Args:
            confirmation_evidence: dict com assessment_ids/exam_ids/criteria_met
                                   (não-vazio, validado por JSON Schema).
            severity: 'mild'/'moderate'/'severe'/'profound'.
        """
        when = event_datetime or datetime.now(timezone.utc)
        DiagnosisTransitionService.validate(current_state, DiagnosisState.CONFIRMED)

        event = DiagnosisConfirmed(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=actor_id,
            occurred_at=when,
            confirmed_by=confirmed_by,
            confirmation_evidence=confirmation_evidence,
            severity=severity,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=actor_id,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def revise(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        current_state: DiagnosisState,
        new_condition_code: ConditionCode,
        revised_by: str,
        reason: str,
        actor_id: str,
        previous_condition_code: Optional[str] = None,
        new_classification: Optional[Dict[str, Any]] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Transição CONFIRMED → REVISED.
        """
        when = event_datetime or datetime.now(timezone.utc)
        DiagnosisTransitionService.validate(current_state, DiagnosisState.REVISED)

        event = DiagnosisRevised(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=actor_id,
            occurred_at=when,
            new_condition_code=str(new_condition_code),
            previous_condition_code=previous_condition_code,
            revised_by=revised_by,
            reason=reason,
            new_classification=new_classification,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=actor_id,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def mark_in_remission(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        current_state: DiagnosisState,
        remission_type: str,
        marked_by: str,
        actor_id: str,
        evidence: Optional[Dict[str, Any]] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Transição CONFIRMED/REVISED → IN_REMISSION.
        """
        when = event_datetime or datetime.now(timezone.utc)
        DiagnosisTransitionService.validate(current_state, DiagnosisState.IN_REMISSION)

        event = DiagnosisInRemission(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=actor_id,
            occurred_at=when,
            remission_type=remission_type,
            marked_by=marked_by,
            evidence=evidence,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=actor_id,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def discard(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        current_state: DiagnosisState,
        discarded_by: str,
        reason: str,
        actor_id: str,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """
        Transição para DISCARDED (estado terminal).
        """
        when = event_datetime or datetime.now(timezone.utc)
        DiagnosisTransitionService.validate(current_state, DiagnosisState.DISCARDED)

        event = DiagnosisDiscarded(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=actor_id,
            occurred_at=when,
            discarded_by=discarded_by,
            reason=reason,
            notes=notes,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=actor_id,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def add_classification(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        classification_type: ClassificationType,
        code: str,
        added_by: str,
        is_primary: bool = False,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """Adiciona classificação multi-sistema."""
        when = event_datetime or datetime.now(timezone.utc)

        event = DiagnosisClassificationAdded(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=added_by,
            occurred_at=when,
            classification_type=classification_type.value,
            code=code,
            added_by=added_by,
            is_primary=is_primary,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=added_by,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def remove_classification(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        diagnosis_id: str,
        classification_type: ClassificationType,
        code: str,
        removed_by: str,
        reason: str,
        event_datetime: Optional[datetime] = None,
    ) -> DiagnosisCommandResult:
        """Remove classificação (histórico preservado)."""
        when = event_datetime or datetime.now(timezone.utc)

        event = DiagnosisClassificationRemoved(
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            actor_id=removed_by,
            occurred_at=when,
            classification_type=classification_type.value,
            code=code,
            removed_by=removed_by,
            reason=reason,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="diagnosis",
            aggregate_id=diagnosis_id,
            created_by=removed_by,
        )

        return DiagnosisCommandResult(
            event_id=event_id,
            diagnosis_id=diagnosis_id,
            event_type=event.event_type,
            occurred_at=when,
        )