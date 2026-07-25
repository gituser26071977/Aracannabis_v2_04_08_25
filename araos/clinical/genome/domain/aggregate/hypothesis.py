"""
Hypothesis — interpretação alternativa concorrente.

AS-001 §6.7 — Hypotheses SHALL coexistir sem exclusividade.
AS-002 §4.9.2 — Hypothesis SHALL NEVER substituir Expression.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from types import MappingProxyType


@dataclass(frozen=True)
class Hypothesis:
    """Hipótese interpretativa concorrente sobre o estado do Gene."""

    hypothesis_id: str
    description: str
    weight: float                       # ∈ [0.0, 1.0]
    supporting_event_ids: tuple[str, ...]
    confidence: float                   # ∈ [0.0, 1.0]
    is_active: bool = True
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("Hypothesis.hypothesis_id obrigatório")
        if not self.description:
            raise ValueError("Hypothesis.description obrigatório")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                f"Hypothesis.weight deve estar em [0.0, 1.0], recebido {self.weight}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Hypothesis.confidence deve estar em [0.0, 1.0], recebido {self.confidence}"
            )
        if self.created_at.tzinfo is None:
            raise ValueError("Hypothesis.created_at deve ser timezone-aware (UTC)")

    def deactivate(self) -> "Hypothesis":
        """Desativa a hipótese (imutável — retorna nova)."""
        return Hypothesis(
            hypothesis_id=self.hypothesis_id,
            description=self.description,
            weight=self.weight,
            supporting_event_ids=self.supporting_event_ids,
            confidence=self.confidence,
            is_active=False,
            created_at=self.created_at,
            metadata=self.metadata,
        )
