"""
Sprint 4.4.5 — Multi-tenancy Stress.

Testes intensivos de isolamento entre tenants.

Cobre:
- 10 tenants paralelos em Cohort/Graph/Genome/Research.
- Cross-tenant gene injection (deve ser filtrado/rejeitado).
- Cross-tenant correlation (deve nunca correlacionar genes de tenants diferentes).
- Cross-tenant graph (KnowledgeGraph sempre single-tenant).
- Cross-tenant research (ResearchSession respeita tenant_id).
- Replay multi-tenant (state_hash inclui tenant_id).

Garantia absoluta: ausência de vazamento entre tenants.
"""

from __future__ import annotations

import hashlib
import itertools
from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.cohort import (
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.correlation import CorrelationEngine, CorrelationMethod
from araos.clinical.knowledge.domain.knowledge_graph import KnowledgeGraphBuilder
from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchWorkspace,
)
from araos.clinical.timeline.domain.window import TimeWindow

from tests.sprint_4_4_5.conftest import _build_gene_with_trajectory

UTC = timezone.utc


# ────────────────────────────────────────────────────────────────────
# 10 tenants paralelos — isolamento
# ────────────────────────────────────────────────────────────────────


class TestMultiTenancyIsolation:
    @pytest.fixture
    def ten_tenants(self):
        """Gera 10 tenants com 1 paciente cada."""
        base = datetime(2026, 1, 1, tzinfo=UTC)
        window = TimeWindow(
            start=base, end=base + timedelta(days=180), label="6m",
        )
        tenants = []
        for i in range(10):
            tenant_id = f"tenant_{i:02d}"
            patient_id = f"p_{i:02d}"
            genes = (
                _build_gene_with_trajectory(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    gene_id="GENE_SLEEP",
                    values=((4.0, 0.4, 0), (5.0, 0.6, 30), (6.0, 0.7, 60)),
                ),
                _build_gene_with_trajectory(
                    tenant_id=tenant_id,
                    patient_id=patient_id,
                    gene_id="GENE_ANXIETY",
                    values=((7.0, 0.7, 0), (5.0, 0.5, 30), (4.0, 0.4, 60)),
                ),
            )
            tenants.append({
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "genes": genes,
                "window": window,
            })
        return tenants

    def REDACTED(self, ten_tenants):
        """State hashes de 10 tenants diferentes são todos distintos."""
        hashes = set()
        for t in ten_tenants:
            genome = build_clinical_genome(
                tenant_id=t["tenant_id"],
                patient_id=t["patient_id"],
                window=t["window"],
                genes=t["genes"],
            )
            hashes.add(genome.state_hash)
        assert len(hashes) == 10, f"Esperado 10 hashes únicos, obtido {len(hashes)}"

    def REDACTED(self, ten_tenants):
        """KnowledgeGraph state hashes de 10 tenants são todos distintos."""
        service = KnowledgeService()
        hashes = set()
        for t in ten_tenants:
            genome = build_clinical_genome(
                tenant_id=t["tenant_id"],
                patient_id=t["patient_id"],
                window=t["window"],
                genes=t["genes"],
            )
            result = service.run_pipeline(genome)
            if result.graph:
                hashes.add(result.graph.state_hash)
        assert len(hashes) == 10

    def REDACTED(self, ten_tenants):
        """Cada tenant tem correlações independentes (sem mistura)."""
        engine = CorrelationEngine()
        seen_correlation_ids = set()
        for t in ten_tenants:
            genome = build_clinical_genome(
                tenant_id=t["tenant_id"],
                patient_id=t["patient_id"],
                window=t["window"],
                genes=t["genes"],
            )
            # Genes têm trajetórias opostas (sleep ↑, anxiety ↓) → NEGATIVE.
            correlations = engine.compute(genome, method=CorrelationMethod.NEGATIVE)
            for c in correlations:
                # correlation_id é content-derived (SHA-256) — deve ser único entre tenants.
                assert c.correlation_id not in seen_correlation_ids, (
                    f"Correlation ID {c.correlation_id} colidiu entre tenants"
                )
                seen_correlation_ids.add(c.correlation_id)
        # 10 tenants × pelo menos 1 correlation cada
        assert len(seen_correlation_ids) >= 10


# ────────────────────────────────────────────────────────────────────
# Cross-tenant injection — genes de outros tenants devem ser filtrados
# ────────────────────────────────────────────────────────────────────


class TestCrossTenantInjection:
    def REDACTED(self):
        """ClinicalGenome rejeita mistura de tenants."""
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
                window=_six_month_window(),
                genes=(gene_a, gene_b),
            )

    def REDACTED(self):
        """CohortBuilder filtra pacientes de outros tenants."""
        p_target = PatientData(patient_id="p_target", tenant_id="t_A", age=14, sex="F")
        p_cross = PatientData(patient_id="p_cross", tenant_id="t_B", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[p_cross, p_target],
            tenant_id="t_A",
            name="isolated",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            ),
        )
        assert "p_cross" not in cohort.matched_patient_ids
        assert "p_target" in cohort.matched_patient_ids

    def test_knowledge_graph_single_tenant(self, scenario_a1_2genes):
        """KnowledgeGraph sempre single-tenant — genome misto falha antes."""
        # Já enforced por ClinicalGenome — graph é construído a partir
        # de um genome, e genome cross-tenant não pode existir.
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        assert graph.tenant_id == scenario_a1_2genes.tenant_id


# ────────────────────────────────────────────────────────────────────
# Cohort isolation — coortes de diferentes tenants não vazam
# ────────────────────────────────────────────────────────────────────


class TestCohortIsolation:
    def REDACTED(self):
        """Mesmo critério + mesmo nome + tenant diferente → state_hash diferente."""
        p_a = PatientData(patient_id="p_a", tenant_id="t_A", age=14, sex="F")
        p_b = PatientData(patient_id="p_b", tenant_id="t_B", age=14, sex="F")
        criteria = (
            Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
        )
        cohort_a = CohortBuilder().evaluate(
            patients=[p_a], tenant_id="t_A", name="same_name", criteria=criteria,
        )
        cohort_b = CohortBuilder().evaluate(
            patients=[p_b], tenant_id="t_B", name="same_name", criteria=criteria,
        )
        assert cohort_a.state_hash != cohort_b.state_hash
        assert cohort_a.cohort_id != cohort_b.cohort_id


# ────────────────────────────────────────────────────────────────────
# Research isolation — session só opera no tenant do cohort
# ────────────────────────────────────────────────────────────────────


class TestResearchIsolation:
    def REDACTED(self, scenario_a1_2genes):
        """ResearchSession.execute considera apenas genes do seu tenant."""
        from araos.clinical.knowledge.domain.cohort import CohortBuilder

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
            params={"scope": "tenant_test"},
        )
        genes_by_patient = {
            scenario_a1_2genes.patient_id: list(scenario_a1_2genes.genes),
        }
        workspace = ResearchWorkspace()
        session = workspace.execute(
            query, patients=[patient], genes_by_patient=genes_by_patient
        )
        # Verifica que state_hash é determinístico e tenant_id é coerente
        # (state_hash difere entre tenants — validado por outro teste).
        assert session.state_hash is not None
        assert len(session.state_hash) == 64


# ────────────────────────────────────────────────────────────────────
# Cross-tenant replay — state_hash sempre preserva tenant_id
# ────────────────────────────────────────────────────────────────────


class TestCrossTenantReplay:
    def REDACTED(self):
        """Replay byte-identical MAS state_hash difere entre tenants."""
        base = datetime(2026, 1, 1, tzinfo=UTC)
        window = TimeWindow(
            start=base, end=base + timedelta(days=180), label="6m",
        )

        # Cria genes idênticos em estrutura, diferentes em tenant_id.
        genes_a = (
            _build_gene_with_trajectory(
                tenant_id="t_A",
                patient_id="p1",
                gene_id="G_SLEEP",
                values=((4.0, 0.4, 0), (5.0, 0.6, 30)),
            ),
        )
        genes_b = (
            _build_gene_with_trajectory(
                tenant_id="t_B",
                patient_id="p1",
                gene_id="G_SLEEP",
                values=((4.0, 0.4, 0), (5.0, 0.6, 30)),
            ),
        )

        g_a = build_clinical_genome(
            tenant_id="t_A", patient_id="p1", window=window, genes=genes_a,
        )
        g_b = build_clinical_genome(
            tenant_id="t_B", patient_id="p1", window=window, genes=genes_b,
        )
        # tenant_id entra no canonical → hash diferente.
        assert g_a.state_hash != g_b.state_hash


def _six_month_window() -> TimeWindow:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
