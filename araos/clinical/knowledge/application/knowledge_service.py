"""
KnowledgeService — Facade principal do Clinical Knowledge Engine.

Sprint 4.4 — Clinical Knowledge Engine v1.0.

Orquestra o pipeline:
    Replay → ClinicalGenome Projection → Correlation → Hypothesis → Knowledge Graph

Uso:
    service = KnowledgeService()
    result = service.run_pipeline(genome)  # gera correlações + hypotheses + graph
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...genome.domain.events import DomainEvent
from ...timeline.domain.window import TimeWindow
from ..domain.clinical_genome import ClinicalGenome, ClinicalGenomeBuilder
from ..domain.correlation import CorrelationEngine, CorrelationMethod, CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis, HypothesisEngine
from ..domain.knowledge_graph import KnowledgeGraph, KnowledgeGraphBuilder
from .dto import KnowledgePipelineResult
from .hypothesis_id_namespace import namespace_hypothesis_ids


class KnowledgeService:
    """Facade principal — orquestra Replay → Projection → Engines."""

    def __init__(
        self,
        *,
        correlation_engine: CorrelationEngine | None = None,
        hypothesis_engine: HypothesisEngine | None = None,
        graph_builder: KnowledgeGraphBuilder | None = None,
        genome_builder: ClinicalGenomeBuilder | None = None,
    ) -> None:
        self._correlation_engine = correlation_engine or CorrelationEngine()
        self._hypothesis_engine = hypothesis_engine or HypothesisEngine()
        self._graph_builder = graph_builder or KnowledgeGraphBuilder()
        self._genome_builder = genome_builder or ClinicalGenomeBuilder()

    def build_genome_from_genes(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        window: TimeWindow,
        genes: Sequence[ClinicalGene],
    ) -> ClinicalGenome:
        """Monta ClinicalGenome a partir de Genes reconstruídos."""
        return self._genome_builder.build_from_genes(
            tenant_id=tenant_id,
            patient_id=patient_id,
            window=window,
            genes=genes,
        )

    def build_genome_from_events(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        window: TimeWindow,
        events_by_gene: dict[str, Sequence[DomainEvent]],
    ) -> ClinicalGenome:
        """Monta ClinicalGenome via replay de eventos."""
        return self._genome_builder.build_from_events(
            tenant_id=tenant_id,
            patient_id=patient_id,
            window=window,
            events_by_gene=events_by_gene,
        )

    def compute_correlations(
        self,
        genome: ClinicalGenome,
        *,
        method: CorrelationMethod = CorrelationMethod.POSITIVE,
    ) -> tuple[CorrelationResult, ...]:
        """Calcula correlações entre Genes do genome."""
        return self._correlation_engine.compute(genome, method=method)

    def compute_all_correlations(
        self, genome: ClinicalGenome
    ) -> tuple[CorrelationResult, ...]:
        """Calcula todas as correlações (todos os métodos)."""
        all_results: list[CorrelationResult] = []
        for method in CorrelationMethod:
            all_results.extend(self._correlation_engine.compute(genome, method=method))
        return tuple(all_results)

    def generate_hypotheses(
        self,
        genome: ClinicalGenome,
        correlations: Sequence[CorrelationResult],
    ) -> tuple[ClinicalHypothesis, ...]:
        """Gera hipóteses a partir do genome + correlações.

        Aplica tenant-namespacing em hypothesis_id (task #197) para
        evitar colisão cross-tenant em IDs content-derived.
        """
        raw = self._hypothesis_engine.generate(genome, correlations)
        return namespace_hypothesis_ids(raw, genome.tenant_id)

    def build_graph(
        self,
        genome: ClinicalGenome,
        *,
        correlations: Sequence[CorrelationResult] = (),
        hypotheses: Sequence[ClinicalHypothesis] = (),
    ) -> KnowledgeGraph:
        """Constrói KnowledgeGraph integrado."""
        return self._graph_builder.build(
            genome, correlations=correlations, hypotheses=hypotheses
        )

    def run_pipeline(
        self,
        genome: ClinicalGenome,
        *,
        methods: Sequence[CorrelationMethod] | None = None,
        include_graph: bool = True,
    ) -> KnowledgePipelineResult:
        """Executa pipeline completo: Correlation → Hypothesis → Graph.

        Args:
            genome: ClinicalGenome (read-model).
            methods: lista de CorrelationMethod a aplicar (default: todos).
            include_graph: se True, constrói KnowledgeGraph.

        Returns:
            KnowledgePipelineResult com correlations, hypotheses, graph opcional.
        """
        started_at = datetime.now(timezone.utc)
        # 1) Correlações
        if methods is None:
            correlations = self.compute_all_correlations(genome)
        else:
            all_corr: list[CorrelationResult] = []
            for m in methods:
                all_corr.extend(self._correlation_engine.compute(genome, method=m))
            correlations = tuple(all_corr)
        # 2) Hipóteses (com tenant-namespacing no hypothesis_id — task #197)
        raw_hypotheses = self._hypothesis_engine.generate(genome, correlations)
        hypotheses = namespace_hypothesis_ids(raw_hypotheses, genome.tenant_id)
        # 3) Graph (opcional)
        graph: KnowledgeGraph | None = None
        if include_graph:
            graph = self._graph_builder.build(
                genome, correlations=correlations, hypotheses=hypotheses
            )
        completed_at = datetime.now(timezone.utc)
        return KnowledgePipelineResult(
            genome=genome,
            correlations=correlations,
            hypotheses=hypotheses,
            graph=graph,
            started_at=started_at,
            completed_at=completed_at,
        )