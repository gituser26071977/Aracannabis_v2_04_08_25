"""
Hypothesis Engine — Sprint 4.4 Clinical Knowledge Engine v1.0.

PRINCÍPIOS:
    - Hypothesis não representa verdade clínica.
    - Hypothesis representa hipótese inferida, evidência calculada,
      conhecimento derivado.
    - Toda Hypothesis contém:
        * confidence score
        * supporting genes
        * contradicting genes
        * supporting expressions
        * contradicting expressions
        * evidence (event_ids)
        * correlations_used
        * explicação completa (InferenceExplanation)
        * status (PROPOSED / SUPPORTED / CONTRADICTED / INCONCLUSIVE / RETRACTED)

REGRAS DE GERAÇÃO (6 canônicas):
    1. H_CORR_POSITIVE — Gene X high-confidence + correlação positiva com Y
       → "Gene X pode influenciar Gene Y" (status: SUPPORTED)
    2. H_CORR_NEGATIVE — Gene X low-confidence + correlação negativa com Y
       → "Gene X antagoniza Gene Y" (status: PROPOSED)
    3. H_VOLATILITY_COOCCUR — Gene X high-volatility + co-ocorrência com Y
       → "Gene X e Y co-ocorrem sob instabilidade" (status: SUPPORTED)
    4. H_NO_EXPRESSION — Gene sem Expression
       → "Gene X nunca observado" (status: INCONCLUSIVE)
    5. H_MUTUAL_EXCLUSION — Mutual exclusion detectada
       → "Gene X e Y mutuamente exclusivos" (status: CONTRADICTED)
    6. H_TEMPORAL_PRECEDENCE — Gene X precede Gene Y
       → "Gene X precede Gene Y" (status: SUPPORTED)

PURE DOMAIN: zero dependências externas.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...genome.domain.expression import ExpressionState
from ...timeline.domain.window import TimeWindow
from .clinical_genome import ClinicalGenome
from .correlation import CorrelationMethod, CorrelationResult
from .explainability import ExplainabilityPipeline, InferenceExplanation, InferenceType


class HypothesisStatus(str, Enum):
    """Estados canônicos de uma Hipótese Clínica."""

    PROPOSED = "proposed"               # inferida, ainda sem evidência
    SUPPORTED = "supported"             # sustentada por correlações/evidência
    CONTRADICTED = "contradicted"       # refutada por evidência
    INCONCLUSIVE = "inconclusive"       # dados insuficientes
    RETRACTED = "retracted"             # removida por decisão humana


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _deterministic_hypothesis_id(
    rule_id: str,
    gene_ids: tuple[str, ...],
    correlation_ids: tuple[str, ...],
    claim: str,
) -> str:
    """ID determinístico: mesmo rule + genes + correlations + claim = mesmo ID."""
    raw = f"{rule_id}|{','.join(sorted(gene_ids))}|{','.join(sorted(correlation_ids))}|{claim}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"hyp_{digest}"


@dataclass(frozen=True)
class ClinicalHypothesis:
    """Hipótese clínica inferida — conhecimento derivado, não verdade.

    Cada hipótese documenta:
        - claim (afirmação textual)
        - confidence (∈ [0, 1])
        - status
        - supporting_genes / contradicting_genes
        - supporting_expressions / contradicting_expressions
        - evidence (event_ids)
        - correlations_used (correlation_ids)
        - explanation (InferenceExplanation completa)
    """

    hypothesis_id: str
    claim: str
    confidence: float
    supporting_genes: tuple[str, ...]
    supporting_expressions: tuple[str, ...]
    contradicting_genes: tuple[str, ...]
    contradicting_expressions: tuple[str, ...]
    evidence: tuple[str, ...]                    # event_ids
    correlations_used: tuple[str, ...]           # correlation_ids
    status: HypothesisStatus
    rule_id: str                                # qual regra produziu (H_xxx)
    created_at: datetime
    explanation: InferenceExplanation

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("ClinicalHypothesis.hypothesis_id obrigatório")
        if not self.claim:
            raise ValueError("ClinicalHypothesis.claim obrigatório")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"ClinicalHypothesis.confidence deve estar em [0.0, 1.0], "
                f"recebido {self.confidence}"
            )
        if not self.rule_id:
            raise ValueError("ClinicalHypothesis.rule_id obrigatório")
        if self.created_at.tzinfo is None:
            raise ValueError(
                "ClinicalHypothesis.created_at deve ser timezone-aware (UTC)"
            )

    # REDACTED
    # Rastreabilidade
    # REDACTED

    def has_provenance(self) -> bool:
        """Verifica proveniência mínima (genes ou expressões ou evidência)."""
        return bool(
            self.supporting_genes
            or self.contradicting_genes
            or self.evidence
            or self.correlations_used
        )

    def total_participating_sources(self) -> int:
        return (
            len(self.supporting_genes)
            + len(self.contradicting_genes)
            + len(self.evidence)
            + len(self.correlations_used)
        )


# ============================================================================
# HypothesisEngine — pure function, deterministic
# ============================================================================


class HypothesisEngine:
    """Engine de geração de hipóteses a partir de Genes + Correlações.

    Uso:
        engine = HypothesisEngine()
        hypotheses = engine.generate(genome, correlations)

    Regras:
        - Aplica as 6 regras canônicas declaradas acima.
        - Sem ML — apenas heurísticas baseadas em estado + correlações.
        - Cada hipótese carrega InferenceExplanation.
    """

    def generate(
        self,
        genome: ClinicalGenome,
        correlations: Sequence[CorrelationResult] = (),
    ) -> tuple[ClinicalHypothesis, ...]:
        """Gera hypotheses a partir do genome e das correlações disponíveis.

        Args:
            genome: ClinicalGenome (read-model).
            correlations: tuple[CorrelationResult] produzido por CorrelationEngine.

        Returns:
            tuple[ClinicalHypothesis] — pode ser vazio se nenhuma regra
            disparar.
        """
        results: list[ClinicalHypothesis] = []
        genes = list(genome.genes)

        # Regra 4: Gene sem Expression (sempre roda, mesmo sem correlações).
        for gene in genes:
            hyp = self._rule_no_expression(gene)
            if hyp is not None:
                results.append(hyp)

        # Regras 1, 2, 3, 5, 6: dependem de correlações.
        for corr in correlations:
            if corr.method == CorrelationMethod.POSITIVE:
                hyp = self._rule_corr_positive(genome, corr)
                if hyp:
                    results.append(hyp)
            elif corr.method == CorrelationMethod.NEGATIVE:
                hyp = self._rule_corr_negative(genome, corr)
                if hyp:
                    results.append(hyp)
            elif corr.method == CorrelationMethod.CO_OCCURRENCE:
                hyp = self._rule_volatility_cooccur(genome, corr)
                if hyp:
                    results.append(hyp)
            elif corr.method == CorrelationMethod.MUTUAL_EXCLUSION:
                hyp = self._rule_mutual_exclusion(genome, corr)
                if hyp:
                    results.append(hyp)
            elif corr.method == CorrelationMethod.TEMPORAL_PRECEDENCE:
                hyp = self._rule_temporal_precedence(genome, corr)
                if hyp:
                    results.append(hyp)

        return tuple(results)

    # REDACTED
    # Regras
    # REDACTED

    def _rule_no_expression(
        self, gene: ClinicalGene
    ) -> ClinicalHypothesis | None:
        """Regra 4: Gene sem Expression observada."""
        if gene.current_expression is not None:
            return None
        return _make_hypothesis(
            rule_id="H_NO_EXPRESSION",
            claim=f"Gene {gene.gene_id} nunca foi observado neste paciente",
            confidence=0.0,
            status=HypothesisStatus.INCONCLUSIVE,
            supporting_genes=(),
            contradicting_genes=(gene.gene_id,),
            supporting_expressions=(),
            contradicting_expressions=(),
            evidence=tuple(e.event_id for e in gene.history),
            correlations_used=(),
            gene_ids=(gene.gene_id,),
            expression_refs=(),
            event_ids=tuple(e.event_id for e in gene.history),
            correlation_ids=(),
        )

    def _rule_corr_positive(
        self,
        genome: ClinicalGenome,
        corr: CorrelationResult,
    ) -> ClinicalHypothesis | None:
        """Regra 1: correlação positiva + Gene X high-confidence → influencia."""
        gene_x = genome.gene(corr.gene_x_id)
        gene_y = genome.gene(corr.gene_y_id)
        if gene_x is None or gene_y is None:
            return None
        # Gene X high-confidence (>= 0.7).
        if gene_x.current_expression is None:
            return None
        if gene_x.current_expression.confidence.value < 0.7:
            return None
        confidence = min(1.0, corr.confidence * 0.8)
        return _make_hypothesis(
            rule_id="H_CORR_POSITIVE",
            claim=(
                f"Gene {corr.gene_x_id} (alta confiança) pode influenciar "
                f"Gene {corr.gene_y_id} (correlação positiva r={corr.coefficient:.2f})"
            ),
            confidence=confidence,
            status=HypothesisStatus.SUPPORTED,
            supporting_genes=(corr.gene_x_id, corr.gene_y_id),
            contradicting_genes=(),
            supporting_expressions=(
                _expr_ref(gene_x), _expr_ref(gene_y),
            ),
            contradicting_expressions=(),
            evidence=corr.supporting_event_ids,
            correlations_used=(corr.correlation_id,),
            gene_ids=(corr.gene_x_id, corr.gene_y_id),
            expression_refs=(_expr_ref(gene_x), _expr_ref(gene_y)),
            event_ids=corr.supporting_event_ids,
            correlation_ids=(corr.correlation_id,),
        )

    def _rule_corr_negative(
        self,
        genome: ClinicalGenome,
        corr: CorrelationResult,
    ) -> ClinicalHypothesis | None:
        """Regra 2: correlação negativa + Gene X low-confidence → antagoniza."""
        gene_x = genome.gene(corr.gene_x_id)
        gene_y = genome.gene(corr.gene_y_id)
        if gene_x is None or gene_y is None:
            return None
        if gene_x.current_expression is None:
            return None
        if gene_x.current_expression.confidence.value >= 0.5:
            return None
        confidence = min(1.0, abs(corr.coefficient) * 0.6)
        return _make_hypothesis(
            rule_id="H_CORR_NEGATIVE",
            claim=(
                f"Gene {corr.gene_x_id} (baixa confiança) antagoniza "
                f"Gene {corr.gene_y_id} (correlação negativa r={corr.coefficient:.2f})"
            ),
            confidence=confidence,
            status=HypothesisStatus.PROPOSED,
            supporting_genes=(corr.gene_y_id,),
            contradicting_genes=(corr.gene_x_id,),
            supporting_expressions=(_expr_ref(gene_y),),
            contradicting_expressions=(_expr_ref(gene_x),),
            evidence=corr.supporting_event_ids,
            correlations_used=(corr.correlation_id,),
            gene_ids=(corr.gene_x_id, corr.gene_y_id),
            expression_refs=(_expr_ref(gene_x), _expr_ref(gene_y)),
            event_ids=corr.supporting_event_ids,
            correlation_ids=(corr.correlation_id,),
        )

    def _rule_volatility_cooccur(
        self,
        genome: ClinicalGenome,
        corr: CorrelationResult,
    ) -> ClinicalHypothesis | None:
        """Regra 3: co-ocorrência + Gene X alta volatilidade → instabilidade."""
        gene_x = genome.gene(corr.gene_x_id)
        gene_y = genome.gene(corr.gene_y_id)
        if gene_x is None or gene_y is None:
            return None
        if gene_x.current_expression is None:
            return None
        if gene_x.current_expression.volatility.value != "high":
            return None
        confidence = min(1.0, corr.confidence * 0.7)
        return _make_hypothesis(
            rule_id="H_VOLATILITY_COOCCUR",
            claim=(
                f"Gene {corr.gene_x_id} (alta volatilidade) e Gene "
                f"{corr.gene_y_id} co-ocorrem sob instabilidade clínica"
            ),
            confidence=confidence,
            status=HypothesisStatus.SUPPORTED,
            supporting_genes=(corr.gene_x_id, corr.gene_y_id),
            contradicting_genes=(),
            supporting_expressions=(_expr_ref(gene_x), _expr_ref(gene_y)),
            contradicting_expressions=(),
            evidence=corr.supporting_event_ids,
            correlations_used=(corr.correlation_id,),
            gene_ids=(corr.gene_x_id, corr.gene_y_id),
            expression_refs=(_expr_ref(gene_x), _expr_ref(gene_y)),
            event_ids=corr.supporting_event_ids,
            correlation_ids=(corr.correlation_id,),
        )

    def _rule_mutual_exclusion(
        self,
        genome: ClinicalGenome,
        corr: CorrelationResult,
    ) -> ClinicalHypothesis | None:
        """Regra 5: mutual exclusion detectada."""
        gene_x = genome.gene(corr.gene_x_id)
        gene_y = genome.gene(corr.gene_y_id)
        if gene_x is None or gene_y is None:
            return None
        return _make_hypothesis(
            rule_id="H_MUTUAL_EXCLUSION",
            claim=(
                f"Gene {corr.gene_x_id} e Gene {corr.gene_y_id} são "
                f"mutuamente exclusivos (coef={corr.coefficient:.2f})"
            ),
            confidence=corr.confidence,
            status=HypothesisStatus.CONTRADICTED,
            supporting_genes=(),
            contradicting_genes=(corr.gene_x_id, corr.gene_y_id),
            supporting_expressions=(),
            contradicting_expressions=(
                _safe_expr_ref(gene_x), _safe_expr_ref(gene_y),
            ),
            evidence=corr.supporting_event_ids,
            correlations_used=(corr.correlation_id,),
            gene_ids=(corr.gene_x_id, corr.gene_y_id),
            expression_refs=(
                _safe_expr_ref(gene_x), _safe_expr_ref(gene_y),
            ),
            event_ids=corr.supporting_event_ids,
            correlation_ids=(corr.correlation_id,),
        )

    def _rule_temporal_precedence(
        self,
        genome: ClinicalGenome,
        corr: CorrelationResult,
    ) -> ClinicalHypothesis | None:
        """Regra 6: temporal precedence detectada."""
        gene_x = genome.gene(corr.gene_x_id)
        gene_y = genome.gene(corr.gene_y_id)
        if gene_x is None or gene_y is None:
            return None
        if corr.coefficient < 0.6:
            return None
        return _make_hypothesis(
            rule_id="H_TEMPORAL_PRECEDENCE",
            claim=(
                f"Gene {corr.gene_x_id} precede Gene {corr.gene_y_id} "
                f"em {corr.coefficient:.0%} dos eventos"
            ),
            confidence=corr.confidence,
            status=HypothesisStatus.SUPPORTED,
            supporting_genes=(corr.gene_x_id, corr.gene_y_id),
            contradicting_genes=(),
            supporting_expressions=(
                _safe_expr_ref(gene_x), _safe_expr_ref(gene_y),
            ),
            contradicting_expressions=(),
            evidence=corr.supporting_event_ids,
            correlations_used=(corr.correlation_id,),
            gene_ids=(corr.gene_x_id, corr.gene_y_id),
            expression_refs=(
                _safe_expr_ref(gene_x), _safe_expr_ref(gene_y),
            ),
            event_ids=corr.supporting_event_ids,
            correlation_ids=(corr.correlation_id,),
        )


# ============================================================================
# Helpers
# ============================================================================


def _expr_ref(gene: ClinicalGene) -> str:
    """Gera referência canônica da Expression atual do Gene."""
    if gene.current_expression is None:
        return f"expr_no_expr_{gene.gene_id}"
    return f"expr_{gene.current_expression.sequence}:{gene.gene_id}"


def _safe_expr_ref(gene: ClinicalGene) -> str:
    """Versão tolerante a Gene sem Expression (retorna marker)."""
    return _expr_ref(gene)


def _make_hypothesis(
    *,
    rule_id: str,
    claim: str,
    confidence: float,
    status: HypothesisStatus,
    supporting_genes: tuple[str, ...],
    contradicting_genes: tuple[str, ...],
    supporting_expressions: tuple[str, ...],
    contradicting_expressions: tuple[str, ...],
    evidence: tuple[str, ...],
    correlations_used: tuple[str, ...],
    gene_ids: tuple[str, ...],
    expression_refs: tuple[str, ...],
    event_ids: tuple[str, ...],
    correlation_ids: tuple[str, ...],
) -> ClinicalHypothesis:
    """Constrói ClinicalHypothesis com InferenceExplanation coerente."""
    explanation = ExplainabilityPipeline.for_hypothesis(
        claim=claim,
        rule_id=rule_id,
        confidence=confidence,
        gene_ids=list(gene_ids),
        expression_refs=list(expression_refs),
        event_ids=list(event_ids),
        correlation_ids=list(correlation_ids),
    )
    return ClinicalHypothesis(
        hypothesis_id=_deterministic_hypothesis_id(
            rule_id=rule_id,
            gene_ids=gene_ids,
            correlation_ids=correlation_ids,
            claim=claim,
        ),
        claim=claim,
        confidence=confidence,
        supporting_genes=supporting_genes,
        supporting_expressions=supporting_expressions,
        contradicting_genes=contradicting_genes,
        contradicting_expressions=contradicting_expressions,
        evidence=evidence,
        correlations_used=correlations_used,
        status=status,
        rule_id=rule_id,
        created_at=_utcnow(),
        explanation=explanation,
    )


# implements:
#   AS-001 §6.6 — Hypotheses SHALL coexistir sem exclusividade
#   AS-002 §4.9.2 — Hypothesis SHALL NEVER substituir Expression
#   AS-001 §7.5 — Explainability cross-cutting
#   Sprint 4.4 — "Hypothesis não representa verdade clínica"