"""
ContextRelationship — grafo de relacionamentos entre ClinicalContexts.

Sprint 4.2 — ADR-0003. Permite modelar influência entre contextos:

    SchoolContext ──influenced──→ ClinicalEpisode (behavioral)
                              │
                              └──related_to──→ MedicationContext
                                                │
                                                └──impacted──→ Outcome
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class RelationshipType(str, Enum):
    """Tipo de relacionamento entre contextos."""
    INFLUENCED = "influenced"            # A influenciou B
    RELATED_TO = "related_to"            # associação geral
    IMPACTED = "impacted"                # A impactou B (medida de outcome)
    PRECEDED = "preceded"                # A precedeu B temporalmente
    CAUSED = "caused"                    # A causou B (raro, requer evidência forte)
    CO_OCCURRED_WITH = "co_occurred"     # sobreposição temporal

    @classmethod
    def values(cls) -> list[str]:
        return [r.value for r in cls]


@dataclass(frozen=True)
class ContextRelationship:
    """Aresta do grafo de ClinicalContexts."""

    relationship_id: str
    tenant_id: str
    source_context_id: str
    target_context_id: str
    relationship_type: RelationshipType
    confidence: float
    created_at: datetime
    created_by: str
    evidence_event_ids: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.relationship_id:
            raise ValueError("relationship_id is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.source_context_id:
            raise ValueError("source_context_id is required")
        if not self.target_context_id:
            raise ValueError("target_context_id is required")
        if self.source_context_id == self.target_context_id:
            raise ValueError(
                "self-loop not allowed: source_context_id == target_context_id"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if not self.created_by:
            raise ValueError("created_by is required")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "tenant_id": self.tenant_id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "relationship_type": self.relationship_type.value,
            "confidence": self.confidence,
            "evidence_event_ids": list(self.evidence_event_ids),
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
        }
