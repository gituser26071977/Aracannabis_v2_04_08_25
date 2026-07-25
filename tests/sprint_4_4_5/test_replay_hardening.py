"""
Sprint 4.4.5 — Replay Hardening.

Valida invariante fundamental do Clinical Knowledge Engine:
todo replay equivalente deve produzir EXATAMENTE o mesmo estado clínico.

Cobre:
- Centenas de replays consecutivos (N ∈ {100, 500, 1000}).
- Diferentes ordens de entrada (gene order permutations).
- Diferentes TimeWindows.
- Diferentes tenants.
- Diferentes combinações de genes.
- Reconstrução completa de:
    * ClinicalGenome (state_hash)
    * KnowledgeGraph (graph.state_hash)
    * Cohort (cohort.state_hash)
    * ResearchSession (session.state_hash)

Todas as comparações são byte-identical (SHA-256).
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import (
    ClinicalGenome,
    ClinicalGenomeBuilder,
    build_clinical_genome,
)
from araos.clinical.knowledge.domain.cohort import (
    Cohort,
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.knowledge_graph import KnowledgeGraph
from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchWorkspace,
)
from araos.clinical.timeline.domain.window import TimeWindow

UTC = timezone.utc


# ────────────────────────────────────────────────────────────────────
# 1. Centenas de replays consecutivos
# ────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("n_runs", [100, 500, 1000])
def REDACTED(
    scenario_a1_2genes, n_runs
):
    """100, 500, 1000 runs consecutivos → mesmo state_hash."""
    hashes = []
    for _ in range(n_runs):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        hashes.append(genome.state_hash)
    unique = set(hashes)
    assert len(unique) == 1, (
        f"ClinicalGenome.state_hash divergiu em {n_runs} runs: {len(unique)} valores distintos"
    )


@pytest.mark.parametrize("n_runs", [100, 500])
def REDACTED(
    scenario_a1_2genes, n_runs
):
    """KnowledgeGraph.state_hash estável em N runs."""
    service = KnowledgeService()
    hashes = []
    for _ in range(n_runs):
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        result = service.run_pipeline(genome)
        if result.graph:
            hashes.append(result.graph.state_hash)
    unique = set(hashes)
    assert len(unique) == 1, (
        f"KnowledgeGraph.state_hash divergiu em {n_runs} runs: {len(unique)} valores"
    )


@pytest.mark.parametrize("n_runs", [100, 500])
def REDACTED(scenario_a1_2genes, n_runs):
    """Cohort.state_hash estável em N runs."""
    patient = PatientData(
        patient_id=scenario_a1_2genes.patient_id,
        tenant_id=scenario_a1_2genes.tenant_id,
        age=14,
        sex="F",
    )
    criteria = (
        Criterion(
            field="patient.age",
            operator=CriterionOperator.GT,
            value=10,
        ),
    )
    hashes = []
    for _ in range(n_runs):
        cohort = CohortBuilder().evaluate(
            patients=[patient],
            tenant_id=scenario_a1_2genes.tenant_id,
            name="hardening_cohort",
            criteria=criteria,
        )
        hashes.append(cohort.state_hash)
    unique = set(hashes)
    assert len(unique) == 1, (
        f"Cohort.state_hash divergiu em {n_runs} runs: {len(unique)} valores"
    )


@pytest.mark.parametrize("n_runs", [100, 500])
def REDACTED(
    scenario_a1_2genes, n_runs
):
    """ResearchSession.state_hash estável em N runs (execute ≡ replay)."""
    patient = PatientData(
        patient_id=scenario_a1_2genes.patient_id,
        tenant_id=scenario_a1_2genes.tenant_id,
        age=14,
        sex="F",
    )
    cohort = CohortBuilder().evaluate(
        patients=[patient],
        tenant_id=scenario_a1_2genes.tenant_id,
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
        query_id="q_hardening",
        cohort_id=cohort.cohort_id,
        analysis_type=AnalysisType.STATS,
        params={"scope": "patient_demographics"},
    )

    service = KnowledgeService()
    genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    )
    pipeline = service.run_pipeline(genome)
    patient = PatientData(
        patient_id=scenario_a1_2genes.patient_id,
        tenant_id=scenario_a1_2genes.tenant_id,
        age=14,
        sex="F",
    )
    genes_by_patient = {
        scenario_a1_2genes.patient_id: list(scenario_a1_2genes.genes),
    }
    workspace = ResearchWorkspace()
    session1 = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)
    hashes = [session1.state_hash]

    for _ in range(n_runs - 1):
        session = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)
        hashes.append(session.state_hash)

    unique = set(hashes)
    assert len(unique) == 1, (
        f"ResearchSession.state_hash divergiu em {n_runs} runs: {len(unique)} valores"
    )


# ────────────────────────────────────────────────────────────────────
# 2. Diferentes ordens de entrada
# ────────────────────────────────────────────────────────────────────


def REDACTED(
    scenario_a1_2genes,
):
    """Todas as 2! permutações de genes produzem mesmo state_hash."""
    genes = scenario_a1_2genes.genes
    reference_genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=genes,
    )
    reference_hash = reference_genome.state_hash

    for perm in itertools.permutations(genes):
        permuted_genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=perm,
        )
        assert permuted_genome.state_hash == reference_hash, (
            f"Permutation {perm} divergiu"
        )


def REDACTED(
    scenario_a1_2genes,
):
    """KnowledgeGraph.state_hash invariante à ordem dos correlations."""
    service = KnowledgeService()
    genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    )
    correlations = list(service.compute_all_correlations(genome))
    if len(correlations) < 2:
        pytest.skip("Poucas correlações no cenário — ordenação trivial")
    reference_graph = service.build_graph(genome, correlations=correlations)
    ref_hash = reference_graph.state_hash
    for perm in itertools.permutations(correlations):
        g = service.build_graph(genome, correlations=list(perm))
        assert g.state_hash == ref_hash, f"Permutation divergiu"


# ────────────────────────────────────────────────────────────────────
# 3. Diferentes TimeWindows
# ────────────────────────────────────────────────────────────────────


def REDACTED(scenario_a1_2genes):
    """TimeWindow é parte do canonical — windows diferentes → hash diferente."""
    base_hash = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    ).state_hash

    longer = TimeWindow(
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 12, 31, tzinfo=UTC),
        label="12_months",
    )
    longer_hash = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=longer,
        genes=scenario_a1_2genes.genes,
    ).state_hash

    shorter = TimeWindow(
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 6, 1, tzinfo=UTC),
        label="3_months",
    )
    shorter_hash = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=shorter,
        genes=scenario_a1_2genes.genes,
    ).state_hash

    assert base_hash != longer_hash
    assert base_hash != shorter_hash
    assert longer_hash != shorter_hash


# ────────────────────────────────────────────────────────────────────
# 4. Diferentes tenants
# ────────────────────────────────────────────────────────────────────


def REDACTED():
    """Tenants diferentes → state_hash diferentes (mesmo genes, mesmo window)."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")

    genes_a1 = _build_patient_genes_helper("tenant_alpha", "patient_001")
    genes_b1 = _build_patient_genes_helper("tenant_beta", "patient_001")

    hash_a = build_clinical_genome(
        tenant_id="tenant_alpha",
        patient_id="patient_001",
        window=window,
        genes=genes_a1,
    ).state_hash
    hash_b = build_clinical_genome(
        tenant_id="tenant_beta",
        patient_id="patient_001",
        window=window,
        genes=genes_b1,
    ).state_hash

    assert hash_a != hash_b, "State hash deveria variar por tenant_id"


def _build_patient_genes_helper(tenant_id: str, patient_id: str) -> tuple:
    from tests.sprint_4_4_5.conftest import _build_gene_with_trajectory
    return (
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


# ────────────────────────────────────────────────────────────────────
# 5. Diferentes combinações de genes
# ────────────────────────────────────────────────────────────────────


def REDACTED(scenario_a1_2genes):
    """Subconjuntos diferentes de genes → state_hash diferente."""
    full_hash = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    ).state_hash

    sleep_only = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes[:1],
    ).state_hash

    anxiety_only = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes[1:],
    ).state_hash

    assert full_hash != sleep_only
    assert full_hash != anxiety_only
    assert sleep_only != anxiety_only


# ────────────────────────────────────────────────────────────────────
# 6. Reconstrução completa — equivalência byte-identical
# ────────────────────────────────────────────────────────────────────


def REDACTED(
    scenario_a1_2genes,
):
    """state_hash deve ser exatamente SHA-256 do canonical dict."""
    genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    )
    canonical = json.dumps(
        genome.to_canonical_dict(),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert genome.state_hash == expected


def REDACTED(scenario_a1_2genes):
    """Reexecutar graph build → mesmo state_hash byte-a-byte."""
    service = KnowledgeService()
    genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    )
    g1 = service.build_graph(genome)
    g2 = service.build_graph(genome)
    assert g1.state_hash == g2.state_hash
    # Comparação apenas via state_hash — built_at diverge por construção.


def REDACTED(scenario_a1_2genes):
    """ResearchWorkspace.execute ≡ replay — state_hash byte-idêntico."""
    patient = PatientData(
        patient_id=scenario_a1_2genes.patient_id,
        tenant_id=scenario_a1_2genes.tenant_id,
        age=14,
        sex="F",
    )
    cohort = CohortBuilder().evaluate(
        patients=[patient],
        tenant_id=scenario_a1_2genes.tenant_id,
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
        query_id="q_replay_test",
        cohort_id=cohort.cohort_id,
        analysis_type=AnalysisType.STATS,
        params={"scope": "patient_demographics"},
    )
    service = KnowledgeService()
    genome = build_clinical_genome(
        tenant_id=scenario_a1_2genes.tenant_id,
        patient_id=scenario_a1_2genes.patient_id,
        window=scenario_a1_2genes.window,
        genes=scenario_a1_2genes.genes,
    )
    pipeline = service.run_pipeline(genome)
    patient = PatientData(
        patient_id=scenario_a1_2genes.patient_id,
        tenant_id=scenario_a1_2genes.tenant_id,
        age=14,
        sex="F",
    )
    genes_by_patient = {
        scenario_a1_2genes.patient_id: list(scenario_a1_2genes.genes),
    }
    workspace = ResearchWorkspace()
    s1 = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)
    s2 = workspace.execute(query, patients=[patient], genes_by_patient=genes_by_patient)
    assert s1.state_hash == s2.state_hash
    assert s1.result_json == s2.result_json
