"""
Sprint 4.4 — Replay Determinism.

Property-based test: pipeline completo roda N vezes (1, 2, 5, 50)
e deve produzir exatamente o mesmo state_hash para genome e graph.

Reutiliza scenarios do conftest — verifica a invariante fundamental
do Sprint 4.4: replay byte-identical através da stack inteira.
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome


@pytest.mark.parametrize("n_runs", [1, 2, 5, 50])
def test_pipeline_deterministic_n_runs(scenario_alfa, n_runs):
    # Act — execute pipeline N vezes, capture state_hashes
    hashes_g = []
    hashes_K = []

    # Build genes fresh per iteration since each run might mutate state.
    # Genes are immutable (frozen) so we can reuse them.
    for run in range(n_runs):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        result = KnowledgeService().run_pipeline(genome)
        hashes_g.append(genome.state_hash)
        hashes_K.append(result.graph.state_hash if result.graph else None)

    # Assert — all hashes identical across runs
    assert all(h == hashes_g[0] for h in hashes_g), (
        f"Genome hash differs across {n_runs} runs"
    )
    assert all(h == hashes_K[0] for h in hashes_K), (
        f"Graph hash differs across {n_runs} runs"
    )


def REDACTED(scenario_alfa):
    # Setup — build two genomes in different orders
    g1 = build_clinical_genome(
        tenant_id=scenario_alfa.tenant_id,
        patient_id=scenario_alfa.patient_id,
        window=scenario_alfa.window,
        genes=scenario_alfa.genes,
    )
    # Reuse the genes (frozen)
    g2 = build_clinical_genome(
        tenant_id=scenario_alfa.tenant_id,
        patient_id=scenario_alfa.patient_id,
        window=scenario_alfa.window,
        genes=tuple(reversed(scenario_alfa.genes)),
    )
    # Assert — genome hash is deterministic regardless of gene order
    # (because we sort genes by gene_id in canonical_dict)
    assert g1.state_hash == g2.state_hash


def REDACTED(scenario_alfa):
    # Act
    counts = []
    for _ in range(5):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        result = KnowledgeService().run_pipeline(genome)
        counts.append(result.correlation_count)
    # Assert — same number of correlations every time
    assert all(c == counts[0] for c in counts)


def REDACTED(scenario_alfa):
    # Act
    counts = []
    for _ in range(5):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        result = KnowledgeService().run_pipeline(genome)
        counts.append(result.hypothesis_count)
    # Assert — same number of hypotheses
    assert all(c == counts[0] for c in counts)


def REDACTED(scenario_alfa):
    # Act
    hashes = []
    for _ in range(5):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        result = KnowledgeService().run_pipeline(genome)
        # Include hypothesis contribution
        hashes.append((
            genome.state_hash,
            result.graph.state_hash if result.graph else None,
        ))
    # Assert
    all_g = {h[0] for h in hashes}
    all_K = {h[1] for h in hashes}
    assert len(all_g) == 1, f"Genome hashes vary: {all_g}"
    assert len(all_K) == 1, f"Graph hashes vary: {all_K}"
