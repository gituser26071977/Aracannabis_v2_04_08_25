"""
DTOs — Data Transfer Objects do Application Layer.

Sprint 4.4 — Clinical Knowledge Engine v1.0.

DTOs são imutáveis (frozen dataclasses) e usados para transportar
resultados entre Application Services e callers (testes, demo).
Não contêm lógica — apenas estrutura de dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from ...timeline.domain.window import TimeWindow
from ..domain.clinical_genome import ClinicalGenome
from ..domain.cohort import Cohort, Criterion
from ..domain.correlation import CorrelationMethod, CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis
from ..domain.knowledge_graph import KnowledgeGraph
from ..domain.research import AnalysisType, ResearchQuery, ResearchSession


# ============================================================================
# Request DTOs (input)
# ============================================================================


@dataclass(frozen=True)
class CorrelationRequest:
    """Request para CorrelationService."""

    genome: ClinicalGenome
    method: CorrelationMethod = CorrelationMethod.POSITIVE
    min_observations: int = 2


@dataclass(frozen=True)
class HypothesisRequest:
    """Request para HypothesisService."""

    genome: ClinicalGenome
    correlations: tuple[CorrelationResult, ...] = ()


@dataclass(frozen=True)
class CohortRequest:
    """Request para CohortService."""

    patients: tuple[Any, ...]
    tenant_id: str
    name: str
    criteria: tuple[Criterion, ...] = ()


@dataclass(frozen=True)
class ResearchRequest:
    """Request para ResearchService."""

    cohort_id: str
    analysis_type: AnalysisType
    params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    version: int = 1


@dataclass(frozen=True)
class GraphRequest:
    """Request para GraphService."""

    genome: ClinicalGenome
    correlations: tuple[CorrelationResult, ...] = ()
    hypotheses: tuple[ClinicalHypothesis, ...] = ()


# ============================================================================
# Result DTOs (output)
# ============================================================================


@dataclass(frozen=True)
class KnowledgePipelineResult:
    """Resultado agregado do pipeline completo do Knowledge Engine."""

    genome: ClinicalGenome
    correlations: tuple[CorrelationResult, ...]
    hypotheses: tuple[ClinicalHypothesis, ...]
    graph: KnowledgeGraph | None
    started_at: datetime
    completed_at: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def correlation_count(self) -> int:
        return len(self.correlations)

    @property
    def hypothesis_count(self) -> int:
        return len(self.hypotheses)

    @property
    def graph_node_count(self) -> int:
        return len(self.graph.nodes) if self.graph else 0

    @property
    def graph_edge_count(self) -> int:
        return len(self.graph.edges) if self.graph else 0