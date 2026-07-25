"""
Confidence — decimal [0.0, 1.0] representando certeza agregada.

AS-002 §3.4 + §4.2.1 — Confidence SHALL ser decimal no intervalo
fechado [0.0, 1.0]. Sempre explícita (ausência = 0.0 registrado).

AS-001 §6.6 — Confidence SHALL ser derivada, não primária.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Confidence:
    """Confiança agregada no intervalo [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError(
                f"Confidence.value deve ser numérico, recebido {type(self.value).__name__}"
            )
        if not 0.0 <= float(self.value) <= 1.0:
            raise ValueError(
                f"Confidence.value deve estar em [0.0, 1.0], recebido {self.value}"
            )

    @property
    def is_zero(self) -> bool:
        return self.value == 0.0

    @property
    def is_full(self) -> bool:
        return self.value == 1.0

    @classmethod
    def zero(cls) -> "Confidence":
        """Confidence explícita 0.0 (ausência de evidência)."""
        return cls(0.0)

    @classmethod
    def from_decimal(cls, value: float) -> "Confidence":
        return cls(value)

    def __float__(self) -> float:
        return float(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Confidence):
            return self.value == other.value
        if isinstance(other, (int, float)):
            return self.value == float(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)
