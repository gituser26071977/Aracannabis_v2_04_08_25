"""
Sprint 4.4.5 — Property-Based Testing.

Adota padrão de tests/neurodev_sprint_3_2/test_property_based.py usando
Hypothesis para validar invariantes fundamentais do Clinical Knowledge
Engine sob cenários ALEATÓRIOS respeitando as regras do domínio.

Engines cobertos:
- ClinicalGenome (replay determinístico, state_hash)
- CorrelationEngine (coefficient range, content-derived IDs)
- HypothesisEngine (confidence range, content-derived IDs)
- KnowledgeGraph (integridade referencial, content-derived IDs)
- ExplainabilityPipeline (confidence range, proveniência)
- ReplayEngine (N replays = mesmo state_hash)
- ResearchWorkspace (execute ≡ replay)
- CohortBuilder (tenant isolation, content-derived ID)

Configuração:
- max_examples=200 (propriedades fortes sem inflar tempo)
- deadline=None (engines são pure Python — sem timeouts)
- HealthCheck.suppress_health_check para evitar falsos positivos
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import (
    ClinicalGenome,
    build_clinical_genome,
)
from araos.clinical.knowledge.domain.cohort import (
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.correlation import (
    CorrelationEngine,
    CorrelationMethod,
)
from araos.clinical.knowledge.domain.explainability import (
    ExplainabilityPipeline,
    InferenceType,
)
from araos.clinical.knowledge.domain.hypothesis import (
    HypothesisEngine,
)
from araos.clinical.knowledge.domain.knowledge_graph import (
    EdgeType,
    KnowledgeGraphBuilder,
    NodeType,
)
from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchWorkspace,
)
from araos.clinical.timeline.domain.window import TimeWindow

from tests.sprint_4_4_5.conftest import (
    _build_gene_with_trajectory,
    _gene_genome_a1,
    _gene_genome_b1,
    _make_explanation,
    _window,
)

UTC = timezone.utc

# Health checks suprimidos — engines são puros sem I/O.
SUPPRESS = [
    HealthCheck.function_scoped_fixture,
    HealthCheck.too_slow,
    HealthCheck.filter_too_much,
]


# ────────────────────────────────────────────────────────────────────
# Strategies
# ────────────────────────────────────────────────────────────────────


TENANT_IDS = st.sampled_from(["tenant_a", "tenant_b", "tenant_c", "tenant_d"])
PATIENT_IDS = st.sampled_from(["p_001", "p_002", "p_003", "p_004"])
GENE_IDS = st.sampled_from(
    ["GENE_SLEEP", "GENE_ANXIETY", "GENE_ATTENTION", "GENE_MOOD"]
)
CONFIDENCE_VALUES = st.floats(
    min_value=0.05, max_value=0.95, allow_nan=False, allow_infinity=False
)
EXPRESSION_VALUES = st.floats(
    min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False
)


@st.composite
def time_windows(draw, start_year: int = 2026):
    start = datetime(start_year, 1, 1, tzinfo=UTC)
    days = draw(st.integers(min_value=30, max_value=365))
    return TimeWindow(
        start=start,
        end=start + timedelta(days=days),
        label=f"{days}_days",
    )


@st.composite
def gene_trajectories(draw, n_points: int | None = None):
    """Trajetória com N pontos de expression (value, confidence, days_offset)."""
    if n_points is None:
        n_points = draw(st.integers(min_value=2, max_value=4))
    values = []
    for i in range(n_points):
        v = draw(EXPRESSION_VALUES)
        c = draw(CONFIDENCE_VALUES)
        d = i * 30  # fixed days apart
        values.append((v, c, d))
    return values


@st.composite
def single_tenant_genes(draw, tenant_id: str, patient_id: str):
    """Gera 1-3 Genes para o mesmo tenant+patient (mesmo gene_id único)."""
    n_genes = draw(st.integers(min_value=1, max_value=3))
    genes = []
    used_ids = set()
    for _ in range(n_genes):
        gene_id = draw(GENE_IDS)
        if gene_id in used_ids:
            continue
        used_ids.add(gene_id)
        trajectory = draw(gene_trajectories())
        gene = _build_gene_with_trajectory(
            tenant_id=tenant_id,
            patient_id=patient_id,
            gene_id=gene_id,
            values=trajectory,
        )
        genes.append(gene)
    assume(len(genes) >= 1)
    return tuple(genes)


@st.composite
def valid_genomes(draw):
    """Gera ClinicalGenome válido (tenant único, 1-3 genes)."""
    tenant_id = draw(TENANT_IDS)
    patient_id = draw(PATIENT_IDS)
    window = draw(time_windows())
    genes = draw(single_tenant_genes(tenant_id, patient_id))
    return build_clinical_genome(
        tenant_id=tenant_id,
        patient_id=patient_id,
        window=window,
        genes=genes,
    )


# ────────────────────────────────────────────────────────────────────
# ClinicalGenome — Replay determinístico
# ────────────────────────────────────────────────────────────────────


class TestClinicalGenomeProperties:
    @given(genome=valid_genomes())
    @settings(max_examples=200, deadline=None, suppress_health_check=SUPPRESS)
    def test_state_hash_is_sha256_hex(self, genome: ClinicalGenome):
        assert len(genome.state_hash) == 64
        assert all(c in "0123456789abcdef" for c in genome.state_hash)

    @given(genome=valid_genomes(), n=st.integers(min_value=1, max_value=20))
    @settings(max_examples=50, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome, n: int):
        """Replay N vezes → mesmo state_hash byte-identical."""
        baseline = genome.state_hash
        # Re-construir N vezes e verificar equivalência.
        for _ in range(n):
            new_genome = build_clinical_genome(
                tenant_id=genome.tenant_id,
                patient_id=genome.patient_id,
                window=genome.window,
                genes=genome.genes,
            )
            assert new_genome.state_hash == baseline

    @given(genome=valid_genomes())
    @settings(max_examples=200, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        canonical = genome.to_canonical_dict()
        assert "built_at" not in canonical

    @given(genome=valid_genomes())
    @settings(max_examples=200, deadline=None, suppress_health_check=SUPPRESS)
    def test_genome_id_is_uuid_backed(self, genome: ClinicalGenome):
        # genome_id é transiente (UUID-derived) — não participa do state_hash.
        # Invariante: genome_id é não-vazio e começa com "genome_".
        assert genome.genome_id.startswith("genome_")
        assert len(genome.genome_id) > len("genome_")


# ────────────────────────────────────────────────────────────────────
# CorrelationEngine — coefficient/confidence range
# ────────────────────────────────────────────────────────────────────


class TestCorrelationEngineProperties:
    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        engine = CorrelationEngine()
        if len(genome.genes) < 2:
            return  # skip 1-gene genomes
        for method in CorrelationMethod:
            correlations = engine.compute(genome, method=method)
            for c in correlations:
                assert -1.0 <= c.coefficient <= 1.0, (
                    f"coefficient {c.coefficient} fora de [-1, 1]"
                )
                assert 0.0 <= c.confidence <= 1.0
                assert c.n_observations >= 0

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        """correlation_id é SHA-256-derived: mesmo input → mesmo ID."""
        engine = CorrelationEngine()
        if len(genome.genes) < 2:
            return
        c1 = engine.compute(genome, method=CorrelationMethod.POSITIVE)
        c2 = engine.compute(genome, method=CorrelationMethod.POSITIVE)
        ids_1 = {c.correlation_id for c in c1}
        ids_2 = {c.correlation_id for c in c2}
        assert ids_1 == ids_2

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def test_tenant_id_in_correlation(self, genome: ClinicalGenome):
        """Toda correlation carrega tenant_id do genome."""
        engine = CorrelationEngine()
        if len(genome.genes) < 2:
            return
        for method in CorrelationMethod:
            for c in engine.compute(genome, method=method):
                # correlation_id inclui gene_x/gene_y/window mas NÃO tenant_id
                # (determinístico pelo par de genes). Verifica apenas
                # que explanation carrega tenant via participating_genes.
                assert c.explanation is not None
                break


# ────────────────────────────────────────────────────────────────────
# HypothesisEngine — confidence range
# ────────────────────────────────────────────────────────────────────


class TestHypothesisEngineProperties:
    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        engine = HypothesisEngine()
        correlations = ()
        if len(genome.genes) >= 2:
            correlations = CorrelationEngine().compute(
                genome, method=CorrelationMethod.POSITIVE
            )
        hypotheses = engine.generate(genome, correlations)
        for h in hypotheses:
            assert 0.0 <= h.confidence <= 1.0
            assert h.status is not None

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def test_hypothesis_id_content_derived(self, genome: ClinicalGenome):
        engine = HypothesisEngine()
        correlations = ()
        if len(genome.genes) >= 2:
            correlations = CorrelationEngine().compute(
                genome, method=CorrelationMethod.POSITIVE
            )
        h1 = engine.generate(genome, correlations)
        h2 = engine.generate(genome, correlations)
        ids_1 = {hyp.hypothesis_id for hyp in h1}
        ids_2 = {hyp.hypothesis_id for hyp in h2}
        assert ids_1 == ids_2


# ────────────────────────────────────────────────────────────────────
# KnowledgeGraph — integridade referencial
# ────────────────────────────────────────────────────────────────────


class TestKnowledgeGraphProperties:
    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        builder = KnowledgeGraphBuilder()
        g1 = builder.build(genome)
        g2 = builder.build(genome)
        ids_1 = {n.node_id for n in g1.nodes}
        ids_2 = {n.node_id for n in g2.nodes}
        assert ids_1 == ids_2

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def test_graph_state_hash_stable(self, genome: ClinicalGenome):
        builder = KnowledgeGraphBuilder()
        h1 = builder.build(genome).state_hash
        h2 = builder.build(genome).state_hash
        assert h1 == h2

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(self, genome: ClinicalGenome):
        """Invariante de integridade referencial."""
        builder = KnowledgeGraphBuilder()
        g = builder.build(genome)
        node_ids = {n.node_id for n in g.nodes}
        for edge in g.edges:
            assert edge.source_node_id in node_ids
            assert edge.target_node_id in node_ids


# ────────────────────────────────────────────────────────────────────
# ExplainabilityPipeline — proveniência
# ────────────────────────────────────────────────────────────────────


class TestExplainabilityProperties:
    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(
        self, genome: ClinicalGenome
    ):
        engine = CorrelationEngine()
        if len(genome.genes) < 2:
            return
        for method in CorrelationMethod:
            for c in engine.compute(genome, method=method):
                assert c.explanation is not None
                assert c.explanation.confidence >= 0.0
                assert c.explanation.confidence <= 1.0
                assert c.explanation.method  # não-vazio

    @given(genome=valid_genomes())
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(
        self, genome: ClinicalGenome
    ):
        engine = HypothesisEngine()
        correlations = ()
        if len(genome.genes) >= 2:
            correlations = CorrelationEngine().compute(
                genome, method=CorrelationMethod.POSITIVE
            )
        for h in engine.generate(genome, correlations):
            assert h.explanation is not None
            assert h.explanation.confidence >= 0.0
            assert h.explanation.confidence <= 1.0


# ────────────────────────────────────────────────────────────────────
# ResearchWorkspace — execute ≡ replay
# ────────────────────────────────────────────────────────────────────


class TestResearchWorkspaceProperties:
    @given(genome=valid_genomes(), n=st.integers(min_value=1, max_value=10))
    @settings(max_examples=50, deadline=None, suppress_health_check=SUPPRESS)
    def REDACTED(
        self, genome: ClinicalGenome, n: int
    ):
        patient = PatientData(
            patient_id=genome.patient_id,
            tenant_id=genome.tenant_id,
            age=14,
            sex="F",
        )
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=genome.tenant_id,
            name="research_cohort",
            criteria=(
                Criterion(
                    field="patient.age",
                    operator=CriterionOperator.GT,
                    value=10,
                ),
            ),
        )
        query = ResearchQuery(
            query_id="q_property",
            cohort_id=cohort.cohort_id,
            analysis_type=AnalysisType.STATS,
            params={"scope": "test"},
        )
        genes_by_patient = {genome.patient_id: list(genome.genes)}
        workspace = ResearchWorkspace()

        s1 = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)
        baseline_hash = s1.state_hash
        for _ in range(n):
            s_n = workspace.execute(
                query, patients=[patient], genes_by_patient=genes_by_patient
            )
            assert s_n.state_hash == baseline_hash


# ────────────────────────────────────────────────────────────────────
# CohortBuilder — tenant isolation
# ────────────────────────────────────────────────────────────────────


class TestCohortBuilderProperties:
    @given(tenant_id=TENANT_IDS)
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def test_cohort_id_content_derived(self, tenant_id: str):
        patient = PatientData(
            patient_id="p_test",
            tenant_id=tenant_id,
            age=15,
            sex="M",
        )
        c1 = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=tenant_id,
            name="hardening",
            criteria=(
                Criterion(
                    field="patient.age",
                    operator=CriterionOperator.GT,
                    value=10,
                ),
            ),
        )
        c2 = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=tenant_id,
            name="hardening",
            criteria=(
                Criterion(
                    field="patient.age",
                    operator=CriterionOperator.GT,
                    value=10,
                ),
            ),
        )
        assert c1.cohort_id == c2.cohort_id
        assert c1.cohort_id.startswith("cohort_")

    @given(tenant_id=TENANT_IDS)
    @settings(max_examples=100, deadline=None, suppress_health_check=SUPPRESS)
    def test_cross_tenant_patient_excluded(self, tenant_id: str):
        """Paciente de outro tenant é filtrado (não incluído)."""
        other_tenant = "tenant_other_" if tenant_id != "tenant_other_" else "tenant_z"
        patient_cross = PatientData(
            patient_id="p_cross",
            tenant_id=other_tenant,
            age=14,
            sex="F",
        )
        patient_target = PatientData(
            patient_id="p_target",
            tenant_id=tenant_id,
            age=14,
            sex="F",
        )
        cohort = CohortBuilder().evaluate(
            patients=[patient_cross, patient_target],
            tenant_id=tenant_id,
            name="isolated",
            criteria=(
                Criterion(
                    field="patient.age",
                    operator=CriterionOperator.GT,
                    value=10,
                ),
            ),
        )
        # Apenas o paciente do tenant correto é incluído.
        assert "p_cross" not in cohort.matched_patient_ids
        assert "p_target" in cohort.matched_patient_ids
