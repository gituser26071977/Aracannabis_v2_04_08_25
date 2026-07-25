"""
TimeWindow — janela temporal para queries e análises.

Usado por:
    - TimelineQuery (Sprint 4.1): filtros de intervalo.
    - Analytics (Sprint 4.3): período de análise.
    - Correlation (Sprint 4.4): janela de correlação.
    - Cohort (Sprint 4.4): restrições temporais de critério.

Invariantes:
    - start <= end (validado).
    - Se duration_days fornecido, start + duration = end.
    - Datas sempre timezone-aware.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass(frozen=True)
class TimeWindow:
    """Janela temporal imutável."""

    start: datetime
    end: datetime
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("start and end must be timezone-aware")
        if self.start > self.end:
            raise ValueError("start must be <= end")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    @property
    def duration_days(self) -> float:
        return self.duration.total_seconds() / 86400.0

    def contains(self, when: datetime) -> bool:
        """True se `when` está dentro da janela (inclusivo nos extremos)."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        return self.start <= when <= self.end

    @classmethod
    def last_days(cls, days: int, end: Optional[datetime] = None,
                  label: Optional[str] = None) -> "TimeWindow":
        """Janela dos últimos N dias (até `end`, default=now)."""
        if end is None:
            end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        return cls(start=start, end=end, label=label or f"last_{days}_days")

    @classmethod
    def between(cls, start: datetime, end: datetime,
                label: Optional[str] = None) -> "TimeWindow":
        return cls(start=start, end=end, label=label)

    def to_dict(self) -> dict:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "label": self.label,
            "duration_days": self.duration_days,
        }