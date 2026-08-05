"""
AraOS Neurodevelopmental — Outcome Application Service.

Resultados clínicos derivados de eventos: improvement, worsening,
partial_response, remission, adverse_event, no_change.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.events import (
    OutcomeAdverseEvent,
    OutcomeImprovement,
    OutcomeNoChange,
    OutcomePartialResponse,
    OutcomeRemission,
    OutcomeWorsening,
)
from ..domain.ids import OutcomeId, new_id
from ..domain.outcome import (
    OutcomeCausality,
    OutcomeMagnitude,
    OutcomeSeverity,
)


@dataclass
class OutcomeCommandResult:
    event_id: str
    outcome_id: str
    event_type: str
    occurred_at: datetime


class OutcomeService:
    """Application service para Outcome."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    def record_improvement(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        evidence: Dict[str, Any],
        intervention_id: Optional[str] = None,
        magnitude: Optional[OutcomeMagnitude] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomeImprovement(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            evidence=evidence,
            intervention_id=intervention_id,
            magnitude=magnitude.value if magnitude else None,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def record_worsening(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        evidence: Dict[str, Any],
        intervention_id: Optional[str] = None,
        magnitude: Optional[OutcomeMagnitude] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomeWorsening(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            evidence=evidence,
            intervention_id=intervention_id,
            magnitude=magnitude.value if magnitude else None,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def record_partial_response(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        intervention_id: str,
        evidence: Dict[str, Any],
        responding_domains: Optional[List[str]] = None,
        non_responding_domains: Optional[List[str]] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomePartialResponse(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            intervention_id=intervention_id,
            evidence=evidence,
            responding_domains=responding_domains,
            non_responding_domains=non_responding_domains,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def record_remission(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        evidence: Dict[str, Any],
        duration_months: Optional[int] = None,
        intervention_id: Optional[str] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomeRemission(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            evidence=evidence,
            duration_months=duration_months,
            intervention_id=intervention_id,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def record_adverse_event(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        severity: OutcomeSeverity,
        description: str,
        intervention_id: Optional[str] = None,
        causality: Optional[OutcomeCausality] = None,
        action_taken: Optional[str] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomeAdverseEvent(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            severity=severity.value,
            description=description,
            intervention_id=intervention_id,
            causality=causality.value if causality else None,
            action_taken=action_taken,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def record_no_change(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        observed_by: str,
        intervention_id: Optional[str] = None,
        duration_observed_months: Optional[int] = None,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> OutcomeCommandResult:
        when = event_datetime or datetime.now(timezone.utc)
        new_outcome_id = OutcomeId(new_id())

        event = OutcomeNoChange(
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            actor_id=observed_by,
            occurred_at=when,
            observed_by=observed_by,
            intervention_id=intervention_id,
            duration_observed_months=duration_observed_months,
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
            aggregate_type="outcome",
            aggregate_id=str(new_outcome_id),
            created_by=observed_by,
        )

        return OutcomeCommandResult(
            event_id=event_id,
            outcome_id=str(new_outcome_id),
            event_type=event.event_type,
            occurred_at=when,
        )