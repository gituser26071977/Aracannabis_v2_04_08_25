"""
Correlation Engine — Sprint 4.4 Clinical Knowledge Engine v1.0.

PRINCÍPIOS:
    - Correlation nunca representa causalidade (apenas associação).
    - Correlation é observacional: força estatística sobre evidência.
    - Toda correlation emite InferenceExplanation (cross-cutting).

MÉTODOS CANÔNICOS:
    - POSITIVE: Pearson simplificado sobre séries de confidence.
    - NEGATIVE: correlação negativa (coef < 0).
    - CO_OCCURRENCE: eventos simultâneos (±1 dia).
    - MUTUAL_EXCLUSION: inverso de co-ocorrência.
    - TEMPORAL_PRECEDENCE: gene_x.Expression precede gene_y.Expression.
    - STATISTICAL_DEPENDENCY: chi-quadrado simplificado (categórico).

ALGORITMOS:
    Pure Python — sem numpy/scipy. Cada método é uma função pura
    que recebe o ClinicalGenome e devolve tuple[CorrelationResult].

PURE DOMAIN:
    Zero dependências externas além de stdlib + tipos validados.
"""

from __future__ import annotations

import hashlib
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...timeline.domain.window import TimeWindow
from .clinical_genome import ClinicalGenome
from .explainability import ExplainabilityPipeline, InferenceExplanation, InferenceType


class CorrelationMethod(str, Enum):
    """Métodos canônicos de correlação do Knowledge Engine."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    CO_OCCURRENCE = "co_occurrence"
    MUTUAL_EXCLUSION = "mutual_exclusion"
    TEMPORAL_PRECEDENCE = "temporal_precedence"
    STATISTICAL_DEPENDENCY = "statistical_dependency"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _deterministic_correlation_id(
    method: str,
    gene_x: str,
    gene_y: str,
    window_start: str,
    window_end: str,
    tenant_id: str,
) -> str:
    """ID determinístico: mesmo gene pair + mesma window + mesmo tenant = mesmo ID.

    Garante replay bit-identical sem precisar de UUID.

    Sprint 4.4.5 — tenant_id incluído para evitar cross-tenant collision:
    sem tenant_id no hash, genes de tenants diferentes com mesmo gene_id
    produziriam correlation_id idêntico (vazamento).
    """
    raw = f"{tenant_id}|{method}|{gene_x}|{gene_y}|{window_start}|{window_end}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
    return f"corr_{method}_{digest}"


@dataclass(frozen=True)
class CorrelationResult:
    """Resultado de uma análise de correlação entre 2 Genes.

    Convenção de sinal:
        - coefficient ∈ [-1.0, 1.0]
        - POSITIVE: coefficient > 0 e significativo
        - NEGATIVE: coefficient < 0 e significativo
        - CO_OCCURRENCE: coefficient ∈ [0.0, 1.0] (fração de co-ocorrência)
        - MUTUAL_EXCLUSION: coefficient ∈ [0.0, 1.0] (fração de exclusão)
        - TEMPORAL_PRECEDENCE: coefficient ∈ [0.0, 1.0] (lag fraction)
        - STATISTICAL_DEPENDENCY: coefficient ∈ [0.0, 1.0] (chi² normalizado)
    """

    correlation_id: str
    method: CorrelationMethod
    gene_x_id: str
    gene_y_id: str
    coefficient: float
    p_value: float | None
    n_observations: int
    confidence: float                       # ∈ [0.0, 1.0]
    window: TimeWindow
    supporting_event_ids: tuple[str, ...]
    computed_at: datetime
    explanation: InferenceExplanation

    def __post_init__(self) -> None:
        if not self.correlation_id:
            raise ValueError("CorrelationResult.correlation_id obrigatório")
        if not (-1.0 <= self.coefficient <= 1.0):
            raise ValueError(
                f"CorrelationResult.coefficient deve estar em [-1.0, 1.0], "
                f"recebido {self.coefficient}"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"CorrelationResult.confidence deve estar em [0.0, 1.0], "
                f"recebido {self.confidence}"
            )
        if self.n_observations < 0:
            raise ValueError(
                f"CorrelationResult.n_observations não pode ser negativo: {self.n_observations}"
            )
        if self.computed_at.tzinfo is None:
            raise ValueError(
                "CorrelationResult.computed_at deve ser timezone-aware (UTC)"
            )


# ============================================================================
# CorrelationEngine — pure function, deterministic
# ============================================================================


class CorrelationEngine:
    """Engine de correlação entre Genes do mesmo paciente.

    Uso:
        engine = CorrelationEngine()
        results = engine.compute(genome, method=CorrelationMethod.POSITIVE)

    Invariantes:
        - Determinístico: mesmos inputs → mesmos outputs (mesmo coefficient).
        - Pure: sem side-effects; sem mutação do genome.
        - Cross-cutting: cada resultado traz InferenceExplanation.
    """

    # REDACTED
    # API pública
    # REDACTED

    def compute(
        self,
        genome: ClinicalGenome,
        *,
        method: CorrelationMethod,
        min_observations: int = 2,
    ) -> tuple[CorrelationResult, ...]:
        """Calcula correlações entre todos os pares de Genes do genome.

        Args:
            genome: ClinicalGenome (read-model).
            method: CorrelationMethod a aplicar.
            min_observations: número mínimo de pontos para considerar válido.

        Returns:
            tuple[CorrelationResult] — uma por par (gene_x, gene_y) com
            coefficient significativo. Pode ser vazio se nenhum par tiver
            dados suficientes.
        """
        genes = list(genome.genes)
        if len(genes) < 2:
            return ()

        results: list[CorrelationResult] = []
        for i, gene_x in enumerate(genes):
            for gene_y in genes[i + 1 :]:
                result = self._compute_pair(
                    gene_x=gene_x,
                    gene_y=gene_y,
                    method=method,
                    window=genome.window,
                    min_observations=min_observations,
                )
                if result is not None:
                    results.append(result)
        return tuple(results)

    # REDACTED
    # Implementação por método
    # REDACTED

    def _compute_pair(
        self,
        *,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        method: CorrelationMethod,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        if method == CorrelationMethod.POSITIVE:
            return self._pearson_positive(
                gene_x, gene_y, window, min_observations
            )
        if method == CorrelationMethod.NEGATIVE:
            return self._pearson_negative(
                gene_x, gene_y, window, min_observations
            )
        if method == CorrelationMethod.CO_OCCURRENCE:
            return self._co_occurrence(gene_x, gene_y, window, min_observations)
        if method == CorrelationMethod.MUTUAL_EXCLUSION:
            return self._mutual_exclusion(
                gene_x, gene_y, window, min_observations
            )
        if method == CorrelationMethod.TEMPORAL_PRECEDENCE:
            return self._temporal_precedence(
                gene_x, gene_y, window, min_observations
            )
        if method == CorrelationMethod.STATISTICAL_DEPENDENCY:
            return self._statistical_dependency(
                gene_x, gene_y, window, min_observations
            )
        return None

    # REDACTED
    # POSITIVE / NEGATIVE — Pearson simplificado
    # REDACTED

    def _pearson_positive(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        series_x, _ = _confidence_series(gene_x, window)
        series_y, _ = _confidence_series(gene_y, window)
        coef, n = _pearson(series_x, series_y)
        if n < min_observations or coef <= 0:
            return None
        return _make_result(
            method=CorrelationMethod.POSITIVE,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coef,
            n_observations=n,
            window=window,
            event_ids=_event_ids_pair(gene_x, gene_y),
            method_label="pearson_positive",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"Confiança de {gene_x.gene_id} sobe quando confiança de "
                f"{gene_y.gene_id} sobe (r={coef:.2f}, n={n})"
            ),
        )

    def _pearson_negative(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        series_x, _ = _confidence_series(gene_x, window)
        series_y, _ = _confidence_series(gene_y, window)
        coef, n = _pearson(series_x, series_y)
        if n < min_observations or coef >= 0:
            return None
        return _make_result(
            method=CorrelationMethod.NEGATIVE,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coef,
            n_observations=n,
            window=window,
            event_ids=_event_ids_pair(gene_x, gene_y),
            method_label="pearson_negative",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"Confiança de {gene_x.gene_id} sobe quando confiança de "
                f"{gene_y.gene_id} desce (r={coef:.2f}, n={n})"
            ),
        )

    # REDACTED
    # CO_OCCURRENCE / MUTUAL_EXCLUSION — eventos simultâneos
    # REDACTED

    def _co_occurrence(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        events_x, ev_ids_x = _expression_event_times(gene_x, window)
        events_y, ev_ids_y = _expression_event_times(gene_y, window)
        if not events_x or not events_y:
            return None
        tolerance = timedelta(days=1)
        simultaneous = 0
        supporting: list[str] = []
        for ex, ev_x in zip(events_x, ev_ids_x):
            for ey, ev_y in zip(events_y, ev_ids_y):
                if abs((ex - ey).total_seconds()) <= tolerance.total_seconds():
                    simultaneous += 1
                    supporting.extend([ev_x, ev_y])
        total_x = len(events_x)
        total_y = len(events_y)
        union = total_x + total_y - simultaneous
        if union == 0 or simultaneous < min_observations:
            return None
        coefficient = simultaneous / union
        return _make_result(
            method=CorrelationMethod.CO_OCCURRENCE,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coefficient,
            n_observations=simultaneous,
            window=window,
            event_ids=tuple(supporting),
            method_label="co_occurrence",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"{gene_x.gene_id} e {gene_y.gene_id} co-ocorrem em "
                f"{simultaneous}/{union} eventos (±1 dia)"
            ),
        )

    def _mutual_exclusion(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        events_x, ev_ids_x = _expression_event_times(gene_x, window)
        events_y, ev_ids_y = _expression_event_times(gene_y, window)
        if not events_x or not events_y:
            return None
        tolerance = timedelta(days=1)
        simultaneous = 0
        supporting: list[str] = []
        for ex, ev_x in zip(events_x, ev_ids_x):
            for ey, ev_y in zip(events_y, ev_ids_y):
                if abs((ex - ey).total_seconds()) <= tolerance.total_seconds():
                    simultaneous += 1
                    supporting.extend([ev_x, ev_y])
        total_x = len(events_x)
        total_y = len(events_y)
        union = total_x + total_y - simultaneous
        if union == 0:
            return None
        non_simultaneous = total_x + total_y - 2 * simultaneous
        coefficient = non_simultaneous / union if union else 0.0
        if simultaneous == 0 and (total_x + total_y) < min_observations:
            return None
        return _make_result(
            method=CorrelationMethod.MUTUAL_EXCLUSION,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coefficient,
            n_observations=total_x + total_y,
            window=window,
            event_ids=tuple(supporting),
            method_label="mutual_exclusion",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"{gene_x.gene_id} e {gene_y.gene_id} mutuamente exclusivos "
                f"({non_simultaneous}/{union} eventos não simultâneos)"
            ),
        )

    # REDACTED
    # TEMPORAL_PRECEDENCE — gene_x.Expression precede gene_y.Expression
    # REDACTED

    def _temporal_precedence(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        events_x, ev_ids_x = _expression_event_times(gene_x, window)
        events_y, ev_ids_y = _expression_event_times(gene_y, window)
        if not events_x or not events_y:
            return None
        # Conta pares onde event_x precede event_y.
        precedence_count = 0
        supporting: list[str] = []
        for ex, ev_x in zip(events_x, ev_ids_x):
            for ey, ev_y in zip(events_y, ev_ids_y):
                if ex < ey:
                    precedence_count += 1
                    supporting.extend([ev_x, ev_y])
        total_pairs = len(events_x) * len(events_y)
        if total_pairs == 0 or precedence_count < min_observations:
            return None
        coefficient = precedence_count / total_pairs
        return _make_result(
            method=CorrelationMethod.TEMPORAL_PRECEDENCE,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coefficient,
            n_observations=precedence_count,
            window=window,
            event_ids=tuple(supporting),
            method_label="temporal_precedence",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"{gene_x.gene_id} precede {gene_y.gene_id} em "
                f"{precedence_count}/{total_pairs} pares"
            ),
        )

    # REDACTED
    # STATISTICAL_DEPENDENCY — chi-quadrado simplificado (discreto)
    # REDACTED

    def _statistical_dependency(
        self,
        gene_x: ClinicalGene,
        gene_y: ClinicalGene,
        window: TimeWindow,
        min_observations: int,
    ) -> CorrelationResult | None:
        # Discretiza estado de cada Expression em "high" / "low".
        states_x = _discretized_states(gene_x, window)
        states_y = _discretized_states(gene_y, window)
        if len(states_x) < min_observations or len(states_y) < min_observations:
            return None
        # Cross-tab simplificada (assumindo séries pareadas por ordem temporal).
        n = min(len(states_x), len(states_y))
        if n == 0:
            return None
        # Observações conjuntas.
        a = sum(1 for i in range(n) if states_x[i] == "high" and states_y[i] == "high")
        b = sum(1 for i in range(n) if states_x[i] == "high" and states_y[i] == "low")
        c = sum(1 for i in range(n) if states_x[i] == "low" and states_y[i] == "high")
        d = sum(1 for i in range(n) if states_x[i] == "low" and states_y[i] == "low")
        total = a + b + c + d
        if total == 0:
            return None
        expected_a = (a + b) * (a + c) / total
        expected_b = (a + b) * (b + d) / total
        expected_c = (c + d) * (a + c) / total
        expected_d = (c + d) * (b + d) / total
        chi2 = 0.0
        for obs, exp in ((a, expected_a), (b, expected_b), (c, expected_c), (d, expected_d)):
            if exp > 0:
                chi2 += (obs - exp) ** 2 / exp
        # Normaliza para [0, 1]: chi²_max ≈ n para tabela 2x2.
        coefficient = min(1.0, chi2 / max(n, 1))
        if coefficient < 0.1:
            return None
        return _make_result(
            method=CorrelationMethod.STATISTICAL_DEPENDENCY,
            gene_x_id=gene_x.gene_id,
            gene_y_id=gene_y.gene_id,
            coefficient=coefficient,
            n_observations=total,
            window=window,
            event_ids=_event_ids_pair(gene_x, gene_y),
            method_label="chi_squared_simplified",
            tenant_id=gene_x.tenant_id,
            claim=(
                f"{gene_x.gene_id} e {gene_y.gene_id} têm dependência estatística "
                f"(chi²_norm={coefficient:.2f}, n={total})"
            ),
        )


# ============================================================================
# Helpers — pure functions
# ============================================================================


def _confidence_series(
    gene: ClinicalGene, window: TimeWindow
) -> tuple[list[float], list[str]]:
    """Extrai série temporal de confidence dentro da window."""
    series: list[float] = []
    event_ids: list[str] = []
    for point in gene.trajectory:
        vt = point.expression.valid_time
        if window.contains(vt):
            series.append(point.expression.confidence.value)
            event_ids.extend(point.contributing_event_ids)
    return series, event_ids


def _expression_event_times(
    gene: ClinicalGene, window: TimeWindow
) -> tuple[list[datetime], list[str]]:
    """Extrai (valid_time, event_id) por Expression dentro da window."""
    times: list[datetime] = []
    event_ids: list[str] = []
    for point in gene.trajectory:
        vt = point.expression.valid_time
        if window.contains(vt):
            times.append(vt)
            event_ids.extend(point.contributing_event_ids)
    return times, event_ids


def _discretized_states(
    gene: ClinicalGene, window: TimeWindow
) -> list[str]:
    """Discretiza Expression.confidence em 'high' (>=0.5) ou 'low' (<0.5)."""
    states: list[str] = []
    for point in gene.trajectory:
        vt = point.expression.valid_time
        if window.contains(vt):
            states.append("high" if point.expression.confidence.value >= 0.5 else "low")
    return states


def _event_ids_pair(
    gene_x: ClinicalGene, gene_y: ClinicalGene
) -> tuple[str, ...]:
    """Coleta event_ids de ambos os Genes."""
    ids: set[str] = set()
    for gene in (gene_x, gene_y):
        for entry in gene.history:
            ids.add(entry.event_id)
    return tuple(sorted(ids))


def _pearson(
    xs: Sequence[float], ys: Sequence[float]
) -> tuple[float, int]:
    """Pearson simplificado (sem numpy).

    Retorna (coefficient, n_observations_aligned).
    """
    n = min(len(xs), len(ys))
    if n < 2:
        return 0.0, n
    mean_x = sum(xs[:n]) / n
    mean_y = sum(ys[:n]) / n
    cov = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
    var_x = sum((xs[i] - mean_x) ** 2 for i in range(n))
    var_y = sum((ys[i] - mean_y) ** 2 for i in range(n))
    if var_x == 0 or var_y == 0:
        return 0.0, n
    coef = cov / math.sqrt(var_x * var_y)
    # Clamp por segurança numérica.
    coef = max(-1.0, min(1.0, coef))
    return coef, n


def _make_result(
    *,
    method: CorrelationMethod,
    gene_x_id: str,
    gene_y_id: str,
    coefficient: float,
    n_observations: int,
    window: TimeWindow,
    event_ids: tuple[str, ...],
    method_label: str,
    claim: str,
    tenant_id: str,
) -> CorrelationResult:
    """Constrói CorrelationResult + InferenceExplanation de forma coerente."""
    # Confidence = coefficient absoluto × fator de observações (logarítmico).
    obs_factor = min(1.0, math.log1p(n_observations) / math.log1p(10))
    confidence = min(1.0, abs(coefficient) * obs_factor)
    explanation = ExplainabilityPipeline.for_correlation(
        claim=claim,
        method=method_label,
        confidence=confidence,
        gene_x_id=gene_x_id,
        gene_y_id=gene_y_id,
        event_ids=event_ids,
    )
    return CorrelationResult(
        correlation_id=_deterministic_correlation_id(
            method.value,
            gene_x_id,
            gene_y_id,
            window.start.isoformat(),
            window.end.isoformat(),
            tenant_id,
        ),
        method=method,
        gene_x_id=gene_x_id,
        gene_y_id=gene_y_id,
        coefficient=coefficient,
        p_value=None,            # Pure Python — sem scipy
        n_observations=n_observations,
        confidence=confidence,
        window=window,
        supporting_event_ids=event_ids,
        computed_at=_utcnow(),
        explanation=explanation,
    )


# implements:
#   AS-001 §7.5 — Explainability cross-cutting
#   AS-002 §4.3.1 — Explanation reference
#   ADR-0006 §3 — Pure Domain (zero numpy/scipy)
#   Sprint 4.4 — "Correlation nunca representa causalidade"