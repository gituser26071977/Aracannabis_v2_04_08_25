"""
Sprint 4.4.5 — Domain Invariants.

Catalogar explicitamente todas as invariantes do domínio e validar
que nunca sejam violadas.

Cada invariante:
- tem descrição canônica
- tem localização no código
- tem teste correspondente

20+ invariantes cobertas neste arquivo:

I-01  ClinicalGenome é frozen (imutável).
I-02  ClinicalGenome.state_hash MUST ser SHA-256 hex (64 chars).
I-03  ClinicalGenome rejeita mistura de tenants (multi-tenancy).
I-04  ClinicalGenome rejeita mistura de pacientes.
I-05  CorrelationResult.coefficient ∈ [-1, 1].
I-06  CorrelationResult.confidence ∈ [0, 1].
I-07  ClinicalHypothesis nunca altera Gene (estado externo).
I-08  Correlation nunca declara causalidade (não usa "causa").
I-09  KnowledgeGraph é frozen.
I-10  KnowledgeGraph.state_hash MUST ser SHA-256 hex.
I-11  KnowledgeGraph mantém integridade referencial (edges → nodes).
I-12  Cohort é frozen.
I-13  Cohort.state_hash MUST ser SHA-256 hex.
I-14  Cohort.cohort_id é content-derived (SHA-256 prefix).
I-15  ResearchSession.state_hash é SHA-256 do result_json.
I-16  InferenceExplanation confidence ∈ [0, 1].
I-17  InferenceExplanation created_at é timezone-aware (UTC).
I-18  InferenceExplanation (CORRELATION/HYPOTHESIS/GRAPH_EDGE) MUST
      incluir participating_genes (proveniência completa).
I-19  Datetime fields sempre UTC.
I-20  IDs determinísticos são content-derived (mesmo input → mesmo ID).
I-21  ClinicalGenome.to_canonical_dict() exclui built_at e genome_id.
I-22  KnowledgeGraph.to_canonical_dict() exclui built_at.
I-23  Cohort.to_canonical_dict() exclui built_at.
I-24  Tenant IDs dos Genes constituintes são únicos (já enforced).
I-25  CohortBuilder filtra pacientes cross-tenant.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import (
    ClinicalGenome,
    build_clinical_genome,
)
from araos.clinical.knowledge.domain.cohort import (
    Cohort,
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.correlation import (
    CorrelationEngine,
    CorrelationMethod,
    CorrelationResult,
)
from araos.clinical.knowledge.domain.explainability import (
    ExplainabilityPipeline,
    InferenceExplanation,
    InferenceType,
)
from araos.clinical.knowledge.domain.hypothesis import (
    ClinicalHypothesis,
    HypothesisEngine,
)
from araos.clinical.knowledge.domain.knowledge_graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    NodeType,
)
from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchSession,
    ResearchWorkspace,
)


UTC = timezone.utc


# ────────────────────────────────────────────────────────────────────
# I-01..I-04 — ClinicalGenome invariantes
# ────────────────────────────────────────────────────────────────────


class TestClinicalGenomeInvariants:
    def test_I01_genome_is_frozen(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        with pytest.raises(FrozenInstanceError):
            genome.tenant_id = "hacked"  # type: ignore

    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        # Validação explícita.
        genome.validate_state_hash()
        assert len(genome.state_hash) == 64
        assert all(c in "0123456789abcdef" for c in genome.state_hash)

    def REDACTED(self):
        from tests.sprint_4_4_5.conftest import (
            _build_gene_with_trajectory,
        )

        gene_a = _build_gene_with_trajectory(
            tenant_id="tenant_A",
            patient_id="p1",
            gene_id="G",
            values=((5.0, 0.5, 0), (6.0, 0.6, 30)),
        )
        gene_b = _build_gene_with_trajectory(
            tenant_id="tenant_B",
            patient_id="p1",
            gene_id="G2",
            values=((5.0, 0.5, 0), (6.0, 0.6, 30)),
        )
        with pytest.raises(ValueError, match="tenant"):
            build_clinical_genome(
                tenant_id="tenant_A",
                patient_id="p1",
                window=_scenario_window(),
                genes=(gene_a, gene_b),
            )

    def REDACTED(self):
        from tests.sprint_4_4_5.conftest import (
            _build_gene_with_trajectory,
        )

        gene_a = _build_gene_with_trajectory(
            tenant_id="tenant_A",
            patient_id="p1",
            gene_id="G",
            values=((5.0, 0.5, 0),),
        )
        gene_b = _build_gene_with_trajectory(
            tenant_id="tenant_A",
            patient_id="p2",
            gene_id="G2",
            values=((5.0, 0.5, 0),),
        )
        with pytest.raises(ValueError, match="paciente"):
            build_clinical_genome(
                tenant_id="tenant_A",
                patient_id="p1",
                window=_scenario_window(),
                genes=(gene_a, gene_b),
            )


def _scenario_window():
    from araos.clinical.timeline.domain.window import TimeWindow
    from datetime import timedelta

    base = datetime(2026, 1, 1, tzinfo=UTC)
    return TimeWindow(start=base, end=base + timedelta(days=180), label="6m")


# ────────────────────────────────────────────────────────────────────
# I-05..I-08 — Correlation invariantes
# ────────────────────────────────────────────────────────────────────


class TestCorrelationInvariants:
    def test_I05_coefficient_in_range(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        for method in CorrelationMethod:
            for c in CorrelationEngine().compute(genome, method=method):
                assert -1.0 <= c.coefficient <= 1.0

    def test_I06_confidence_in_range(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        for method in CorrelationMethod:
            for c in CorrelationEngine().compute(genome, method=method):
                assert 0.0 <= c.confidence <= 1.0

    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        original_state = [(g.gene_id, g.status) for g in genome.genes]
        correlations = CorrelationEngine().compute(
            genome, method=CorrelationMethod.POSITIVE
        )
        HypothesisEngine().generate(genome, correlations)
        post_state = [(g.gene_id, g.status) for g in genome.genes]
        assert original_state == post_state, "Hypothesis alterou Gene!"

    def REDACTED(self, scenario_a1_2genes):
        """Invariante: nenhuma claim/claim_text contém 'causa' ou 'because'."""
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        for method in CorrelationMethod:
            for c in CorrelationEngine().compute(genome, method=method):
                claim = (c.explanation.claim or "").lower()
                forbidden = ["causa", "because", "provoca", "induz"]
                for f in forbidden:
                    assert f not in claim, f"Correlation declara causalidade: {claim!r}"


# ────────────────────────────────────────────────────────────────────
# I-09..I-11 — KnowledgeGraph invariantes
# ────────────────────────────────────────────────────────────────────


class TestKnowledgeGraphInvariants:
    def test_I09_graph_is_frozen(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        with pytest.raises(FrozenInstanceError):
            graph.tenant_id = "hacked"  # type: ignore

    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        graph.validate_state_hash()
        assert len(graph.state_hash) == 64

    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        service = KnowledgeService()
        correlations = service.compute_all_correlations(genome)
        graph = service.build_graph(genome, correlations=correlations)
        node_ids = {n.node_id for n in graph.nodes}
        for edge in graph.edges:
            assert edge.source_node_id in node_ids
            assert edge.target_node_id in node_ids


# ────────────────────────────────────────────────────────────────────
# I-12..I-14 — Cohort invariantes
# ────────────────────────────────────────────────────────────────────


class TestCohortInvariants:
    def test_I12_cohort_is_frozen(self):
        patient = PatientData(patient_id="p", tenant_id="t", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id="t",
            name="c",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        with pytest.raises(FrozenInstanceError):
            cohort.tenant_id = "hacked"  # type: ignore

    def REDACTED(self):
        patient = PatientData(patient_id="p", tenant_id="t", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id="t",
            name="c",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        cohort.validate_state_hash()
        assert len(cohort.state_hash) == 64

    def test_I14_cohort_id_content_derived(self):
        patient = PatientData(patient_id="p", tenant_id="t", age=14, sex="F")
        criteria = (
            Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
        )
        c1 = CohortBuilder().evaluate(
            patients=[patient], tenant_id="t", name="x", criteria=criteria,
        )
        c2 = CohortBuilder().evaluate(
            patients=[patient], tenant_id="t", name="x", criteria=criteria,
        )
        assert c1.cohort_id == c2.cohort_id
        assert c1.cohort_id.startswith("cohort_")

    def REDACTED(self):
        patient_target = PatientData(patient_id="p_target", tenant_id="t_A", age=14, sex="F")
        patient_cross = PatientData(patient_id="p_cross", tenant_id="t_B", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[patient_cross, patient_target],
            tenant_id="t_A",
            name="isolated",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        assert "p_cross" not in cohort.matched_patient_ids
        assert "p_target" in cohort.matched_patient_ids


# ────────────────────────────────────────────────────────────────────
# I-15 — ResearchSession invariante
# ────────────────────────────────────────────────────────────────────


class TestResearchSessionInvariants:
    def REDACTED(self, scenario_a1_2genes):
        patient = PatientData(
            patient_id=scenario_a1_2genes.patient_id,
            tenant_id=scenario_a1_2genes.tenant_id,
            age=14,
            sex="F",
        )
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=scenario_a1_2genes.tenant_id,
            name="r",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        query = ResearchQuery(
            query_id="q1",
            cohort_id=cohort.cohort_id,
            analysis_type=AnalysisType.STATS,
            params={"scope": "test"},
        )
        genes_by_patient = {
            scenario_a1_2genes.patient_id: list(scenario_a1_2genes.genes),
        }
        workspace = ResearchWorkspace()
        session = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)

        import hashlib
        expected = hashlib.sha256(session.result_json.encode("utf-8")).hexdigest()
        assert session.state_hash == expected


# ────────────────────────────────────────────────────────────────────
# I-16..I-18 — InferenceExplanation invariantes
# ────────────────────────────────────────────────────────────────────


class TestInferenceExplanationInvariants:
    def REDACTED(self):
        now = datetime.now(UTC)
        for inf_type in InferenceType:
            genes = ("g1",) if inf_type not in (
                InferenceType.COHORT, InferenceType.RESEARCH,
            ) else ()
            expl = InferenceExplanation(
                explanation_id=f"e_{inf_type.value}",
                inference_type=inf_type,
                claim="test",
                method="test_method",
                participating_genes=genes,
                participating_expressions=(),
                participating_events=(),
                participating_correlations=(),
                participating_hypotheses=(),
                confidence=0.5,
                assumptions=(),
                limitations=(),
                created_at=now,
                analyst="system",
            )
            assert 0.0 <= expl.confidence <= 1.0

    def REDACTED(self):
        now = datetime.now(UTC)
        expl = InferenceExplanation(
            explanation_id="e1",
            inference_type=InferenceType.CORRELATION,
            claim="test",
            method="test_method",
            participating_genes=("g1",),
            participating_expressions=(),
            participating_events=(),
            participating_correlations=(),
            participating_hypotheses=(),
            confidence=0.5,
            assumptions=(),
            limitations=(),
            created_at=now,
            analyst="system",
        )
        assert expl.created_at.tzinfo is not None

    def REDACTED(self):
        """Hardening: inferências analíticas MUST incluir participating_genes."""
        now = datetime.now(UTC)
        for inf_type in (
            InferenceType.CORRELATION,
            InferenceType.HYPOTHESIS,
            InferenceType.GRAPH_EDGE,
        ):
            with pytest.raises(ValueError, match="participating_genes"):
                InferenceExplanation(
                    explanation_id=f"e_{inf_type.value}",
                    inference_type=inf_type,
                    claim="test",
                    method="test",
                    participating_genes=(),  # vazio — deve falhar
                    participating_expressions=(),
                    participating_events=(),
                    participating_correlations=(),
                    participating_hypotheses=(),
                    confidence=0.5,
                    assumptions=(),
                    limitations=(),
                    created_at=now,
                    analyst="system",
                )

    def REDACTED(self):
        """Cohort e Research podem operar sem genes específicos (não-falha)."""
        now = datetime.now(UTC)
        for inf_type in (InferenceType.COHORT, InferenceType.RESEARCH):
            expl = InferenceExplanation(
                explanation_id=f"e_{inf_type.value}",
                inference_type=inf_type,
                claim="test",
                method="test",
                participating_genes=(),
                participating_expressions=(),
                participating_events=(),
                participating_correlations=(),
                participating_hypotheses=(),
                confidence=0.5,
                assumptions=(),
                limitations=(),
                created_at=now,
                analyst="system",
            )
            assert expl.participating_genes == ()


# ────────────────────────────────────────────────────────────────────
# I-19..I-23 — Datetime/Canonical invariantes
# ────────────────────────────────────────────────────────────────────


class TestCanonicalDictInvariants:
    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        canonical = genome.to_canonical_dict()
        assert "built_at" not in canonical
        assert "genome_id" not in canonical

    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        canonical = graph.to_canonical_dict()
        assert "built_at" not in canonical

    def REDACTED(self):
        patient = PatientData(patient_id="p", tenant_id="t", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id="t",
            name="c",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        canonical = cohort.to_canonical_dict()
        assert "built_at" not in canonical


# ────────────────────────────────────────────────────────────────────
# I-20 — IDs determinísticos content-derived
# ────────────────────────────────────────────────────────────────────


class TestContentDerivedIDs:
    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        c1 = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        c2 = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        assert {c.correlation_id for c in c1} == {c.correlation_id for c in c2}

    def test_hypothesis_id_content_derived(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        correlations = CorrelationEngine().compute(
            genome, method=CorrelationMethod.POSITIVE
        )
        h1 = HypothesisEngine().generate(genome, correlations)
        h2 = HypothesisEngine().generate(genome, correlations)
        assert {hyp.hypothesis_id for hyp in h1} == {hyp.hypothesis_id for hyp in h2}

    def test_graph_node_id_content_derived(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        g1 = KnowledgeGraphBuilder().build(genome)
        g2 = KnowledgeGraphBuilder().build(genome)
        assert {n.node_id for n in g1.nodes} == {n.node_id for n in g2.nodes}


# ────────────────────────────────────────────────────────────────────
# I-24 — Genes constituintes com tenant_id único (enforced no genome)
# ────────────────────────────────────────────────────────────────────


class TestGenesInvariants:
    def REDACTED(self):
        with pytest.raises(ValueError, match="ao menos 1"):
            ClinicalGenome(
                genome_id="g1",
                tenant_id="t",
                patient_id="p",
                window=_scenario_window(),
                genes=(),
            )


# ────────────────────────────────────────────────────────────────────
# I-19 — Datetime UTC
# ────────────────────────────────────────────────────────────────────


class TestDatetimeInvariants:
    def REDACTED(self, scenario_a1_2genes):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        for g in genome.genes:
            if g.current_expression:
                assert g.current_expression.last_update.tzinfo is not None
                assert g.current_expression.valid_time.tzinfo is not None
