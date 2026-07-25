"""
Relationship — aresta Knowledge-Graph-ready entre Genes.

AS-001 §6.8 — Cada Relationship SHALL especificar: target_gene_id,
relationship_type, confidence, evidence_event_ids.

Tipos canônicos: influences, co_occurs_with, precedes, antagonizes,
amplifies.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# AS-001 Requisito 6.8.2
CANONICAL_RELATIONSHIP_TYPES: tuple[str, ...] = (
    "influences",
    "co_occurs_with",
    "precedes",
    "antagonizes",
    "amplifies",
)


@dataclass(frozen=True)
class Relationship:
    """Aresta entre este Gene e outro Gene."""

    target_gene_id: str
    relationship_type: str
    confidence: float
    evidence_event_ids: tuple[str, ...]
    created_at: datetime
    is_directed: bool = True
    is_active: bool = True

    def __post_init__(self) -> None:
        if not self.target_gene_id:
            raise ValueError("Relationship.target_gene_id obrigatório")
        if self.relationship_type not in CANONICAL_RELATIONSHIP_TYPES:
            raise ValueError(
                f"Relationship.relationship_type '{self.relationship_type}' "
                f"não está entre os tipos canônicos: {CANONICAL_RELATIONSHIP_TYPES}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Relationship.confidence deve estar em [0.0, 1.0], recebido {self.confidence}"
            )
        if not self.evidence_event_ids:
            raise ValueError(
                "Relationship.evidence_event_ids SHALL conter ao menos 1 event_id "
                "(AS-001 §6.8.1)"
            )
        if self.created_at.tzinfo is None:
            raise ValueError("Relationship.created_at deve ser timezone-aware (UTC)")

    def deactivate(self) -> "Relationship":
        return Relationship(
            target_gene_id=self.target_gene_id,
            relationship_type=self.relationship_type,
            confidence=self.confidence,
            evidence_event_ids=self.evidence_event_ids,
            created_at=self.created_at,
            is_directed=self.is_directed,
            is_active=False,
        )
