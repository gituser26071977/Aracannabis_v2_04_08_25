"""
AraOS Follow-up — Events.

Eventos do motor de acompanhamento para o Event Bus.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any
from datetime import datetime, timezone

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventPriority, EventCategory


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def followup_started_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    specialty_code: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: programa de acompanhamento iniciado."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_STARTED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "specialty_code": specialty_code,
            "started_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def followup_completed_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: programa de acompanhamento concluído."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_COMPLETED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "completed_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def followup_response_received_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    response_id: str,
    checkpoint_id: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: resposta de questionário recebida."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_RESPONSE_RECEIVED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "response_id": response_id,
            "checkpoint_id": checkpoint_id,
            "received_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def followup_alert_triggered_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    alert_id: str,
    severity: str,
    title: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: alerta de follow-up disparado."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_ALERT_TRIGGERED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "alert_id": alert_id,
            "severity": severity,
            "title": title,
            "triggered_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.HIGH if severity in ("high", "critical") else EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )


def followup_escalated_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    alert_id: str,
    reason: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: alerta escalonado."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_ESCALATED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "alert_id": alert_id,
            "reason": reason,
            "escalated_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.CRITICAL,
        event_category=EventCategory.CLINICAL,
    )


def followup_phase_changed_event(
    program_id: str,
    patient_id: str,
    tenant_id: str,
    previous_phase: str,
    new_phase: str,
    correlation_id: str = "",
) -> EventEnvelopeV2:
    """Evento: fase do programa alterada."""
    return EventEnvelopeV2(
        event_type="FOLLOWUP_PHASE_CHANGED",
        payload={
            "program_id": program_id,
            "patient_id": patient_id,
            "tenant_id": tenant_id,
            "previous_phase": previous_phase,
            "new_phase": new_phase,
            "changed_at": _now(),
        },
        tenant_id=tenant_id,
        correlation_id=correlation_id,
        priority=EventPriority.NORMAL,
        event_category=EventCategory.CLINICAL,
    )
