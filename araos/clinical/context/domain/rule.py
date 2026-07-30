"""
Rule + ContextSuggestion — Rule Engine ABC.

Sprint 4.2 — ADR-0003. Toda regra recebe eventos do paciente + contextos
existentes e retorna 0+ sugestões. Pure function (sem I/O).

Sugestões NUNCA alteram dados automaticamente — exigem confirmação humana.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.timeline.domain.window import TimeWindow


@dataclass(frozen=True)
class ContextSuggestion:
    """Sugestão de ClinicalContext gerada por uma regra.

    Esta é a UNIDADE de trabalho do Rule Engine. Cada sugestão vira
    uma Explanation (analysis_type=CONTEXT_SUGGESTION) registrada
    no ExplanationRegistry, e opcionalmente um evento
    CLINICAL_CONTEXT_SUGGESTED.
    """

    suggestion_id: str
    context_type: ContextType
    title: str
    description: str
    reason: str
    confidence: float
    rule_id: str
    contributing_event_ids: List[str]
    suggested_window: TimeWindow
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.suggestion_id:
            raise ValueError("suggestion_id is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")
        if not self.rule_id:
            raise ValueError("rule_id is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.contributing_event_ids:
            raise ValueError("contributing_event_ids must not be empty")
        if not self.limitations:
            raise ValueError(
                "limitations must have at least 1 entry — toda sugestão tem limitações"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "context_type": self.context_type.value,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "contributing_event_ids": list(self.contributing_event_ids),
            "suggested_window": self.suggested_window.to_dict(),
            "supporting_data": dict(self.supporting_data),
            "assumptions": list(self.assumptions),
            "limitations": list(self.limitations),
        }


class Rule(ABC):
    """Regra do Rule Engine. Pure function (sem I/O)."""

    rule_id: str
    description: str
    min_confidence: float

    @abstractmethod
    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        """Avalia os eventos e retorna 0+ sugestões.

        Args:
            events: eventos clínicos do paciente (ordenados por sequence).
                Cada evento é um dict com chaves: event_type, event_datetime,
                payload, tenant_id, patient_id, event_id, etc.
            existing_contexts: ClinicalContexts já criados para o paciente
                (para deduplicação).

        Returns:
            Lista de sugestões. Vazio se regra não se aplica.
        """


def _now() -> datetime:
    return datetime.now(timezone.utc)
