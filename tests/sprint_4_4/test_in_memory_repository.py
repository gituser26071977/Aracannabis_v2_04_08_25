"""
Sprint 4.4 — InMemoryKnowledgeRepository.

Testes cobrindo:
    - save/load genes.
    - save/load genome.
    - list_patient_ids.
    - list_genomes.
    - clear.
    - Thread-safety (lock básico).

Sprint 4.5 G3: InMemoryKnowledgeRepository agora aceita tenant_id
explicitamente. Tests passam tenant_id="tenant_alfa" para casar
com o scenario_alfa fixture.
"""

from __future__ import annotations

import threading

import pytest

from araos.clinical.knowledge.infrastructure import InMemoryKnowledgeRepository

_TENANT = "tenant_alfa"


def _build_genome_dummy(scenario_alfa):
    """Helper para criar genome a partir do scenario_alfa."""
    from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
    return build_clinical_genome(
        tenant_id=scenario_alfa.tenant_id,
        patient_id=scenario_alfa.patient_id,
        window=scenario_alfa.window,
        genes=scenario_alfa.genes,
    )


class TestRepositoryGenes:
    """save/load Genes."""

    def test_save_and_load_genes(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        # Assert
        loaded = repo.load_genes(scenario_alfa.patient_id)
        assert len(loaded) == len(scenario_alfa.genes)
        assert loaded[0].gene_id == scenario_alfa.genes[0].gene_id

    def REDACTED(self):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        loaded = repo.load_genes("missing_patient")
        # Assert
        assert loaded == ()

    def test_list_patient_ids_sorted(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        repo.save_genes("z_patient", ())
        repo.save_genes("a_patient", ())
        repo.save_genes("m_patient", ())
        # Assert
        ids = repo.list_patient_ids()
        assert ids == ("a_patient", "m_patient", "z_patient")


class TestRepositoryGenomes:
    """save/load Genome."""

    def test_save_and_load_genome(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        genome = _build_genome_dummy(scenario_alfa)
        repo.save_genome(genome)
        loaded = repo.load_genome(genome.genome_id)
        # Assert
        assert loaded is not None
        assert loaded.state_hash == genome.state_hash

    def test_load_genome_missing(self):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        loaded = repo.load_genome("nope")
        # Assert
        assert loaded is None

    def test_list_genomes(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        genome = _build_genome_dummy(scenario_alfa)
        repo.save_genome(genome)
        # Assert
        assert len(repo.list_genomes()) == 1


class TestRepositoryClear:
    """clear()."""

    def test_clear_removes_all(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        genome = _build_genome_dummy(scenario_alfa)
        repo.save_genome(genome)
        repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        repo.clear()
        # Assert
        assert len(repo.list_genomes()) == 0
        assert len(repo.load_genes(scenario_alfa.patient_id)) == 0


class TestRepositoryLen:
    """__len__."""

    def test_len_counts_total(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        genome = _build_genome_dummy(scenario_alfa)
        repo.save_genome(genome)
        repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        # Assert
        total = len(repo)
        assert total >= 2  # 1 genome + 1 patient entry


class TestRepositoryThreadSafety:
    """Lock é usado."""

    def test_concurrent_save_no_corruption(self, scenario_alfa):
        # Act
        repo = InMemoryKnowledgeRepository(tenant_id=_TENANT)
        errors: list[Exception] = []

        def save_some():
            try:
                for i in range(50):
                    repo.save_genes(f"patient_{threading.current_thread().name}_{i}", ())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=save_some, name=f"t{i}") for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Assert
        assert len(errors) == 0
        # 3 threads × 50 saves each = 150 patient entries
        assert len(repo.list_patient_ids()) == 150
