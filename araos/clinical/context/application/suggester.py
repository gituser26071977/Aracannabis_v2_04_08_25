"""
ContextSuggester — composição de Rule Engine + Explanation Registry.

Sprint 4.2 — ADR-0003. Toda sugestão vira:
    1. Uma Explanation (analysis_type=CONTEXT_SUGGESTION) registrada.
    2. Um evento CLINICAL_CONTEXT_SUGGESTED no Event Store.

Nenhuma sugestão cria ClinicalContext automaticamente — exige confirmação
humana via POST /contexts/{suggestion_id}/confirm.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from araos.clinical.context.application.rule_engine import RuleEngine
from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.rule import ContextSuggestion
from araos.clinical.explainability import AnalysisType, Explanation
from araos.clinical.explainability.registry import (
    ExplanationRegistry,
    new_explanation_id,
)


_logger = logging.getLogger(__name__)


class _EventPublisher(Protocol):
    def publish(self, **kwargs: Any) -> str: ...


class ContextSuggester:
    """Compõe RuleEngine + ExplanationRegistry.

    Para cada sugestão:
        - Cria Explanation com analysis_type=CONTEXT_SUGGESTION.
        - Registra no ExplanationRegistry.
        - Publica evento CLINICAL_CONTEXT_SUGGESTED.
    """

    def __init__(
        self,
        rule_engine: RuleEngine,
        explanation_registry: ExplanationRegistry,
        event_publisher: Optional[_EventPublisher] = None,
    ) -> None:
        self._rule_engine = rule_engine
        self._registry = explanation_registry
        self._publisher = event_publisher

    def suggest(
        self,
        tenant_id: str,
        patient_id: str,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
        analyst: str = "system",
    ) -> List[ContextSuggestion]:
        """Executa regras + registra Explanation + emite evento (se publisher).

        Retorna lista de sugestões (com explanation_id preenchido).
        """
        result = self._rule_engine.evaluate(
            tenant_id=tenant_id,
            patient_id=patient_id,
            events=events,
            existing_contexts=existing_contexts,
        )
        if not result.suggestions:
            return []

        explanations: List[Explanation] = []
        for sug in result.suggestions:
            explanation = self._build_explanation(
                tenant_id=tenant_id,
                patient_id=patient_id,
                suggestion=sug,
                events=events,
                analyst=analyst,
            )
            explanations.append(explanation)

        # Bulk register
        for exp in explanations:
            try:
                self._registry.register(exp)
            except Exception as e:    # pragma: no cover
                _logger.error(
                    "explanation_register_failed",
                    extra={"explanation_id": exp.explanation_id, "error": str(e)},
                )

        # Publica eventos
        if self._publisher is not None:
            for sug, exp in zip(result.suggestions, explanations):
                try:
                    self._publisher.publish(
                        tenant_id=tenant_id,
                        patient_id=patient_id,
                        event_type="CLINICAL_CONTEXT_SUGGESTED",
                        event_datetime=datetime.now(timezone.utc),
                        source_module="intelligence",
                        payload={
                            "context_id": None,    # ainda não criado
                            "context_type": sug.context_type.value,
                            "rule_id": sug.rule_id,
                            "confidence": sug.confidence,
                            "contributing_event_ids": sug.contributing_event_ids,
                            "explanation_id": exp.explanation_id,
                            "suggestion_id": sug.suggestion_id,
                        },
                        metadata={"suggestion_id": sug.suggestion_id},
                    )
                except Exception as e:    # pragma: no cover
                    _logger.warning(
                        "context_suggested_publish_failed",
                        extra={"suggestion_id": sug.suggestion_id, "error": str(e)},
                    )

        return result.suggestions

    def _build_explanation(
        self,
        tenant_id: str,
        patient_id: str,
        suggestion: ContextSuggestion,
        events: List[Dict[str, Any]],
        analyst: str,
    ) -> Explanation:
        from araos.clinical.timeline.domain.variable import (
            VariableSource,
            VariableSpec,
        )

        contributing = [
            ev for ev in events
            if (ev.get("event_id") or ev.get("id")) in suggestion.contributing_event_ids
        ]
        variables = [
            VariableSpec(
                name=f"event:{ev.get('event_type', 'unknown')}",
                source=VariableSource.EVENT_PAYLOAD,
                source_event_type=ev.get("event_type", ""),
                value_extractor="event_id",
            )
            for ev in contributing
        ] or [
            VariableSpec(
                name="events:patient",
                source=VariableSource.EVENT_PAYLOAD,
                source_event_type="*",
                value_extractor="count",
            ),
        ]

        return Explanation(
            explanation_id=new_explanation_id(),
            analysis_id=suggestion.suggestion_id,
            analysis_type=AnalysisType.CONTEXT_SUGGESTION,
            question=f"Por que o contexto '{suggestion.context_type.value}' foi sugerido?",
            answer=(
                f"Regra '{suggestion.rule_id}' disparou com base em "
                f"{len(suggestion.contributing_event_ids)} evento(s). "
                f"Confiança: {suggestion.confidence:.0%}. {suggestion.reason}"
            ),
            confidence=suggestion.confidence,
            method=f"rule_engine:{suggestion.rule_id}",
            data_window=suggestion.suggested_window,
            variables=variables,
            contributing_event_ids=list(suggestion.contributing_event_ids),
            assumptions=list(suggestion.assumptions),
            limitations=list(suggestion.limitations),
            created_at=datetime.now(timezone.utc),
            analyst=analyst,
            tenant_id=tenant_id,
            correlation_id=None,
        )
