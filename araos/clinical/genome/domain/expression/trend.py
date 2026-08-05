"""
Trend — enumeração canônica para direção da Expression.

AS-002 §3.5 — Trend SHALL pertencer ao conjunto enumerado
{improving, stable, declining, oscillating, unknown}.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from enum import Enum


class Trend(str, Enum):
    """Direção observada da Expression ao longo do tempo."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    OSCILLATING = "oscillating"
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls.values()
