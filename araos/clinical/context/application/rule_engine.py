"""
RuleEngine — orquestrador das regras. Executa todas as regras e consolida
resultados com deduplicação.

Sprint 4.2 — ADR-0003.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.rule import ContextSuggestion, Rule


@dataclass(frozen=True)
class RuleEvaluationResult:
    """Resultado consolidado da execução do Rule Engine."""
    patient_id: str
    tenant_id: str
    suggestions: List[ContextSuggestion] = field(default_factory=list)
    rules_evaluated: int = 0
    rules_fired: List[str] = field(default_factory=list)
    events_analyzed: int = 0
    contexts_considered: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "rules_evaluated": self.rules_evaluated,
            "rules_fired": self.rules_fired,
            "events_analyzed": self.events_analyzed,
            "contexts_considered": self.contexts_considered,
            "n_suggestions": len(self.suggestions),
        }


class RuleEngine:
    """Avalia regras sobre eventos + contextos existentes.

    Stateless: mesma entrada → mesma saída. Sem mutação.
    """

    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        from araos.clinical.context.application.builtin_rules import default_rules
        self._rules: List[Rule] = rules if rules is not None else default_rules()

    def register(self, rule: Rule) -> None:
        """Adiciona regra (extensibilidade)."""
        self._rules.append(rule)

    @property
    def rules(self) -> List[Rule]:
        return list(self._rules)

    def evaluate(
        self,
        tenant_id: str,
        patient_id: str,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> RuleEvaluationResult:
        """Executa todas as regras, deduplica, ordena por confidence desc."""
        all_suggestions: List[ContextSuggestion] = []
        rules_fired: List[str] = []

        for rule in self._rules:
            try:
                suggestions = rule.evaluate(events, existing_contexts)
            except Exception:    # pragma: no cover — defensive
                continue
            for s in suggestions:
                if s.confidence < rule.min_confidence:
                    continue
                all_suggestions.append(s)
            if suggestions:
                rules_fired.append(rule.rule_id)

        # Dedup: mesma (context_type, contributing_event_ids tuple) → descarta
        deduped: List[ContextSuggestion] = []
        seen_keys: set = set()
        for s in sorted(all_suggestions, key=lambda x: x.confidence, reverse=True):
            key = (s.context_type.value, tuple(sorted(s.contributing_event_ids)))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(s)

        return RuleEvaluationResult(
            patient_id=patient_id,
            tenant_id=tenant_id,
            suggestions=deduped,
            rules_evaluated=len(self._rules),
            rules_fired=rules_fired,
            events_analyzed=len(events),
            contexts_considered=len(existing_contexts),
        )
