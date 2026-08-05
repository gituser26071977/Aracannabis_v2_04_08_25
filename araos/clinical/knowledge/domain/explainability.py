"""
Explainability Pipeline — InferenceExplanation cross-cutting.

Sprint 4.4 — Clinical Knowledge Engine v1.0.

Toda inferência (correlation, hypothesis, cohort, graph_edge, research)
DEVE emitir uma ``InferenceExplanation`` com a totalidade dos elementos
que contribuíram para a conclusão:

    - quais genes participaram
    - quais expressões participaram
    - quais eventos participaram
    - quais correlações participaram
    - quais hipóteses participaram
    - justificativa textual (claim)
    - método aplicado
    - confidence
    - limitações declaradas
    - pressupostos assumidos

Invariante cross-cutting:
    Nenhuma inferência pode ser "caixa preta". Toda análise carrega
    consigo a explicação completa de sua origem e seus limites.

Padrão: AS-001 §7.5 (Explainability cross-cutting para Gene),
        AS-002 §4.3.1 (Explanation reference para Expression).

Pure domain: zero dependências externas.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence


class InferenceType(str, Enum):
    """Tipos canônicos de inferência do Knowledge Engine."""

    CORRELATION = "correlation"
    HYPOTHESIS = "hypothesis"
    COHORT = "cohort"
    GRAPH_EDGE = "graph_edge"
    RESEARCH = "research"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    """Gera ID curto (prefix + 8 chars hex)."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass(frozen=True)
class InferenceExplanation:
    """Explicação completa de uma inferência do Knowledge Engine.

    Implementa o princípio: "toda inferência deve responder por quê,
    com quais dados, em qual janela, com qual confiança, e quais
    limitações".
    """

    explanation_id: str
    inference_type: InferenceType
    claim: str                              # afirmação produzida pela inferência
    method: str                             # método aplicado ("pearson", "rule_1", "cohort_eq", ...)
    participating_genes: tuple[str, ...]    # gene_ids (URN suffix) que participaram
    participating_expressions: tuple[str, ...]  # expression refs (sequence:gene_id)
    participating_events: tuple[str, ...]   # event_ids
    participating_correlations: tuple[str, ...]  # correlation_ids
    participating_hypotheses: tuple[str, ...]    # hypothesis_ids
    confidence: float                       # ∈ [0.0, 1.0]
    assumptions: tuple[str, ...]            # pressupostos explícitos
    limitations: tuple[str, ...]            # limitações declaradas
    created_at: datetime
    analyst: str                            # "system" ou user_id (Sprint 4.5)
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.explanation_id:
            raise ValueError("InferenceExplanation.explanation_id obrigatório")
        if not self.claim:
            raise ValueError("InferenceExplanation.claim obrigatório")
        if not self.method:
            raise ValueError("InferenceExplanation.method obrigatório")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"InferenceExplanation.confidence deve estar em [0.0, 1.0], "
                f"recebido {self.confidence}"
            )
        if self.created_at.tzinfo is None:
            raise ValueError(
                "InferenceExplanation.created_at deve ser timezone-aware (UTC)"
            )
        # Sprint 4.4.5 — Hardening: inferências analíticas MUST carry
        # participating_genes para garantir proveniência completa.
        # COHORT e RESEARCH podem operar sobre grupos sem genes específicos.
        if self.inference_type in (
            InferenceType.CORRELATION,
            InferenceType.HYPOTHESIS,
            InferenceType.GRAPH_EDGE,
        ):
            if not self.participating_genes:
                raise ValueError(
                    f"InferenceExplanation ({self.inference_type.value}) MUST "
                    f"include participating_genes — proveniência incompleta."
                )

    # REDACTED
    # Rastreabilidade canônica — 5 elementos mínimos obrigatórios
    # REDACTED

    def has_full_provenance(self) -> bool:
        """True se a inferência declarou pelo menos os 5 elementos
        de rastreabilidade: genes, expressions, events, claim, method.

        É esta a invariante que impede inferências "caixa preta".
        """
        return (
            bool(self.participating_genes)
            or bool(self.participating_expressions)
            or bool(self.participating_events)
        ) and bool(self.claim) and bool(self.method)

    def participating_genes_count(self) -> int:
        return len(self.participating_genes)

    def participating_expressions_count(self) -> int:
        return len(self.participating_expressions)

    def participating_events_count(self) -> int:
        return len(self.participating_events)


# ============================================================================
# Builder fluente — usado pelos engines para construir explicações
# ============================================================================


@dataclass
class _ExplanationBuilderState:
    """Estado mutável interno do builder."""

    inference_type: InferenceType
    claim: str
    method: str
    confidence: float
    participating_genes: list[str] = field(default_factory=list)
    participating_expressions: list[str] = field(default_factory=list)
    participating_events: list[str] = field(default_factory=list)
    participating_correlations: list[str] = field(default_factory=list)
    participating_hypotheses: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    analyst: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)


class ExplainabilityPipeline:
    """Fábrica + pipeline de InferenceExplanation.

    Encapsula a invariante cross-cutting: toda inferência é construída
    via este pipeline, que garante:
      - ID único
      - timestamp UTC
      - confidence normalizada
      - listas deduplicadas e ordenadas
      - participation de pelo menos uma fonte (gene/expr/event)
    """

    @staticmethod
    def begin(
        inference_type: InferenceType,
        claim: str,
        method: str,
        confidence: float,
    ) -> "_ExplanationBuilder":
        """Inicia construção de uma InferenceExplanation.

        Retorna builder fluente que aceita os elementos de proveniência
        antes do ``.build()``.
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"confidence deve estar em [0.0, 1.0], recebido {confidence}"
            )
        return _ExplanationBuilder(
            state=_ExplanationBuilderState(
                inference_type=inference_type,
                claim=claim,
                method=method,
                confidence=confidence,
            )
        )

    @staticmethod
    def for_correlation(
        claim: str,
        method: str,
        confidence: float,
        gene_x_id: str,
        gene_y_id: str,
        event_ids: Sequence[str] | None = None,
    ) -> InferenceExplanation:
        """Shortcut para explicação de correlação (2 genes)."""
        builder = ExplainabilityPipeline.begin(
            InferenceType.CORRELATION, claim, method, confidence
        )
        builder.with_genes(gene_x_id, gene_y_id)
        if event_ids:
            builder.with_events(*event_ids)
        builder.with_assumption("Correlação não implica causalidade")
        builder.with_limitation("Associação observacional baseada em série temporal finita")
        return builder.build()

    @staticmethod
    def for_hypothesis(
        claim: str,
        rule_id: str,
        confidence: float,
        *,
        gene_ids: Sequence[str] = (),
        expression_refs: Sequence[str] = (),
        event_ids: Sequence[str] = (),
        correlation_ids: Sequence[str] = (),
    ) -> InferenceExplanation:
        """Shortcut para explicação de hipótese."""
        builder = ExplainabilityPipeline.begin(
            InferenceType.HYPOTHESIS, claim, rule_id, confidence
        )
        if gene_ids:
            builder.with_genes(*gene_ids)
        if expression_refs:
            builder.with_expressions(*expression_refs)
        if event_ids:
            builder.with_events(*event_ids)
        if correlation_ids:
            builder.with_correlations(*correlation_ids)
        builder.with_assumption("Hipótese é conhecimento derivado, não verdade clínica")
        builder.with_limitation(
            "Hipótese requer validação por evidência externa antes de uso clínico"
        )
        return builder.build()

    @staticmethod
    def for_research(
        claim: str,
        query_type: str,
        confidence: float,
        *,
        correlation_ids: Sequence[str] = (),
        hypothesis_ids: Sequence[str] = (),
    ) -> InferenceExplanation:
        """Shortcut para explicação de Research Session."""
        builder = ExplainabilityPipeline.begin(
            InferenceType.RESEARCH, claim, query_type, confidence
        )
        if correlation_ids:
            builder.with_correlations(*correlation_ids)
        if hypothesis_ids:
            builder.with_hypotheses(*hypothesis_ids)
        builder.with_assumption("Resultado de pesquisa é reprodutível via replay")
        builder.with_limitation(
            "Resultado reflete o estado do Knowledge Engine no momento da execução"
        )
        return builder.build()


class _ExplanationBuilder:
    """Builder fluente privado — use ExplainabilityPipeline.begin()."""

    def __init__(self, state: _ExplanationBuilderState) -> None:
        self._state = state

    def with_genes(self, *gene_ids: str | Sequence[str]) -> "_ExplanationBuilder":
        flat: list[str] = []
        for g in gene_ids:
            if isinstance(g, (list, tuple)):
                flat.extend(str(x) for x in g)
            else:
                flat.append(str(g))
        for g in flat:
            if g and g not in self._state.participating_genes:
                self._state.participating_genes.append(g)
        return self

    def with_expressions(self, *expression_refs: str | Sequence[str]) -> "_ExplanationBuilder":
        flat: list[str] = []
        for e in expression_refs:
            if isinstance(e, (list, tuple)):
                flat.extend(str(x) for x in e)
            else:
                flat.append(str(e))
        for e in flat:
            if e and e not in self._state.participating_expressions:
                self._state.participating_expressions.append(e)
        return self

    def with_events(self, *event_ids: str | Sequence[str]) -> "_ExplanationBuilder":
        flat: list[str] = []
        for e in event_ids:
            if isinstance(e, (list, tuple)):
                flat.extend(str(x) for x in e)
            else:
                flat.append(str(e))
        for e in flat:
            if e and e not in self._state.participating_events:
                self._state.participating_events.append(e)
        return self

    def with_correlations(self, *correlation_ids: str | Sequence[str]) -> "_ExplanationBuilder":
        flat: list[str] = []
        for c in correlation_ids:
            if isinstance(c, (list, tuple)):
                flat.extend(str(x) for x in c)
            else:
                flat.append(str(c))
        for c in flat:
            if c and c not in self._state.participating_correlations:
                self._state.participating_correlations.append(c)
        return self

    def with_hypotheses(self, *hypothesis_ids: str | Sequence[str]) -> "_ExplanationBuilder":
        flat: list[str] = []
        for h in hypothesis_ids:
            if isinstance(h, (list, tuple)):
                flat.extend(str(x) for x in h)
            else:
                flat.append(str(h))
        for h in flat:
            if h and h not in self._state.participating_hypotheses:
                self._state.participating_hypotheses.append(h)
        return self

    def with_assumption(self, assumption: str) -> "_ExplanationBuilder":
        if assumption and assumption not in self._state.assumptions:
            self._state.assumptions.append(assumption)
        return self

    def with_limitation(self, limitation: str) -> "_ExplanationBuilder":
        if limitation and limitation not in self._state.limitations:
            self._state.limitations.append(limitation)
        return self

    def with_metadata(self, key: str, value: Any) -> "_ExplanationBuilder":
        self._state.metadata[key] = value
        return self

    def with_analyst(self, analyst: str) -> "_ExplanationBuilder":
        self._state.analyst = analyst
        return self

    def build(self) -> InferenceExplanation:
        """Constrói a InferenceExplanation final.

        Aplica invariantes:
          - listas ordenadas e deduplicadas
          - ID gerado (uuid4 prefixado)
          - timestamp UTC
          - confidence normalizada
        """
        s = self._state
        return InferenceExplanation(
            explanation_id=_new_id("expl"),
            inference_type=s.inference_type,
            claim=s.claim,
            method=s.method,
            participating_genes=tuple(sorted(set(s.participating_genes))),
            participating_expressions=tuple(sorted(set(s.participating_expressions))),
            participating_events=tuple(sorted(set(s.participating_events))),
            participating_correlations=tuple(sorted(set(s.participating_correlations))),
            participating_hypotheses=tuple(sorted(set(s.participating_hypotheses))),
            confidence=float(s.confidence),
            assumptions=tuple(s.assumptions),
            limitations=tuple(s.limitations),
            created_at=_utcnow(),
            analyst=s.analyst,
            metadata=MappingProxyType(dict(s.metadata)),
        )


# implements:
#   AS-001-REQ-0009 — Replay bit-identical (explainability é parte da proveniência)
#   AS-002 §4.3.1 — Explanation reference cross-cutting
#   ADR-0006 §3 — Pure Domain: zero dependências externas