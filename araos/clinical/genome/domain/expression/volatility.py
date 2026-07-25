"""
Volatility — enumeração canônica para variabilidade da Expression.

AS-002 §3.6 — Volatility SHALL pertencer ao conjunto enumerado
{low, medium, high, unknown}.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from enum import Enum


class Volatility(str, Enum):
    """Variabilidade observada da Expression."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls.values()
