"""
Context Dependency — modulador semântico da Expression.

AS-001 §6.4 — ContextDependencies SHALL referenciar apenas Clinical
Contexts válidos no escopo ``(tenant_id, patient_id)``.

AS-002 §4.5.1 — Context References SHALL referenciar apenas Clinical
Contexts válidos no escopo do Gene.

AS-002 §4.5.2 — Mudança em Context SHALL disparar reavaliação.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ContextDependency:
    """Dependência de um Clinical Context na Expression do Gene."""

    context_id: str
    context_type: str      # "medication", "school", "family", "behavioral_phase", etc.
    effective_from: datetime
    effective_until: datetime | None = None  # None = ainda ativo
    weight: float = 1.0   # peso do contexto na modulação

    def __post_init__(self) -> None:
        if not self.context_id:
            raise ValueError("ContextDependency.context_id obrigatório")
        if not self.context_type:
            raise ValueError("ContextDependency.context_type obrigatório")
        if self.effective_from.tzinfo is None:
            raise ValueError("ContextDependency.effective_from deve ser timezone-aware (UTC)")
        if self.effective_until is not None and self.effective_until.tzinfo is None:
            raise ValueError("ContextDependency.effective_until deve ser timezone-aware (UTC)")
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError(
                "ContextDependency.effective_until não pode ser anterior a effective_from"
            )
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                f"ContextDependency.weight deve estar em [0.0, 1.0], recebido {self.weight}"
            )

    def is_active_at(self, when: datetime) -> bool:
        """Verifica se o contexto está ativo no momento ``when``."""
        if when.tzinfo is None:
            raise ValueError("when deve ser timezone-aware (UTC)")
        if when < self.effective_from:
            return False
        if self.effective_until is not None and when >= self.effective_until:
            return False
        return True
