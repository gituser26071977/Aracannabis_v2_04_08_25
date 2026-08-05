"""
Explanation — Value Object de explicabilidade (cross-cutting).

AS-001 §7.5 — Toda alteração significativa SHALL produzir uma
Explanation referenciada por ``Expression.explanation_reference``
(AS-002 §4.3.1 — Explanation Reference SHALL never be empty).

Implementa o contrato de Explainability do Sprint 4.1:
``araos/clinical/explainability/Explanation``.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from types import MappingProxyType


@dataclass(frozen=True)
class Explanation:
    """Explicação registrada para uma mutação da Expression.

    A ``Explanation`` carrega a resposta à pergunta: "por que o estado
    da Expression mudou?". Sem Explanation não há Expression publicável
    (AS-002 §4.3.1).
    """

    explanation_id: str                                  # ULID
    analysis_type: str                                   # "expression_replacement", "hypothesis_added", ...
    question: str                                        # "Por que CBD mudou Confidence?"
    answer: str                                          # "Correlação observada em janela 30d"
    confidence: float                                    # 0.0–1.0
    method: str                                          # "rule_engine", "inference", "manual"
    data_window_start: datetime | None
    data_window_end: datetime | None
    variables: tuple[str, ...]
    contributing_event_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    analyst: str = "system"                              # "system" | user_id
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.explanation_id:
            raise ValueError("Explanation.explanation_id obrigatório")
        if not self.analysis_type:
            raise ValueError("Explanation.analysis_type obrigatório")
        if not self.question:
            raise ValueError("Explanation.question obrigatório")
        if not self.answer:
            raise ValueError("Explanation.answer obrigatório")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Explanation.confidence deve estar em [0.0, 1.0], recebido {self.confidence}"
            )
        if not self.method:
            raise ValueError("Explanation.method obrigatório")
        for label, ts in [
            ("data_window_start", self.data_window_start),
            ("data_window_end", self.data_window_end),
        ]:
            if ts is not None and ts.tzinfo is None:
                raise ValueError(f"Explanation.{label} deve ser timezone-aware (UTC)")
        if self.created_at.tzinfo is None:
            raise ValueError("Explanation.created_at deve ser timezone-aware (UTC)")

    @property
    def is_machine_generated(self) -> bool:
        return self.analyst == "system"
