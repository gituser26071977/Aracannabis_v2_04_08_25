"""
AraOS Cannabis Module — Events.

Eventos de domínio Cannabis para o Event Bus.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any
from datetime import datetime, timezone

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventPriority, EventCategory


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cannabis_started_event(
    patient_id: str,
    tenant_id: str,
    medication_id: str,
    product_name: str,
    initial_dose_mg: float,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_STARTED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "medication_id": medication_id,
            "product_name": product_name,
            "initial_dose_mg": initial_dose_mg,
            "started_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_product_added_event(
    patient_id: str,
    tenant_id: str,
    medication_id: str,
    product_name: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_PRODUCT_ADDED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "medication_id": medication_id,
            "product_name": product_name,
            "added_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_product_changed_event(
    patient_id: str,
    tenant_id: str,
    medication_id: str,
    previous_product: str,
    new_product: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_PRODUCT_CHANGED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "medication_id": medication_id,
            "previous_product": previous_product,
            "new_product": new_product,
            "changed_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_dose_changed_event(
    patient_id: str,
    tenant_id: str,
    medication_id: str,
    previous_dose_mg: float,
    new_dose_mg: float,
    reason: str = "",
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_DOSE_CHANGED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "medication_id": medication_id,
            "previous_dose_mg": previous_dose_mg,
            "new_dose_mg": new_dose_mg,
            "reason": reason,
            "changed_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_outcome_recorded_event(
    patient_id: str,
    tenant_id: str,
    metric_name: str,
    score: float,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_OUTCOME_RECORDED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "metric_name": metric_name,
            "score": score,
            "recorded_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_alert_triggered_event(
    patient_id: str,
    tenant_id: str,
    alert_type: str,
    severity: str,
    description: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_ALERT_TRIGGERED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "alert_type": alert_type,
            "severity": severity,
            "description": description,
            "triggered_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.HIGH if severity in ("high", "critical") else EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def cannabis_discontinued_event(
    patient_id: str,
    tenant_id: str,
    medication_id: str,
    reason: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    return EventEnvelopeV2(
        event_type="CANNABIS_DISCONTINUED",
        payload={
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "medication_id": medication_id,
            "reason": reason,
            "discontinued_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )
