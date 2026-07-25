"""
Conformance Suite — Sprint 4.3 Phase 2.

Cada teste mapeia para um SHALL/INVARIANT específico de AS-001 ou AS-002.
A estrutura é::

    TEST_AS001_REQ_<NNNN> — descrição curta

e mantém correspondência 1:1 com o Requirement ID ``AS-XXX-REQ-NNNN``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import MappingProxyType

import pytest

from araos.clinical.genome.domain.aggregate import (
    ClinicalGene,
    ContextDependency,
    EvidenceReference,
    GeneStatus,
    History,
    Hypothesis,
    MetadataRecord,
    Relationship,
    Snapshot,
    SnapshotPolicy,
    Trajectory,
    TrajectoryPoint,
    build_urn,
    create_gene,
)
from araos.clinical.genome.domain.expression import (
    ClinicalExpression,
    Confidence,
    ExpressionState,
    ObservedValue,
    Trend,
    Volatility,
)
from araos.clinical.genome.domain.explainability import Explanation


UTC = timezone.utc


# ============================================================================
# Test Builders — para evitar duplicação
# ============================================================================


def make_expression(
    *,
    tenant_id: str = "t1",
    patient_id: str = "p1",
    gene_id: str = "GENE_SLEEP",
    value: float | str | None = 7.5,
    confidence: float = 0.8,
    trend: Trend = Trend.STABLE,
    volatility: Volatility = Volatility.LOW,
    state: ExpressionState = ExpressionState.CANONICAL,
    valid_time: datetime | None = None,
    transaction_time: datetime | None = None,
    sequence: int = 0,
    unit: str = "hours",
    qualifier: str = "",
    explanation_ref: str = "exp_001",
    evidence_count: int = 1,
) -> ClinicalExpression:
    if valid_time is None:
        valid_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    if transaction_time is None:
        transaction_time = valid_time + timedelta(seconds=1)

    evidence = tuple(
        EvidenceReference(
            event_id=f"ev_{i}",
            event_type="ASSESSMENT_APPLIED",
            observed_at=valid_time - timedelta(days=i + 1),
            contributing_weight=1.0 / evidence_count,
        )
        for i in range(evidence_count)
    )
    return ClinicalExpression(
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        observed_value=ObservedValue(data=value, unit=unit, qualifier=qualifier),
        confidence=Confidence(value=confidence),
        trend=trend,
        volatility=volatility,
        last_update=transaction_time,
        valid_time=valid_time,
        transaction_time=transaction_time,
        explanation_reference=explanation_ref,
        evidence_references=evidence,
        context_references=(),
        state=state,
        sequence=sequence,
    )


def make_explanation(
    explanation_id: str = "exp_001",
    confidence: float = 0.9,
) -> Explanation:
    return Explanation(
        explanation_id=explanation_id,
        analysis_type="expression_observation",
        question="Por que este valor?",
        answer="Avaliação clínica registrada em formulário padronizado.",
        confidence=confidence,
        method="clinical_assessment",
        data_window_start=None,
        data_window_end=None,
        variables=(),
        contributing_event_ids=("ev_1",),
        assumptions=(),
        limitations=(),
    )


# ============================================================================
# AS-001 — Requisito 5.1.1 — Identidade canônica
# ============================================================================


def REDACTED():
    """AS-001 §5.1.1 — Gene SHALL ter identidade (tenant_id, patient_id, gene_id)."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    assert gene.id == ("t1", "p1", "GENE_X")


def test_as001_req_0002_urn_format():
    """AS-001 §5.1.2 — URN SHALL seguir formato urn:araos:gene:{tenant}:{patient}:{gene}."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    assert gene.urn == "urn:araos:gene:t1:p1:GENE_X"
    assert build_urn("t1", "p1", "GENE_X") == "urn:araos:gene:t1:p1:GENE_X"


# ============================================================================
# AS-001 — Requisito 5.1.3 — Multi-tenancy estrito
# ============================================================================


def REDACTED():
    """AS-001 §5.1.3 — Expression SHALL ter mesmo tenant_id/patient_id do Gene."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    expr_wrong_tenant = make_expression(tenant_id="t2", patient_id="p1", gene_id="GENE_X")
    with pytest.raises(ValueError, match="tenant_id"):
        gene.replace_expression(
            expr_wrong_tenant,
            event_id="ev_1",
            event_type="EXPRESSION_OBSERVED",
            explanation=make_explanation(),
        )


# ============================================================================
# AS-001 — Requisito 6.2 — Trajectory append-only ordenada
# ============================================================================


def REDACTED():
    """AS-001 §6.2.1 — Trajectory SHALL ser append-only."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    expr1 = make_expression(gene_id="GENE_X", valid_time=datetime(2026, 1, 1, tzinfo=UTC), sequence=0)
    expr2 = make_expression(gene_id="GENE_X", valid_time=datetime(2026, 2, 1, tzinfo=UTC), sequence=1)
    gene = gene.replace_expression(expr1, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=make_explanation())
    gene = gene.replace_expression(expr2, event_id="ev_2", event_type="EXPRESSION_REPLACED", explanation=make_explanation("exp_2"))
    assert len(gene.trajectory) == 2


def REDACTED():
    """AS-001 §6.2.2 — Trajectory SHALL ser ordenada por valid_time ascendente."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    e1 = make_expression(gene_id="GENE_X", valid_time=datetime(2026, 1, 1, tzinfo=UTC), sequence=0)
    e2 = make_expression(gene_id="GENE_X", valid_time=datetime(2026, 2, 1, tzinfo=UTC), sequence=1)
    e3 = make_expression(gene_id="GENE_X", valid_time=datetime(2026, 3, 1, tzinfo=UTC), sequence=2)
    for e in [e1, e2, e3]:
        gene = gene.replace_expression(
            e,
            event_id=f"ev_{e.sequence}",
            event_type="EXPRESSION_OBSERVED" if e.sequence == 0 else "EXPRESSION_REPLACED",
            explanation=make_explanation(f"exp_{e.sequence}"),
        )
    times = [p.valid_time for p in gene.trajectory]
    assert times == sorted(times)


def REDACTED():
    """AS-001 §6.2.3 — Inserção desordenada SHALL preservar ordem."""
    trajectory = Trajectory()
    p1 = TrajectoryPoint(expression=make_expression(gene_id="GENE_X", valid_time=datetime(2026, 3, 1, tzinfo=UTC), sequence=2), contributing_event_ids=("ev_3",))
    p2 = TrajectoryPoint(expression=make_expression(gene_id="GENE_X", valid_time=datetime(2026, 1, 1, tzinfo=UTC), sequence=0), contributing_event_ids=("ev_1",))
    p3 = TrajectoryPoint(expression=make_expression(gene_id="GENE_X", valid_time=datetime(2026, 2, 1, tzinfo=UTC), sequence=1), contributing_event_ids=("ev_2",))
    trajectory = trajectory.append(p1).append(p2).append(p3)
    times = [p.valid_time for p in trajectory]
    assert times == [datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC), datetime(2026, 3, 1, tzinfo=UTC)]


# ============================================================================
# AS-001 — Requisito 6.3 — History audit chain
# ============================================================================


def REDACTED():
    """AS-001 §6.3.1 — History SHALL ser append-only."""
    history = History()
    e1 = HistoryEntry_from_event("ev_1", 0, "EXPRESSION_OBSERVED", "system")
    e2 = HistoryEntry_from_event("ev_2", 1, "EXPRESSION_REPLACED", "system")
    history = history.append(e1).append(e2)
    assert len(history) == 2


def REDACTED():
    """AS-001 §6.3.2 — Sequence SHALL ser monotônico."""
    e1 = HistoryEntry_from_event("ev_1", 0, "EXPRESSION_OBSERVED", "system")
    e2 = HistoryEntry_from_event("ev_2", 1, "EXPRESSION_REPLACED", "system")
    history = History((e1, e2))
    with pytest.raises(ValueError):
        History((e2, e1))  # ordem inversa deve falhar


def REDACTED():
    """AS-001 §6.3.3 — Toda mutação SHALL produzir ≥ 1 entrada em History."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    expr1 = make_expression(gene_id="GENE_X", sequence=0)
    expr2 = make_expression(gene_id="GENE_X", sequence=1)
    gene = gene.replace_expression(expr1, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=make_explanation())
    gene = gene.replace_expression(expr2, event_id="ev_2", event_type="EXPRESSION_REPLACED", explanation=make_explanation("exp_2"))
    assert len(gene.history) >= 2


def HistoryEntry_from_event(event_id, sequence, event_type, origin):
    from araos.clinical.genome.domain.aggregate import HistoryEntry
    now = datetime.now(UTC)
    return HistoryEntry(
        event_id=event_id,
        sequence=sequence,
        event_type=event_type,
        occurred_at=now,
        recorded_at=now,
        payload_summary=f"{event_type} test",
        origin=origin,
    )


# ============================================================================
# AS-001 — Requisito 6.5 — Evidence preservation
# ============================================================================


def REDACTED():
    """AS-001 §6.5 — Evidence SHALL ser preservada na Trajectory."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    expr1 = make_expression(gene_id="GENE_X", sequence=0, evidence_count=2)
    expr2 = make_expression(gene_id="GENE_X", value=8.0, sequence=1, evidence_count=1)
    gene = gene.replace_expression(expr1, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=make_explanation())
    gene = gene.replace_expression(expr2, event_id="ev_2", event_type="EXPRESSION_REPLACED", explanation=make_explanation("exp_2"))
    assert len(gene.trajectory) == 2
    points = list(gene.trajectory)
    assert len(points[0].expression.evidence_references) == 2
    assert len(points[1].expression.evidence_references) == 1


# ============================================================================
# AS-001 — Requisito 6.6 — Hypotheses
# ============================================================================


def REDACTED():
    """AS-001 §6.6 — Hipóteses SHALL ser registradas."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    hyp = Hypothesis(
        hypothesis_id="hyp_1",
        description="CBD pode reduzir ansiedade",
        weight=0.7,
        supporting_event_ids=("ev_1",),
        confidence=0.65,
        is_active=True,
    )
    gene = gene.add_hypothesis(hyp, event_id="ev_hyp_1")
    assert len(gene.hypotheses) == 1
    assert gene.hypotheses[0].hypothesis_id == "hyp_1"


def REDACTED():
    """AS-001 §6.6 — Desativação SHALL criar nova entrada em History."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    hyp = Hypothesis(
        hypothesis_id="hyp_1", description="X", weight=0.5,
        supporting_event_ids=(), confidence=0.5, is_active=True,
    )
    gene = gene.add_hypothesis(hyp, event_id="ev_hyp_1")
    history_before = len(gene.history)
    gene = gene.deactivate_hypothesis("hyp_1", event_id="ev_hyp_2")
    assert gene.hypotheses[0].is_active is False
    assert len(gene.history) > history_before


# ============================================================================
# AS-001 — Requisito 6.7 — Relationships canônicos
# ============================================================================


def REDACTED():
    """AS-001 §6.7 — Relationship SHALL ter tipo canônico."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    rel = Relationship(
        target_gene_id="GENE_Y",
        relationship_type="influences",
        confidence=0.7,
        evidence_event_ids=("ev_1",),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    gene = gene.add_relationship(rel, event_id="ev_rel_1")
    assert gene.relationships[0].relationship_type == "influences"


def REDACTED():
    """AS-001 §6.7 — Tipos não-canônicos SHALL ser rejeitados."""
    with pytest.raises(ValueError):
        Relationship(
            target_gene_id="GENE_Y",
            relationship_type="maybe_relates_to",
            confidence=0.7,
            evidence_event_ids=("ev_1",),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )


# ============================================================================
# AS-001 — Requisito 6.8 — Context references
# ============================================================================


def test_as001_req_0073_context_added():
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    ctx = ContextDependency(
        context_id="ctx_1",
        context_type="medication",
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        effective_until=None,
        weight=1.0,
    )
    gene = gene.add_context(ctx, event_id="ev_ctx_1")
    assert ctx in gene.context


def REDACTED():
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    ctx = ContextDependency(
        context_id="ctx_1",
        context_type="medication",
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        effective_until=None,
        weight=1.0,
    )
    gene = gene.add_context(ctx, event_id="ev_ctx_1")
    gene = gene.remove_context("ctx_1", event_id="ev_ctx_2")
    assert ctx not in gene.context


def REDACTED():
    ctx = ContextDependency(
        context_id="ctx_1",
        context_type="medication",
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        effective_until=datetime(2026, 12, 31, tzinfo=UTC),
        weight=1.0,
    )
    assert ctx.is_active_at(datetime(2026, 6, 1, tzinfo=UTC)) is True
    assert ctx.is_active_at(datetime(2027, 1, 1, tzinfo=UTC)) is False
    assert ctx.is_active_at(datetime(2025, 12, 31, tzinfo=UTC)) is False


# ============================================================================
# AS-001 — Requisito 6.9 — Metadata não-canônica
# ============================================================================


def REDACTED():
    """AS-001 §6.9 — Metadata SHALL ser tratada como imutável."""
    rec = MetadataRecord(
        record_id="meta_1",
        content={"kind": "test"},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert isinstance(rec.content, MappingProxyType)
    with pytest.raises(TypeError):
        rec.content["x"] = 1


# ============================================================================
# AS-001 — Requisito 6.4 — Snapshots
# ============================================================================


def REDACTED():
    """AS-001 §6.4 — Snapshot SHALL ter state_hash."""
    snap = Snapshot(
        snapshot_id="snap_1",
        gene_id="GENE_X",
        sequence=10,
        valid_time=datetime(2026, 1, 1, tzinfo=UTC),
        transaction_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        state={"x": 1},
        state_hash="a" * 64,
    )
    assert len(snap.state_hash) == 64  # SHA-256 hex


def REDACTED():
    """AS-001 §6.4 — Snapshot SHALL ter valid_time > transaction_time."""
    with pytest.raises(ValueError):
        Snapshot(
            snapshot_id="snap_1",
            gene_id="GENE_X",
            sequence=10,
            valid_time=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
            transaction_time=datetime(2026, 1, 1, tzinfo=UTC),
            state={},
            state_hash="a" * 64,
        )


# ============================================================================
# AS-001 — Requisito 6.4 — Status ARCHIVED terminal
# ============================================================================


def REDACTED():
    """AS-001 §6.4 — Gene ARCHIVED SHALL rejeitar mutações."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    gene = gene.archive(event_id="ev_arch", reason="superseded")
    expr = make_expression(gene_id="GENE_X")
    with pytest.raises(ValueError, match="arquivado"):
        gene.replace_expression(expr, event_id="ev_1", event_type="EXPRESSION_REPLACED", explanation=make_explanation())


def REDACTED():
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    gene = gene.archive(event_id="ev_arch_1", reason="x")
    history_before = len(gene.history)
    gene2 = gene.archive(event_id="ev_arch_2", reason="x")
    assert len(gene2.history) == history_before


# ============================================================================
# AS-001 — Requisito 8 — Versionamento SemVer
# ============================================================================


def test_as001_req_0081_semver_format():
    """AS-001 §8 — Version SHALL seguir SemVer X.Y.Z."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="2.5.3")
    assert gene.version == "2.5.3"
    parts = gene.version.split(".")
    assert len(parts) == 3
    for p in parts:
        assert p.isdigit()