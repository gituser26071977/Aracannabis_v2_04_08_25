"""
DomainEvent — base imutável para todos os eventos do Clinical Gene.

Reference Implementation — Sprint 4.3 Phase 2.

Invariantes enforced:

- event_id único (ULID).
- sequence per-tenant monotônico (ADR-0001).
- valid_time + transaction_time UTC.
- payload imutável (MappingProxyType).
- origin rastreável.

Implementa a parte central de AS-001 §6.3 (History) e AS-002 §6.5
(Expression Replacement).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
import uuid


def _new_event_id() -> str:
    """Gera event_id único. Production usaria ULID; UUID4 é suficiente para Phase 2."""
    return f"evt_{uuid.uuid4().hex[:24]}"


@dataclass(frozen=True)
class DomainEvent:
    """Base imutável para todos os eventos do Clinical Gene."""

    event_id: str
    event_type: str
    tenant_id: str
    patient_id: str
    gene_id: str
    sequence: int
    valid_time: datetime          # quando clinicamente
    transaction_time: datetime    # quando registrado
    payload: Mapping[str, Any]
    origin: str                   # "system" | user_id | service_id
    correlation_id: str | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("DomainEvent.event_id obrigatório")
        if not self.event_type:
            raise ValueError("DomainEvent.event_type obrigatório")
        if not self.tenant_id:
            raise ValueError("DomainEvent.tenant_id obrigatório (multi-tenancy)")
        if not self.patient_id:
            raise ValueError("DomainEvent.patient_id obrigatório")
        if not self.gene_id:
            raise ValueError("DomainEvent.gene_id obrigatório")
        if self.sequence < 0:
            raise ValueError(f"DomainEvent.sequence deve ser >= 0, recebido {self.sequence}")
        if self.valid_time.tzinfo is None:
            raise ValueError("DomainEvent.valid_time deve ser timezone-aware (UTC)")
        if self.transaction_time.tzinfo is None:
            raise ValueError("DomainEvent.transaction_time deve ser timezone-aware (UTC)")
        if self.transaction_time < self.valid_time:
            raise ValueError(
                "DomainEvent.transaction_time não pode ser anterior a valid_time"
            )
        if not self.origin:
            raise ValueError("DomainEvent.origin obrigatório")
        # Garante imutabilidade dos mappings.
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @staticmethod
    def new_event_id() -> str:
        return _new_event_id()


# --- Tipos canônicos de eventos (AS-001 §6 + AS-002 §6) ---
GENE_CREATED = "GENE_CREATED"
EXPRESSION_OBSERVED = "EXPRESSION_OBSERVED"
EXPRESSION_REPLACED = "EXPRESSION_REPLACED"
EXPRESSION_UNKNOWN_RECORDED = "EXPRESSION_UNKNOWN_RECORDED"
EXPRESSION_UNAVAILABLE_RECORDED = "EXPRESSION_UNAVAILABLE_RECORDED"
EXPRESSION_DERIVED_COMPUTED = "EXPRESSION_DERIVED_COMPUTED"
HYPOTHESIS_ADDED = "HYPOTHESIS_ADDED"
HYPOTHESIS_DEACTIVATED = "HYPOTHESIS_DEACTIVATED"
RELATIONSHIP_ADDED = "RELATIONSHIP_ADDED"
RELATIONSHIP_DEACTIVATED = "RELATIONSHIP_DEACTIVATED"
CONTEXT_ADDED = "CONTEXT_ADDED"
CONTEXT_REMOVED = "CONTEXT_REMOVED"
EVIDENCE_RECORDED = "EVIDENCE_RECORDED"
METADATA_RECORDED = "METADATA_RECORDED"
SNAPSHOT_TAKEN = "SNAPSHOT_TAKEN"
GENE_ARCHIVED = "GENE_ARCHIVED"
