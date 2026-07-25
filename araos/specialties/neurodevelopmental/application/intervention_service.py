"""
AraOS Neurodevelopmental — Intervention Application Service.

Modelo único compartilhado para qualquer tipo de intervenção clínica.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.events import (
    InterventionAdjusted,
    InterventionPaused,
    InterventionResumed,
    InterventionStarted,
    InterventionStopped,
)
from ..domain.intervention import Dose, InterventionType


@dataclass
class InterventionCommandResult:
    event_id: str
    intervention_id: str
    event_type: str
    occurred_at: datetime


class InterventionService:
    """Application service para Intervention."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    def start(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        intervention_id: str,
        intervention_type: InterventionType,
        subtype: str,
        started_by: str,
        start_date: str,
        dose: Optional[Dose] = None,
        indication_condition_code: Optional[str] = None,
        linked_diagnosis_ids: Optional[List[str]] = None,
        prescriber_id: Optional[str] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> InterventionCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        dose_dict = dose.to_dict() if dose is not None else None

        event = InterventionStarted(
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            actor_id=started_by,
            occurred_at=when,
            intervention_type=intervention_type.value,
            subtype=subtype,
            started_by=started_by,
            start_date=start_date,
            dose=dose_dict,
            indication_condition_code=indication_condition_code,
            linked_diagnosis_ids=linked_diagnosis_ids,
            prescriber_id=prescriber_id,
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
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            created_by=started_by,
        )

        return InterventionCommandResult(
            event_id=event_id,
            intervention_id=intervention_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def adjust(
        self,
        tenant_id: str,
        patient_id: str,
        intervention_id: str,
        adjusted_by: str,
        new_dose: Dose,
        reason: str,
        previous_dose: Optional[Dose] = None,
        event_datetime: Optional[datetime] = None,
    ) -> InterventionCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        previous_dose_dict = previous_dose.to_dict() if previous_dose else None

        event = InterventionAdjusted(
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            actor_id=adjusted_by,
            occurred_at=when,
            adjusted_by=adjusted_by,
            previous_dose=previous_dose_dict,
            new_dose=new_dose.to_dict(),
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
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            created_by=adjusted_by,
        )

        return InterventionCommandResult(
            event_id=event_id,
            intervention_id=intervention_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def pause(
        self,
        tenant_id: str,
        patient_id: str,
        intervention_id: str,
        paused_by: str,
        reason: str,
        expected_resume_date: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> InterventionCommandResult:
        when = event_datetime or datetime.now(timezone.utc)

        event = InterventionPaused(
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            actor_id=paused_by,
            occurred_at=when,
            paused_by=paused_by,
            reason=reason,
            expected_resume_date=expected_resume_date,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            created_by=paused_by,
        )

        return InterventionCommandResult(
            event_id=event_id,
            intervention_id=intervention_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def resume(
        self,
        tenant_id: str,
        patient_id: str,
        intervention_id: str,
        resumed_by: str,
        resume_date: str,
        new_dose: Optional[Dose] = None,
        event_datetime: Optional[datetime] = None,
    ) -> InterventionCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_dose_dict = new_dose.to_dict() if new_dose else None

        event = InterventionResumed(
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            actor_id=resumed_by,
            occurred_at=when,
            resumed_by=resumed_by,
            resume_date=resume_date,
            new_dose=new_dose_dict,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            created_by=resumed_by,
        )

        return InterventionCommandResult(
            event_id=event_id,
            intervention_id=intervention_id,
            event_type=event.event_type,
            occurred_at=when,
        )

    def stop(
        self,
        tenant_id: str,
        patient_id: str,
        intervention_id: str,
        stopped_by: str,
        end_date: str,
        reason: str,
        outcome_summary: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> InterventionCommandResult:
        when = event_datetime or datetime.now(timezone.utc)

        event = InterventionStopped(
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            actor_id=stopped_by,
            occurred_at=when,
            stopped_by=stopped_by,
            end_date=end_date,
            reason=reason,
            outcome_summary=outcome_summary,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="intervention",
            aggregate_id=intervention_id,
            created_by=stopped_by,
        )

        return InterventionCommandResult(
            event_id=event_id,
            intervention_id=intervention_id,
            event_type=event.event_type,
            occurred_at=when,
        )