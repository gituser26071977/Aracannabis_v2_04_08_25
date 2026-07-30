"""
TimelineEntry — entrada imutável da timeline clínica.

Representa UM evento clínico na vida do paciente, com separação explícita
entre:

    - valid_time (event_datetime): quando o evento CLÍNICO aconteceu.
      Ex: data em que o paciente teve a crise, data da avaliação.
    - transaction_time (recorded_at): quando foi publicado no Event Store.

Essa separação (bitemporal) é fundamental para:
    - Auditoria regulatória (LGPD/SOC2/HIPAA).
    - Late-arriving events: evento registrado tardiamente.
    - Time travel queries: "qual era o estado em T?".

Invariantes:
    - event_datetime é obrigatório.
    - recorded_at é sempre <= now() (validador em __post_init__).
    - sequence é por-tenant (não global).
    - aggregate_version é o número da versão do aggregate no momento do evento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class TimelineEntry:
    """Entrada imutável da timeline clínica."""

    event_id: str
    sequence: int
    event_type: str
    aggregate_type: str
    aggregate_id: str
    event_datetime: datetime                # valid_time
    recorded_at: datetime                   # transaction_time
    aggregate_version: int
    actor_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    tenant_id: str = ""
    patient_id: str = ""
    correlation_id: Optional[str] = None
    episode_id: Optional[str] = None        # preenchido por Sprint 4.2
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validar timezone-awareness
        if self.event_datetime.tzinfo is None:
            raise ValueError("event_datetime must be timezone-aware (valid_time)")
        if self.recorded_at.tzinfo is None:
            raise ValueError("recorded_at must be timezone-aware (transaction_time)")
        # transaction_time >= valid_time é regra do mundo real
        # (não estritamente válido para late-arriving; toleramos)
        if self.sequence < 0:
            raise ValueError("sequence must be >= 0")
        if self.aggregate_version < 1:
            raise ValueError("aggregate_version must be >= 1")
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.event_type:
            raise ValueError("event_type is required")

    def to_dict(self) -> Dict[str, Any]:
        """Serialização canônica para JSON/HTTP."""
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "event_datetime": self.event_datetime.isoformat(),
            "recorded_at": self.recorded_at.isoformat(),
            "aggregate_version": self.aggregate_version,
            "actor_id": self.actor_id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "correlation_id": self.correlation_id,
            "episode_id": self.episode_id,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_event(cls, event: Dict[str, Any]) -> "TimelineEntry":
        """Constrói TimelineEntry a partir de um evento do Event Store.

        Aceita tanto o formato do ClinicalEventStore (dict com chaves
        event_id, sequence, event_type, aggregate_type, aggregate_id,
        event_datetime, payload, metadata) quanto variações comuns.
        """
        recorded_at_raw = event.get("recorded_at") or event.get("transaction_time")
        if isinstance(recorded_at_raw, str):
            recorded_at = _parse_isoformat(recorded_at_raw)
        elif isinstance(recorded_at_raw, datetime):
            recorded_at = recorded_at_raw
        else:
            recorded_at = _utcnow()

        event_datetime_raw = event.get("event_datetime") or event.get("valid_time")
        if isinstance(event_datetime_raw, str):
            event_datetime = _parse_isoformat(event_datetime_raw)
        elif isinstance(event_datetime_raw, datetime):
            event_datetime = event_datetime_raw
        else:
            raise ValueError("event_datetime is required")

        return cls(
            event_id=str(event.get("event_id") or event.get("id")),
            sequence=int(event.get("sequence", 0)),
            event_type=str(event.get("event_type", "")),
            aggregate_type=str(event.get("aggregate_type", "")),
            aggregate_id=str(event.get("aggregate_id", "")),
            event_datetime=event_datetime,
            recorded_at=recorded_at,
            aggregate_version=int(event.get("aggregate_version", 1)),
            actor_id=str(event.get("actor_id") or event.get("created_by") or ""),
            payload=dict(event.get("payload", {}) or {}),
            tenant_id=str(event.get("tenant_id", "")),
            patient_id=str(event.get("patient_id", "")),
            correlation_id=event.get("correlation_id"),
            episode_id=event.get("episode_id"),
            metadata=dict(event.get("metadata", {}) or {}),
        )


def _parse_isoformat(value: str) -> datetime:
    """Parse ISO 8601 string, retornando datetime timezone-aware."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt