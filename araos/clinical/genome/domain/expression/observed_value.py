"""
ObservedValue — valor clínico observado pela Expression.

AS-002 §3.3 — Observed Value: valor quantitativo ou qualitativo
capturado pelo evento. Pode ser ``null`` em Unknown State, mas
nunca ausente (§4.2.2 — SHALL always carry, mesmo que null).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObservedValue:
    """Valor clínico observado.

    O valor ``data`` pode ser ``None`` para representar Unknown State
    (AS-002 §3.14). Mas o campo ``data`` SHALL sempre estar presente
    (nunca ausente) conforme AS-002 §4.2.2.
    """

    data: Any  # int | float | str | dict | None (Unknown)
    unit: str | None = None
    qualifier: str | None = None

    @classmethod
    def unknown(cls) -> "ObservedValue":
        """Marcador canônico de Unknown State (§3.14)."""
        return cls(data=None, qualifier="unknown")

    @classmethod
    def unavailable(cls) -> "ObservedValue":
        """Marcador canônico de Unavailable State (§3.15)."""
        return cls(data=None, qualifier="unavailable")

    @property
    def is_unknown(self) -> bool:
        return self.data is None and self.qualifier == "unknown"

    @property
    def is_unavailable(self) -> bool:
        return self.data is None and self.qualifier == "unavailable"
