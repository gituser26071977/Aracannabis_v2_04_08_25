"""
Smoke test — validação ponta-a-ponta dos módulos.

Reference Implementation — Sprint 4.3 Phase 2.

Verifica que todos os módulos importam corretamente.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


def test_aggregate_imports():
    from araos.clinical.genome.domain.aggregate import (
        ClinicalGene,
        ContextDependency,
        EvidenceReference,
        History,
        HistoryEntry,
        Hypothesis,
        MetadataRecord,
        Relationship,
        Snapshot,
        SnapshotPolicy,
        Trajectory,
        TrajectoryPoint,
        create_gene,
    )
    assert ClinicalGene is not None
    assert create_gene is not None


def test_expression_imports():
    from araos.clinical.genome.domain.expression import (
        ClinicalExpression,
        Confidence,
        ExpressionState,
        ObservedValue,
        Trend,
        Volatility,
    )
    assert ClinicalExpression is not None


def test_events_imports():
    from araos.clinical.genome.domain.events import (
        DomainEvent,
        GENE_CREATED,
        make_gene_created,
        make_expression_observed,
    )
    assert DomainEvent is not None


def test_explainability_imports():
    from araos.clinical.genome.domain.explainability import Explanation
    from araos.clinical.genome.domain.expression import ExplanationSummary
    assert Explanation is not None
    assert ExplanationSummary is not None


def test_replay_engine_imports():
    from araos.clinical.genome.application import ReplayEngine
    assert ReplayEngine is not None


def test_serialization_imports():
    from araos.clinical.genome.infrastructure import (
        compute_state_hash,
        gene_to_canonical_json,
        gene_from_canonical_json,
        event_to_canonical_json,
    )
    assert compute_state_hash is not None


def test_create_gene_basic():
    from araos.clinical.genome.domain.aggregate import create_gene, GeneStatus
    gene = create_gene(
        tenant_id="t1",
        patient_id="p1",
        gene_id="GENE_SLEEP",
        version="1.0.0",
    )
    assert gene.tenant_id == "t1"
    assert gene.patient_id == "p1"
    assert gene.gene_id == "GENE_SLEEP"
    assert gene.status == GeneStatus.ACTIVE
    assert gene.urn == "urn:araos:gene:t1:p1:GENE_SLEEP"
    assert gene.current_expression is None