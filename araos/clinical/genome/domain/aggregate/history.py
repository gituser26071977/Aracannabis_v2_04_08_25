"""
History — audit chain canônico do Gene (AS-001 §6.3).

Invariantes:

- AS-001 Requisito 6.3.1 — Append-only.
- AS-001 Requisito 6.3.2 — Cada entrada referencia event_id único + sequence.
- AS-001 Requisito 6.3.3 — Toda mutação produz ≥ 1 entrada em History.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator


# implements:
#   AS-001-REQ-0065 — Append-only
#   AS-001-REQ-0066 — event_id + sequence preservados
#   AS-001-REQ-0067 — Toda mutação produz ≥ 1 entrada


@dataclass(frozen=True)
class HistoryEntry:
    """Entrada imutável no audit chain do Gene."""

    event_id: str
    sequence: int
    event_type: str
    occurred_at: datetime
    recorded_at: datetime
    payload_summary: str  # descrição textual da mutação
    origin: str           # "system" | user_id | service_id

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("HistoryEntry.event_id obrigatório")
        if self.sequence < 0:
            raise ValueError(f"HistoryEntry.sequence deve ser >= 0, recebido {self.sequence}")
        if not self.event_type:
            raise ValueError("HistoryEntry.event_type obrigatório")
        if self.occurred_at.tzinfo is None:
            raise ValueError("HistoryEntry.occurred_at deve ser timezone-aware (UTC)")
        if self.recorded_at.tzinfo is None:
            raise ValueError("HistoryEntry.recorded_at deve ser timezone-aware (UTC)")
        if not self.payload_summary:
            raise ValueError("HistoryEntry.payload_summary obrigatório")


@dataclass(frozen=True)
class History:
    """History append-only do Gene."""

    entries: tuple[HistoryEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for i in range(1, len(self.entries)):
            if self.entries[i].sequence <= self.entries[i - 1].sequence:
                raise ValueError(
                    f"History SHALL ser monotônico por sequence: "
                    f"entrada {i-1} seq={self.entries[i-1].sequence} "
                    f">= entrada {i} seq={self.entries[i].sequence}"
                )

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self) -> Iterator[HistoryEntry]:
        return iter(self.entries)

    def append(self, entry: HistoryEntry) -> "History":
        """Append nova entrada preservando ordem por sequence."""
        if not isinstance(entry, HistoryEntry):
            raise TypeError(
                f"History.append exige HistoryEntry, recebido {type(entry).__name__}"
            )
        return History(tuple(self.entries) + (entry,))

    def last_sequence(self) -> int:
        return self.entries[-1].sequence if self.entries else -1

    def contains_event(self, event_id: str) -> bool:
        return any(e.event_id == event_id for e in self.entries)
