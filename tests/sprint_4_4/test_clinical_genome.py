"""
Sprint 4.4 — ClinicalGenome Projection.

Testes cobrindo:
    - Build from genes (purity).
    - Build from events (replay determinístico).
    - state_hash determinístico across runs.
    - Canonical dict NÃO inclui built_at (replay invariant).
    - GenomeState enum derivado.
    - accession methods (gene, gene_ids, all_event_ids).
    - Invariantes (tenant mix, missing genes).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from araos.clinical.knowledge.domain.clinical_genome import (
    ClinicalGenomeBuilder,
    GenomeState,
    build_clinical_genome,
)


UTC = timezone.utc


class TestClinicalGenomeBuild:
    """Construção e identidade do ClinicalGenome."""

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        assert genome.genome_id
        assert genome.tenant_id == scenario_alfa.tenant_id
        assert genome.patient_id == scenario_alfa.patient_id
        assert len(genome.genes) == 2
        assert genome.state_hash
        assert len(genome.state_hash) == 64  # SHA-256 hex

    def test_genome_is_frozen_dataclass(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert — frozen: mutation raises
        with pytest.raises((AttributeError, Exception)):
            genome.tenant_id = "x"

    def REDACTED(self, scenario_alfa, window):
        # Act / Assert
        with pytest.raises(ValueError, match="ao menos 1"):
            build_clinical_genome(
                tenant_id=scenario_alfa.tenant_id,
                patient_id=scenario_alfa.patient_id,
                window=window,
                genes=(),
            )

    def REDACTED(self, scenario_alfa, scenario_beta):
        # Build mixed-tenant fixture
        mixed = scenario_alfa.genes + scenario_beta.genes
        # Act / Assert
        with pytest.raises(ValueError, match="tenant"):
            build_clinical_genome(
                tenant_id=scenario_alfa.tenant_id,
                patient_id=scenario_alfa.patient_id,
                window=scenario_alfa.window,
                genes=mixed,
            )


class TestClinicalGenomeReplay:
    """Replay determinístico + state_hash."""

    def REDACTED(self, scenario_alfa):
        # Act
        h1 = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        ).state_hash
        h2 = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        ).state_hash
        h3 = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        ).state_hash
        # Assert
        assert h1 == h2 == h3

    def REDACTED(self, scenario_alfa, scenario_beta):
        # Act
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
        # Assert
        assert g_a.state_hash != g_b.state_hash

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        d = genome.to_canonical_dict()
        # Assert — built_at NOT in canonical dict (replay invariant)
        assert "built_at" not in d
        assert "genome_id" not in d  # genome_id is ephemeral

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        d = genome.to_canonical_dict()
        # Assert
        assert d["type"] == "ClinicalGenome"
        assert d["tenant_id"] == scenario_alfa.tenant_id
        assert d["patient_id"] == scenario_alfa.patient_id
        assert isinstance(d["genes"], list)
        assert len(d["genes"]) == 2
        assert all("gene_id" in g for g in d["genes"])

    def REDACTED(self, scenario_alfa):
        # Act — compute hash twice on same genome
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        h1 = genome.compute_state_hash()
        h2 = genome.compute_state_hash()
        # Assert
        assert h1 == h2


class TestClinicalGenomeState:
    """Estado agregado (GenomeState) derivado dos Genes."""

    def REDACTED(self, scenario_alfa):
        # Act — all canonical → COMPLETE
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        assert genome.current_state() == GenomeState.COMPLETE

    def test_gene_lookup_by_id(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        assert genome.gene("GENE_SLEEP") is not None
        assert genome.gene("GENE_ANXIETY") is not None
        assert genome.gene("GENE_MISSING") is None

    def test_gene_ids_returns_tuple(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        ids = genome.gene_ids()
        assert isinstance(ids, tuple)
        assert set(ids) == {"GENE_SLEEP", "GENE_ANXIETY"}

    def test_all_event_ids_audit_chain(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        events = genome.all_event_ids()
        # 2 genes × 4 expression events each = 8 unique event_ids
        assert len(events) == 8
        assert all(e.startswith("ev_") for e in events)


class TestClinicalGenomeUrn:
    """URN canônico."""

    def test_urn_format(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        assert genome.urn.startswith("urn:araos:genome:")
        assert scenario_alfa.tenant_id in genome.urn
        assert scenario_alfa.patient_id in genome.urn


class TestClinicalGenomeBuilder:
    """ClinicalGenomeBuilder (factory)."""

    def REDACTED(self, scenario_alfa):
        # Act
        from araos.clinical.genome.application import ReplayEngine
        builder = ClinicalGenomeBuilder(replay_engine=ReplayEngine())
        genome = builder.build_from_genes(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Assert
        assert genome.state_hash
