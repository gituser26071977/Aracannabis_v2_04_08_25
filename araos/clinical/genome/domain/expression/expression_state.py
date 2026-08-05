"""
Expression State — estados canônicos da Clinical Expression.

AS-002 §3.14, §3.15, §3.16, §3.17:

- CANONICAL: Current Expression residente no Aggregate Root Gene.
- UNKNOWN: observada mas com evidência insuficiente.
- UNAVAILABLE: Gene não-observado (não confundir com null).
- DERIVED: calculada a partir do canonical (projeção secundária).
- HISTORICAL: foi Current em momento anterior, agora substituída.

Implementação: nunca usar ``None`` para significado clínico
(AS-002 §3.14 + tarefa Sprint 4.3 Phase 2).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from enum import Enum


class ExpressionState(str, Enum):
    """Estado canônico da Expression em seu ciclo de vida."""

    CANONICAL = "canonical"            # §3.17 — Current Expression
    HISTORICAL = "historical"          # AS-002 §6.2 — substituída
    UNKNOWN = "unknown"                # §3.14 — observada sem evidência
    UNAVAILABLE = "unavailable"        # §3.15 — Gene não-observado
    DERIVED = "derived"                # §3.16 — calculada a partir do canonical

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls.values()
