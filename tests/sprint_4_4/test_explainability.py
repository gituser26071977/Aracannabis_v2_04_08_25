"""
Sprint 4.4 — Explainability Pipeline.

Testes cobrindo:
    - InferenceExplanation obrigatória para qualquer inferência.
    - 5 elementos canônicos (participating_genes, expressions, events,
      correlations, hypotheses).
    - InferenceType enum completo (CORRELATION, HYPOTHESIS, COHORT,
      GRAPH_EDGE, RESEARCH).
    - ExplainabilityPipeline builder pattern + shortcuts.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from araos.clinical.knowledge.domain.explainability import (
    ExplainabilityPipeline,
    InferenceExplanation,
    InferenceType,
)


UTC = timezone.utc


class TestExplainabilityPipelineBasic:
    """Contract tests."""

    def test_begin_returns_builder(self):
        # Act
        builder = ExplainabilityPipeline.begin(
            inference_type=InferenceType.CORRELATION,
            claim="test",
            method="test",
            confidence=0.5,
        )
        # Assert
        assert builder is not None

    def test_explanation_id_format(self):
        # Act
        expl = (
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.CORRELATION,
                claim="test",
                method="test",
                confidence=0.5,
            )
            .with_genes(["G1"])
            .build()
        )
        # Assert — has explanation_id
        assert expl.explanation_id


class TestInferenceType:
    """InferenceType enum."""

    @pytest.mark.parametrize("infer_type", list(InferenceType))
    def test_all_inference_types(self, infer_type):
        # Assert
        assert infer_type.value in {
            "correlation", "hypothesis", "cohort",
            "graph_edge", "research",
        }


class TestExplainabilityShortcuts:
    """Shortcuts produzem InferenceExplanation coerentes."""

    def test_for_correlation(self):
        # Act
        expl = ExplainabilityPipeline.for_correlation(
            claim="corr claim",
            method="pearson",
            confidence=0.8,
            gene_x_id="G1",
            gene_y_id="G2",
            event_ids=("ev_1", "ev_2"),
        )
        # Assert
        assert expl.inference_type == InferenceType.CORRELATION
        assert expl.participating_genes == ("G1", "G2")
        assert "ev_1" in expl.participating_events

    def test_for_hypothesis(self):
        # Act
        expl = ExplainabilityPipeline.for_hypothesis(
            claim="hyp claim",
            rule_id="H_CORR_POSITIVE",
            confidence=0.7,
            gene_ids=("G1",),
            expression_refs=("expr_1:G1",),
            event_ids=("ev_1",),
            correlation_ids=("corr_1",),
        )
        # Assert
        assert expl.inference_type == InferenceType.HYPOTHESIS
        assert "H_CORR_POSITIVE" in expl.method
        assert "G1" in expl.participating_genes

    def test_for_research(self):
        # Act
        expl = ExplainabilityPipeline.for_research(
            claim="research claim",
            query_type="query_1",
            confidence=0.9,
            correlation_ids=("corr_1",),
            hypothesis_ids=("hyp_1",),
        )
        # Assert
        assert expl.inference_type == InferenceType.RESEARCH
        assert "corr_1" in expl.participating_correlations
        assert "hyp_1" in expl.participating_hypotheses


class TestExplainabilityDefaults:
    """Cross-cutting defaults enforced."""

    def test_required_fields_present(self):
        # Act
        expl = ExplainabilityPipeline.for_correlation(
            claim="x",
            method="m",
            confidence=0.5,
            gene_x_id="G1",
            gene_y_id="G2",
        )
        # Assert — all required fields present
        assert expl.participating_genes
        assert expl.created_at
        assert expl.analyst == "system"
        assert 0.0 <= expl.confidence <= 1.0

    def test_assumptions_and_limitations(self):
        # Act — Sprint 4.4.5 Hardening: GRAPH_EDGE MUST carry participating_genes.
        expl = (
            ExplainabilityPipeline.begin(
                inference_type=InferenceType.GRAPH_EDGE,
                claim="x",
                method="m",
                confidence=0.5,
            )
            .with_genes("node_x", "node_y")
            .with_assumption("test assumption")
            .with_limitation("test limitation")
            .build()
        )
        # Assert
        assert "test assumption" in expl.assumptions
        assert "test limitation" in expl.limitations


class TestInferenceExplanationImmutable:
    """InferenceExplanation é frozen."""

    def test_frozen(self):
        # Act
        expl = ExplainabilityPipeline.for_correlation(
            claim="x",
            method="m",
            confidence=0.5,
            gene_x_id="G1",
            gene_y_id="G2",
        )
        # Assert — frozen: mutation raises
        with pytest.raises((AttributeError, Exception)):
            expl.confidence = 0.9
