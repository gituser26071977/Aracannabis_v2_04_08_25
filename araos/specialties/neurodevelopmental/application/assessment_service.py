"""
AraOS Neurodevelopmental — Assessment Application Service.

Aplicação de escalas neuropsicológicas. Assessment produz evidência —
não mutua estado clínico diretamente.

ADR-0002 §2.2.4: 'Assessment = aplicações de escalas, nunca altera
diretamente o estado do paciente.'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.assessment import Assessment, AssessmentStatus
from ..domain.events import AssessmentApplied, AssessmentUpdated
from ..domain.ids import AssessmentId, new_id


@dataclass
class AssessmentCommandResult:
    event_id: str
    assessment_id: str
    event_type: str
    occurred_at: datetime


class AssessmentService:
    """Application service para Assessment."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    def apply(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        scale_code: str,
        scale_version: str,
        applied_by: str,
        raw_responses: Dict[str, Any],
        computed_scores: Dict[str, Any],
        interpretation: Dict[str, Any],
        linked_diagnosis_ids: Optional[List[str]] = None,
        status: AssessmentStatus = AssessmentStatus.FINAL,
        event_datetime: Optional[datetime] = None,
    ) -> AssessmentCommandResult:
        """
        Aplica escala neuropsicológica.
        """
        when = event_datetime or datetime.now(timezone.utc)
        new_assessment_id = AssessmentId(new_id())

        event = AssessmentApplied(
            aggregate_type="assessment",
            aggregate_id=str(new_assessment_id),
            actor_id=applied_by,
            occurred_at=when,
            scale_code=scale_code,
            scale_version=scale_version,
            applied_by=applied_by,
            raw_responses=raw_responses,
            computed_scores=computed_scores,
            interpretation=interpretation,
            linked_diagnosis_ids=linked_diagnosis_ids,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="assessment",
            aggregate_id=str(new_assessment_id),
            created_by=applied_by,
        )

        return AssessmentCommandResult(
            event_id=event_id,
            assessment_id=str(new_assessment_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def update(
        self,
        tenant_id: str,
        patient_id: str,
        assessment_id: str,
        updated_by: str,
        raw_responses: Dict[str, Any],
        computed_scores: Dict[str, Any],
        interpretation: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> AssessmentCommandResult:
        """
        Atualiza (corrige) Assessment existente.

        Cria nova versão — log preserva histórico completo.
        """
        when = event_datetime or datetime.now(timezone.utc)

        event = AssessmentUpdated(
            aggregate_type="assessment",
            aggregate_id=assessment_id,
            actor_id=updated_by,
            occurred_at=when,
            updated_by=updated_by,
            raw_responses=raw_responses,
            computed_scores=computed_scores,
            interpretation=interpretation,
            reason=reason,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="assessment",
            aggregate_id=assessment_id,
            created_by=updated_by,
        )

        return AssessmentCommandResult(
            event_id=event_id,
            assessment_id=assessment_id,
            event_type=event.event_type,
            occurred_at=when,
        )