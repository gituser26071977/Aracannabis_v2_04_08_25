"""
ContextStatus — state machine canônico do ClinicalContext.

Sprint 4.2 — ADR-0003. Define as 7 fases válidas do agregado.

State machine:

                    ┌─→ Rejected
                    │
Planned ─→ Suggested ─→ Active ─→ Completed
              │         │  ↑       │
              │         ↓  │       ↓
              │       Cancelled   Archived
              │
              └────── (Created manually from Planned/Suggested)

Reopened ← Completed (when new events re-open it)

Transições válidas (state machine enforced em ClinicalContext.transition_to):

    Planned     → Suggested | Active
    Suggested   → Active | Rejected
    Active      → Completed | Cancelled | Archived
    Completed   → Active (reopen)
    Cancelled   → (terminal)
    Archived    → (terminal)
    Rejected    → (terminal)
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class ContextStatus(str, Enum):
    """Status do ClinicalContext."""
    PLANNED = "Planned"
    SUGGESTED = "Suggested"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    ARCHIVED = "Archived"
    REJECTED = "Rejected"

    @property
    def is_terminal(self) -> bool:
        """Status terminais não aceitam mais transições."""
        return self in (
            ContextStatus.REJECTED,
            ContextStatus.CANCELLED,
            ContextStatus.ARCHIVED,
        )

    @property
    def is_active_or_suggested(self) -> bool:
        """Status que indicam contexto ativo/pendente (para queries)."""
        return self in (ContextStatus.ACTIVE, ContextStatus.SUGGESTED)

    @classmethod
    def valid_transitions(cls) -> Dict["ContextStatus", Set["ContextStatus"]]:
        """State machine canônica."""
        return {
            cls.PLANNED: {cls.SUGGESTED, cls.ACTIVE, cls.CANCELLED},
            cls.SUGGESTED: {cls.ACTIVE, cls.REJECTED, cls.PLANNED},
            cls.ACTIVE: {cls.COMPLETED, cls.CANCELLED, cls.ARCHIVED},
            cls.COMPLETED: {cls.ACTIVE},   # reopen
            cls.CANCELLED: set(),           # terminal
            cls.ARCHIVED: set(),             # terminal
            cls.REJECTED: set(),             # terminal
        }

    def can_transition_to(self, target: "ContextStatus") -> bool:
        """Verifica se transição é permitida."""
        return target in self.valid_transitions().get(self, set())

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]


# ─── Status endpoints (terminal closure) ─────────────────────────────

TERMINAL_STATUSES = frozenset({
    ContextStatus.COMPLETED,
    ContextStatus.CANCELLED,
    ContextStatus.ARCHIVED,
    ContextStatus.REJECTED,
})


def is_terminal(status: ContextStatus) -> bool:
    return status in TERMINAL_STATUSES


def requires_end_date(status: ContextStatus) -> bool:
    """Completed/Cancelled/Archived exigem end_date."""
    return status in (
        ContextStatus.COMPLETED,
        ContextStatus.CANCELLED,
        ContextStatus.ARCHIVED,
    )


def requires_confirmation(status: ContextStatus) -> bool:
    """Status que exigem confirmed_by/confirmed_at."""
    return status in (ContextStatus.ACTIVE, ContextStatus.COMPLETED)
