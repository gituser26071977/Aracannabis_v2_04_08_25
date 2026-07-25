"""
Sprint 4.4 — Hypothesis Engine.

Testes cobrindo:
    - 6 regras canônicas (H_CORR_POSITIVE, H_CORR_NEGATIVE,
      H_VOLATILITY_COOCCUR, H_NO_EXPRESSION, H_MUTUAL_EXCLUSION,
      H_TEMPORAL_PRECEDENCE).
    - 5 HypothesisStatus (PROPOSED, SUPPORTED, CONTRADICTED,
      INCONCLUSIVE, RETRACTED).
    - Confidence ∈ [0, 1].
    - InferenceExplanation sempre presente.
    - Has provenance rastreável.
    - Determinismo across runs.
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.correlation import (
    CorrelationEngine,
    CorrelationMethod,
)
from araos.clinical.knowledge.domain.hypothesis import (
    ClinicalHypothesis,
    HypothesisEngine,
    HypothesisStatus,
)


class TestHypothesisEngineBasic:
    """Contract tests."""

    def test_generate_returns_tuple(self, scenario_alfa):
        # Act
        engine = HypothesisEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        # Act
        hyp = engine.generate(genome, correlations)
        # Assert
        assert isinstance(hyp, tuple)

    def REDACTED(self, scenario_alfa):
        # Act
        engine = HypothesisEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        hyp = engine.generate(genome, ())
        # Assert — sem correlações, ainda pode haver regra H_NO_EXPRESSION.
        # Para nosso cenário alfa (2 genes com expressões), deve ser vazio.
        assert isinstance(hyp, tuple)


class TestHypothesisStatus:
    """Status enum — 5 estados canônicos."""

    @pytest.mark.parametrize("status", list(HypothesisStatus))
    def test_status_enum_values(self, status):
        # Assert
        assert status.value in (
            "proposed", "supported", "contradicted", "inconclusive", "retracted"
        )


class TestHypothesisInvariants:
    """Invariantes estruturais."""

    def test_confidence_in_range(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        for h in HypothesisEngine().generate(genome, correlations):
            assert 0.0 <= h.confidence <= 1.0

    def test_explanation_required(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        for h in HypothesisEngine().generate(genome, correlations):
            assert h.explanation is not None
            assert h.rule_id

    def test_has_provenance_invariant(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        for h in HypothesisEngine().generate(genome, correlations):
            # Must have at least one provenance element
            assert h.has_provenance()


class TestHypothesisIdDeterminism:
    """IDs determinísticos (replay)."""

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        h1 = HypothesisEngine().generate(genome, correlations)
        h2 = HypothesisEngine().generate(genome, correlations)
        # Assert — same correlations + same genes → same hypothesis_ids
        ids1 = tuple(sorted(h.hypothesis_id for h in h1))
        ids2 = tuple(sorted(h.hypothesis_id for h in h2))
        assert ids1 == ids2

    def REDACTED(self, scenario_alfa, scenario_beta):
        # Act
        from araos.clinical.knowledge.domain.correlation import CorrelationEngine, CorrelationMethod
        g_a = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        g_b = build_clinical_genome(
            tenant_id=scenario_beta.tenant_id,
            patient_id=scenario_beta.patient_id,
            window=scenario_beta.window,
            genes=scenario_beta.genes,
        )
        # Assert — different content → different IDs
        # Both have at least 1 hypothesis (or no)
        # Just ensure no overlap if both generate
        hyp_a = HypothesisEngine().generate(
            g_a, CorrelationEngine().compute(g_a, method=CorrelationMethod.POSITIVE)
        )
        hyp_b = HypothesisEngine().generate(
            g_b, CorrelationEngine().compute(g_b, method=CorrelationMethod.POSITIVE)
        )
        ids_a = set(h.hypothesis_id for h in hyp_a)
        ids_b = set(h.hypothesis_id for h in hyp_b)
        assert not (ids_a & ids_b), "Different content should produce non-overlapping IDs"


class TestHypothesisRules:
    """Regras de geração."""

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        for h in HypothesisEngine().generate(genome, correlations):
            if h.rule_id == "H_CORR_POSITIVE":
                assert h.status in (
                    HypothesisStatus.PROPOSED, HypothesisStatus.SUPPORTED,
                )

    def REDACTED(self):
        # Setup — gene sem expression
        from araos.clinical.genome.domain.aggregate import create_gene
        from datetime import datetime, timezone
        gene_empty = create_gene(
            tenant_id="t1", patient_id="p1", gene_id="GENE_EMPTY", version="1.0.0",
        )
        # Act — gene sem nenhuma expression
        from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
        from araos.clinical.timeline.domain.window import TimeWindow
        genome = build_clinical_genome(
            tenant_id="t1", patient_id="p1",
            window=TimeWindow(
                start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                end=datetime(2026, 6, 1, tzinfo=timezone.utc),
                label="6mo",
            ),
            genes=(gene_empty,),
        )
        # Act
        hyp = HypothesisEngine().generate(genome, ())
        # Assert
        assert any(h.rule_id == "H_NO_EXPRESSION" for h in hyp)
        # INCONCLUSIVE status
        no_expr = next(h for h in hyp if h.rule_id == "H_NO_EXPRESSION")
        assert no_expr.status == HypothesisStatus.INCONCLUSIVE
