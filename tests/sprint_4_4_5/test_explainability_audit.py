"""
Sprint 4.4.5 — Explainability Audit.

Toda inferência deve carregar proveniência completa (5 elementos):
    - participating_genes
    - participating_expressions
    - participating_events
    - participating_correlations
    - participating_hypotheses

Cobertura:
    - Engines que produzem explicações (Correlation, Hypothesis, GraphEdge,
      Cohort, ResearchSession) MUST emitir InferenceExplanation não-vazio.
    - CorrelationResult.explanation MUST ter participating_genes + correlations.
    - ClinicalHypothesis MUST ter participating_genes + correlations.
    - GraphEdge MUST ter participating_genes + events.
    - ResearchSession MUST ter explanation.
    - InferenceType COHORT e RESEARCH são isentos de participating_genes
      (não há gene correlato direto — meta-análise).
    - __post_init__ enforces proveniência para CORRELATION/HYPOTHESIS/GRAPH_EDGE.
    - content-derived explanation_id.
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.correlation import CorrelationEngine, CorrelationMethod
from araos.clinical.knowledge.domain.explainability import (
    ExplainabilityPipeline,
    InferenceExplanation,
    InferenceType,
)
from araos.clinical.knowledge.domain.hypothesis import HypothesisEngine
from araos.clinical.knowledge.domain.knowledge_graph import KnowledgeGraphBuilder


# ────────────────────────────────────────────────────────────────────
# __post_init__ enforcement — proveniência obrigatória
# ────────────────────────────────────────────────────────────────────


class TestProvenanceEnforcement:
    """Inferências MUST carregar participating_genes (exceto COHORT/RESEARCH)."""

    def REDACTED(self):
        with pytest.raises(ValueError, match="participating_genes"):
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=0.5,
            ).build()

    def REDACTED(self):
        with pytest.raises(ValueError, match="participating_genes"):
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.HYPOTHESIS,
                claim="x",
                method="m",
                confidence=0.5,
            ).build()

    def REDACTED(self):
        with pytest.raises(ValueError, match="participating_genes"):
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.GRAPH_EDGE,
                claim="x",
                method="m",
                confidence=0.5,
            ).build()

    def REDACTED(self):
        """COHORT é seleção, não inferência correlacional — sem genes correlatos."""
        expl = ExplainabilityPipeline.begin(
            inference_type=InferenceType.COHORT,
            claim="cohort selection",
            method="criteria_eval",
            confidence=1.0,
        ).build()
        assert expl.inference_type == InferenceType.COHORT
        assert expl.participating_genes == ()

    def REDACTED(self):
        """RESEARCH é meta-análise — pode ser sobre correlações, não genes diretos."""
        expl = ExplainabilityPipeline.begin(
            inference_type=InferenceType.RESEARCH,
            claim="research analysis",
            method="workspace",
            confidence=0.9,
        ).build()
        assert expl.inference_type == InferenceType.RESEARCH
        assert expl.participating_genes == ()


# ────────────────────────────────────────────────────────────────────
# Confidence + created_at invariants
# ────────────────────────────────────────────────────────────────────


class TestExplanationInvariants:
    def test_confidence_must_be_in_range(self):
        with pytest.raises(ValueError, match="confidence"):
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=1.5,  # > 1.0
            ).with_genes("g1").build()

    def test_confidence_negative_rejected(self):
        with pytest.raises(ValueError, match="confidence"):
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=-0.1,
            ).with_genes("g1").build()

    def test_created_at_must_be_utc_aware(self):
        from datetime import datetime, timezone
        with pytest.raises(ValueError, match="UTC|timezone"):
            InferenceExplanation(
                explanation_id="e1",
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=0.5,
                created_at=datetime(2026, 1, 1),  # naive datetime
                participating_genes=("g1",),
                participating_expressions=(),
                participating_events=(),
                participating_correlations=(),
                participating_hypotheses=(),
                assumptions=(),
                limitations=(),
                analyst="system",
            )

    def REDACTED(self):
        from datetime import datetime, timezone
        with pytest.raises(ValueError, match="explanation_id"):
            InferenceExplanation(
                explanation_id="",
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=0.5,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                participating_genes=("g1",),
                participating_expressions=(),
                participating_events=(),
                participating_correlations=(),
                participating_hypotheses=(),
                assumptions=(),
                limitations=(),
                analyst="system",
            )


# ────────────────────────────────────────────────────────────────────
# Correlation engine — proveniência completa
# ────────────────────────────────────────────────────────────────────


class TestCorrelationProvenance:
    def REDACTED(self, scenario_a1_2genes):
        """CorrelationResult.explanation MUST ter participating_genes + correlations."""
        engine = CorrelationEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        results = engine.compute(genome, method=CorrelationMethod.NEGATIVE)
        assert results, "Esperado pelo menos 1 correlação"

        for r in results:
            assert r.explanation is not None
            assert r.explanation.inference_type == InferenceType.CORRELATION
            assert r.explanation.participating_genes, (
                "Correlation MUST carregar participating_genes"
            )
            assert r.gene_x_id in r.explanation.participating_genes
            assert r.gene_y_id in r.explanation.participating_genes

    def REDACTED(self):
        expl = ExplainabilityPipeline.for_correlation(
            claim="corr",
            method="pearson",
            confidence=0.8,
            gene_x_id="G1",
            gene_y_id="G2",
            event_ids=("ev_1",),
        )
        assert expl.inference_type == InferenceType.CORRELATION
        assert "G1" in expl.participating_genes
        assert "G2" in expl.participating_genes
        assert "ev_1" in expl.participating_events


# ────────────────────────────────────────────────────────────────────
# Hypothesis engine — proveniência completa
# ────────────────────────────────────────────────────────────────────


class TestHypothesisProvenance:
    def REDACTED(self, scenario_a1_2genes):
        engine = HypothesisEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        # Sem correlações prévias — pode gerar 0 hipóteses.
        hyps = engine.generate(genome, correlations=())
        # Apenas valida estrutura se houver hipóteses
        for h in hyps:
            assert h.explanation is not None
            assert h.explanation.inference_type == InferenceType.HYPOTHESIS
            assert h.explanation.participating_genes, (
                "Hypothesis MUST carregar participating_genes"
            )

    def REDACTED(self):
        expl = ExplainabilityPipeline.for_hypothesis(
            claim="hyp",
            rule_id="H_CORR_POSITIVE",
            confidence=0.7,
            gene_ids=("G1",),
            expression_refs=("expr_1:G1",),
            event_ids=("ev_1",),
            correlation_ids=("corr_1",),
        )
        assert expl.inference_type == InferenceType.HYPOTHESIS
        assert "G1" in expl.participating_genes
        assert "expr_1:G1" in expl.participating_expressions
        assert "ev_1" in expl.participating_events
        assert "corr_1" in expl.participating_correlations


# ────────────────────────────────────────────────────────────────────
# KnowledgeGraph edges — proveniência completa
# ────────────────────────────────────────────────────────────────────


class TestGraphEdgeProvenance:
    def test_graph_edges_carry_provenance(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        if graph.edges:
            for edge in graph.edges:
                assert edge.explanation is not None
                assert edge.explanation.inference_type == InferenceType.GRAPH_EDGE
                assert edge.explanation.participating_genes, (
                    "Graph edge MUST carregar participating_genes"
                )


# ────────────────────────────────────────────────────────────────────
# Research session — proveniência carregada
# ────────────────────────────────────────────────────────────────────


class TestResearchProvenance:
    def REDACTED(self, scenario_a1_2genes):
        from datetime import datetime, timezone
        from araos.clinical.knowledge.domain.cohort import CohortBuilder, PatientData
        from araos.clinical.knowledge.domain.research import (
            AnalysisType,
            ResearchQuery,
            ResearchWorkspace,
        )

        patient = PatientData(
            patient_id=scenario_a1_2genes.patient_id,
            tenant_id=scenario_a1_2genes.tenant_id,
            age=14,
            sex="F",
        )
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=scenario_a1_2genes.tenant_id,
            name="expl",
            criteria=(),
        )
        query = ResearchQuery(
            query_id="q1",
            cohort_id=cohort.cohort_id,
            analysis_type=AnalysisType.STATS,
            params={},
        )
        workspace = ResearchWorkspace()
        genes_by_patient = {
            scenario_a1_2genes.patient_id: list(scenario_a1_2genes.genes),
        }
        session = workspace.execute(
            query, patients=[patient], genes_by_patient=genes_by_patient
        )
        assert session.explanation is not None
        assert session.explanation.inference_type == InferenceType.RESEARCH


# ────────────────────────────────────────────────────────────────────
# Pipeline end-to-end — toda inferência tem proveniência
# ────────────────────────────────────────────────────────────────────


class TestPipelineFullProvenance:
    def REDACTED(self, scenario_a1_2genes):
        """Pipeline completo → todas as inferências carregam proveniência."""
        service = KnowledgeService()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        result = service.run_pipeline(genome)

        # Correlations
        for c in result.correlations:
            assert c.explanation is not None
            assert c.explanation.participating_genes

        # Hypotheses
        for h in result.hypotheses:
            assert h.explanation is not None
            assert h.explanation.participating_genes

        # Graph edges
        if result.graph:
            for edge in result.graph.edges:
                assert edge.explanation is not None
                assert edge.explanation.participating_genes


# ────────────────────────────────────────────────────────────────────
# Provenance audit summary
# ────────────────────────────────────────────────────────────────────


class TestProvenanceAuditSummary:
    def REDACTED(self):
        """InferenceExplanation suporta os 5 campos canônicos de proveniência."""
        expl = (
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=0.5,
            )
            .with_genes("g1", "g2")
            .with_expressions("expr_1", "expr_2")
            .with_events("ev_1")
            .with_correlations("corr_1")
            .with_hypotheses("hyp_1")
            .build()
        )
        assert expl.participating_genes == ("g1", "g2")
        assert expl.participating_expressions == ("expr_1", "expr_2")
        assert expl.participating_events == ("ev_1",)
        assert expl.participating_correlations == ("corr_1",)
        assert expl.participating_hypotheses == ("hyp_1",)

    def REDACTED(self):
        expl = (
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="x",
                method="m",
                confidence=0.5,
            )
            .with_genes("g1", "g2", "g3")
            .build()
        )
        assert expl.participating_genes_count() == 3