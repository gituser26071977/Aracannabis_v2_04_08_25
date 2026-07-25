"""
EventBuilder — fluent factory para ClinicalEvents (formato do Event Store).

Permite construir eventos prontos para InMemoryClinicalEventStore:

    event = (EventBuilder()
             .with_type("DIAGNOSIS_CONFIRMED")
             .with_aggregate("diagnosis", "diag-1")
             .with_payload(condition_code="TEA_F84.0", ...)
             .with_actor("prof-1")
             .build())

Ou via atalho:

    event = build_clinical_event(
        event_type="DIAGNOSIS_CONFIRMED",
        aggregate_type="diagnosis",
        aggregate_id="diag-1",
        tenant_id="t1",
        patient_id="p1",
        sequence=1,
        payload={...},
    )
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_ms() -> int:
    return int(time.time() * 1000)


class EventBuilder:
    """Fluent builder para ClinicalEvent (formato Event Store)."""

    def __init__(self) -> None:
        self._id: str = str(uuid.uuid4())
        self._type: str = ""
        self._aggregate_type: str = ""
        self._aggregate_id: str = ""
        self._tenant_id: str = "tenant-test"
        self._patient_id: str = "patient-test"
        self._actor_id: str = "actor-test"
        self._sequence: Optional[int] = None
        self._payload: Dict[str, Any] = {}
        self._event_datetime: datetime = _now()
        self._source_module: str = "neurodevelopmental"
        self._correlation_id: Optional[str] = None
        self._causation_id: Optional[str] = None

    def with_id(self, event_id: str) -> "EventBuilder":
        self._id = event_id
        return self

    def with_type(self, event_type: str) -> "EventBuilder":
        self._type = event_type
        return self

    def with_aggregate(
        self, aggregate_type: str, aggregate_id: str
    ) -> "EventBuilder":
        self._aggregate_type = aggregate_type
        self._aggregate_id = aggregate_id
        return self

    def with_tenant(self, tenant_id: str) -> "EventBuilder":
        self._tenant_id = tenant_id
        return self

    def with_patient(self, patient_id: str) -> "EventBuilder":
        self._patient_id = patient_id
        return self

    def with_actor(self, actor_id: str) -> "EventBuilder":
        self._actor_id = actor_id
        return self

    def with_sequence(self, sequence: int) -> "EventBuilder":
        self._sequence = sequence
        return self

    def with_payload(self, **payload: Any) -> "EventBuilder":
        """Merge keyword args no payload."""
        self._payload.update(payload)
        return self

    def with_payload_dict(self, payload: Dict[str, Any]) -> "EventBuilder":
        self._payload = dict(payload)
        return self

    def with_event_datetime(self, when: datetime) -> "EventBuilder":
        self._event_datetime = when
        return self

    def with_correlation_id(self, correlation_id: str) -> "EventBuilder":
        self._correlation_id = correlation_id
        return self

    def with_causation_id(self, causation_id: str) -> "EventBuilder":
        self._causation_id = causation_id
        return self

    def build(self) -> Dict[str, Any]:
        if not self._type:
            raise ValueError("EventBuilder: event_type is required")
        if not self._aggregate_type:
            raise ValueError("EventBuilder: aggregate_type is required")
        if not self._aggregate_id:
            raise ValueError("EventBuilder: aggregate_id is required")

        # sequence default: 0 (deve ser sobrescrito pelo caller se relevante)
        seq = self._sequence if self._sequence is not None else 0

        payload = dict(self._payload)
        # Enriquecer payload com infrastructure metadata (espelha o publisher)
        payload.setdefault("actor_id", self._actor_id)
        payload.setdefault("occurred_at", self._event_datetime.isoformat())
        payload.setdefault("aggregate_id", self._aggregate_id)
        if self._correlation_id is not None:
            payload["_correlation_id"] = self._correlation_id
        if self._causation_id is not None:
            payload["_causation_id"] = self._causation_id

        return {
            "id": self._id,
            "event_type": self._type,
            "aggregate_type": self._aggregate_type,
            "aggregate_id": self._aggregate_id,
            "tenant_id": self._tenant_id,
            "patient_id": self._patient_id,
            "sequence": seq,
            "payload": payload,
            "event_datetime": self._event_datetime.isoformat(),
            "source_module": self._source_module,
            "created_by": self._actor_id,
            "created_at": _now().isoformat(),
        }


def build_clinical_event(
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    tenant_id: str = "tenant-test",
    patient_id: str = "patient-test",
    sequence: int = 0,
    payload: Optional[Dict[str, Any]] = None,
    actor_id: str = "actor-test",
    event_datetime: Optional[datetime] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atalho one-liner para criar ClinicalEvent.

    Mantém ordem de inserção determinística (id auto-gerado) — útil para
    testes de replay.
    """
    return (
        EventBuilder()
        .with_type(event_type)
        .with_aggregate(aggregate_type, aggregate_id)
        .with_tenant(tenant_id)
        .with_patient(patient_id)
        .with_actor(actor_id)
        .with_sequence(sequence)
        .with_event_datetime(event_datetime or _now())
        .with_payload_dict(payload or {})
    ).build()
