"""
Explanation — value object de explicabilidade.

Toda análise de inteligência clínica DEVE emitir uma Explanation.

Invariantes (enforced em __post_init__):
    - analysis_id, analysis_type, method, question, answer não-vazios.
    - confidence ∈ [0.0, 1.0].
    - data_window é TimeWindow com start <= end.
    - variables ≥ 1 (toda análise opera sobre ≥1 variável).
    - contributing_event_ids ≥ 1 quando há dados analisados.
    - limitations ≥ 1 (sempre — nenhuma análise é livre de limitações).

Campos:
    - question/answer  → linguagem natural (mostrado ao clínico).
    - method           → "pearson", "spearman", "linear_regression", etc.
    - confidence       → [0.0, 1.0] — quão confiante o método está.
    - data_window      → período analisado.
    - variables        → spec das variáveis (reusa VariableSpec).
    - contributing_event_ids → 5–20 eventos que mais contribuíram.
    - assumptions      → premissas explícitas (ex: "linearidade").
    - limitations      → o que NÃO podemos afirmar (ex: "correlação ≠ causalidade").
    - analyst          → "system" ou user_id que disparou a análise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from araos.clinical.timeline.domain.variable import VariableSpec
from araos.clinical.timeline.domain.window import TimeWindow


class AnalysisType(str, Enum):
    """Tipo da análise explicada."""
    CORRELATION = "correlation"
    TREND = "trend"
    ANOMALY = "anomaly"
    HYPOTHESIS = "hypothesis"
    EPISODE_SUGGESTION = "episode_suggestion"
    CONTEXT_SUGGESTION = "context_suggestion"
    COHORT_EVALUATION = "cohort_evaluation"
    FORECAST = "forecast"


@dataclass(frozen=True)
class Explanation:
    """Explicabilidade imutável de uma análise."""

    explanation_id: str
    analysis_id: str
    analysis_type: AnalysisType
    question: str
    answer: str
    confidence: float
    method: str
    data_window: TimeWindow
    variables: List[VariableSpec]
    contributing_event_ids: List[str]
    assumptions: List[str]
    limitations: List[str]
    created_at: datetime
    analyst: str = "system"
    tenant_id: str = ""
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.explanation_id:
            raise ValueError("explanation_id is required")
        if not self.analysis_id:
            raise ValueError("analysis_id is required")
        if not self.question:
            raise ValueError("question is required (pergunta clínica)")
        if not self.answer:
            raise ValueError("answer is required (resposta da análise)")
        if not self.method:
            raise ValueError("method is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        if not self.variables:
            raise ValueError("variables must have at least 1 entry")
        if not self.limitations:
            raise ValueError(
                "limitations must have at least 1 entry "
                "(toda análise tem limitações — explicitá-las é obrigatório)"
            )
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        # contributing_event_ids pode ser vazio apenas se limitations explica
        # (ex: "insufficient data — 0 events in window")
        if not self.contributing_event_ids and "insufficient_data" not in self.method:
            # Tolerância: se limitations menciona falta de dados, pode estar vazio
            if not any("dados" in l.lower() or "events" in l.lower() or "data" in l.lower()
                       for l in self.limitations):
                raise ValueError(
                    "contributing_event_ids empty + limitations does not "
                    "explain data scarcity — adicionar limitation explicando"
                )

    @property
    def n_events_analyzed(self) -> int:
        return len(self.contributing_event_ids)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type.value,
            "question": self.question,
            "answer": self.answer,
            "confidence": self.confidence,
            "method": self.method,
            "data_window": self.data_window.to_dict(),
            "variables": [v.to_dict() for v in self.variables],
            "contributing_event_ids": list(self.contributing_event_ids),
            "assumptions": list(self.assumptions),
            "limitations": list(self.limitations),
            "created_at": self.created_at.isoformat(),
            "analyst": self.analyst,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
            "n_events_analyzed": self.n_events_analyzed,
        }