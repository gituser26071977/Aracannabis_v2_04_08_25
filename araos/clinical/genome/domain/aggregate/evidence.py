"""
Evidence Reference — ponteiro imutável para um Domain Event.

AS-001 §6.5 + AS-002 §4.3.2 — Evidence SHALL ser 1..* e SHALL NOT
ser reduzida após a alteração.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EvidenceReference:
    """Referência imutável a um Domain Event que fundamenta a Expression."""

    event_id: str
    event_type: str
    observed_at: datetime
    contributing_weight: float = 1.0  # peso relativo da evidência

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("EvidenceReference.event_id obrigatório")
        if not self.event_type:
            raise ValueError("EvidenceReference.event_type obrigatório")
        if self.observed_at.tzinfo is None:
            raise ValueError("EvidenceReference.observed_at deve ser timezone-aware (UTC)")
        if not 0.0 <= self.contributing_weight <= 1.0:
            raise ValueError(
                f"EvidenceReference.contributing_weight deve estar em [0.0, 1.0], "
                f"recebido {self.contributing_weight}"
            )
