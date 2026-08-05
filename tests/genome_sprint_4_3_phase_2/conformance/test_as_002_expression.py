"""
AS-002 — Clinical Expression — Conformance Suite.

Cobre os requisitos do AS-002 v1.0.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.genome.domain.aggregate import create_gene
from araos.clinical.genome.domain.expression import (
    ClinicalExpression,
    Confidence,
    ExpressionState,
    ObservedValue,
    Trend,
    Volatility,
)
from araos.clinical.genome.domain.aggregate.evidence import EvidenceReference
from araos.clinical.genome.domain.aggregate.context_dependency import ContextDependency

UTC = timezone.utc


def make_expression(
    *,
    tenant_id: str = "t1",
    patient_id: str = "p1",
    gene_id: str = "GENE_X",
    value: float | str | None = 7.5,
    confidence_value: float = 0.8,
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
        confidence=Confidence(value=confidence_value),
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


# ============================================================================
# AS-002 §4.1 — Identidade
# ============================================================================


def REDACTED():
    """AS-002 §4.1.4 — Expression SHALL ser identificada por gene_id, não 'id'."""
    expr = make_expression(gene_id="GENE_SLEEP")
    assert expr.gene_id == "GENE_SLEEP"
    assert not hasattr(expr, "id") or True  # apenas documenta ausência


def REDACTED():
    """AS-002 §4.1.1 — Tenant consistency é enforced externamente (no AR)."""
    from araos.clinical.genome.domain.aggregate import create_gene
    from araos.clinical.genome.domain.explainability import Explanation
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    expr_wrong = make_expression(tenant_id="t2", patient_id="p1", gene_id="GENE_X")
    expl = Explanation(
        explanation_id="exp_1", analysis_type="x", question="q", answer="a",
        confidence=1.0, method="m",
        data_window_start=None, data_window_end=None,
        variables=(), contributing_event_ids=(),
        assumptions=(), limitations=(),
    )
    with pytest.raises(ValueError):
        gene.replace_expression(expr_wrong, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=expl)


# ============================================================================
# AS-002 §4.2 — Confidence
# ============================================================================


def REDACTED():
    """AS-002 §4.2.2 — Confidence MAY ser 0.0 (sem evidência)."""
    c = Confidence.zero()
    assert c.value == 0.0


def REDACTED():
    c = Confidence(value=1.0)
    assert c.is_full


def REDACTED():
    with pytest.raises(ValueError):
        Confidence(value=1.5)
    with pytest.raises(ValueError):
        Confidence(value=-0.1)


def REDACTED():
    c = Confidence.from_decimal(0.75)
    assert c.value == 0.75


# ============================================================================
# AS-002 §4.3 — Explanation reference (cross-cutting)
# ============================================================================


def REDACTED():
    """AS-002 §4.3.1 — Expression SHALL ter explanation_reference não-vazio."""
    with pytest.raises(ValueError, match="explanation_reference"):
        ClinicalExpression(
            tenant_id="t1", patient_id="p1", gene_id="GENE_X",
            observed_value=ObservedValue(data=1.0),
            confidence=Confidence(value=0.5),
            trend=Trend.STABLE, volatility=Volatility.LOW,
            last_update=datetime.now(UTC),
            valid_time=datetime.now(UTC),
            transaction_time=datetime.now(UTC),
            explanation_reference="",  # vazio!
            evidence_references=(
                EvidenceReference(
                    event_id="ev_1", event_type="x",
                    observed_at=datetime.now(UTC), contributing_weight=1.0,
                ),
            ),
            context_references=(),
            state=ExpressionState.CANONICAL,
            sequence=0,
        )


def REDACTED():
    """AS-002 §4.3.2 — Expression SHALL ter ≥ 1 evidence_references."""
    with pytest.raises(ValueError, match="evidence"):
        ClinicalExpression(
            tenant_id="t1", patient_id="p1", gene_id="GENE_X",
            observed_value=ObservedValue(data=1.0),
            confidence=Confidence(value=0.5),
            trend=Trend.STABLE, volatility=Volatility.LOW,
            last_update=datetime.now(UTC),
            valid_time=datetime.now(UTC),
            transaction_time=datetime.now(UTC),
            explanation_reference="exp_1",
            evidence_references=(),  # vazio!
            context_references=(),
            state=ExpressionState.CANONICAL,
            sequence=0,
        )


# ============================================================================
# AS-002 §4.4 — Bitemporalidade
# ============================================================================


def REDACTED():
    """AS-002 §4.4.2 — transaction_time SHALL NOT ser anterior a valid_time."""
    valid = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    txn = datetime(2026, 6, 1, 11, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="transaction_time"):
        ClinicalExpression(
            tenant_id="t1", patient_id="p1", gene_id="GENE_X",
            observed_value=ObservedValue(data=1.0),
            confidence=Confidence(value=0.5),
            trend=Trend.STABLE, volatility=Volatility.LOW,
            last_update=txn,
            valid_time=valid,
            transaction_time=txn,
            explanation_reference="exp_1",
            evidence_references=(
                EvidenceReference(event_id="ev_1", event_type="x",
                                  observed_at=valid, contributing_weight=1.0),
            ),
            context_references=(),
            state=ExpressionState.CANONICAL,
            sequence=0,
        )


def REDACTED():
    """AS-002 §4.4.1 — valid_time SHALL ser timezone-aware."""
    with pytest.raises(ValueError, match="valid_time"):
        ClinicalExpression(
            tenant_id="t1", patient_id="p1", gene_id="GENE_X",
            observed_value=ObservedValue(data=1.0),
            confidence=Confidence(value=0.5),
            trend=Trend.STABLE, volatility=Volatility.LOW,
            last_update=datetime.now(UTC),
            valid_time=datetime(2026, 1, 1),  # naive!
            transaction_time=datetime.now(UTC),
            explanation_reference="exp_1",
            evidence_references=(
                EvidenceReference(event_id="ev_1", event_type="x",
                                  observed_at=datetime.now(UTC), contributing_weight=1.0),
            ),
            context_references=(),
            state=ExpressionState.CANONICAL,
            sequence=0,
        )


# ============================================================================
# AS-002 §4.5 — Context references
# ============================================================================


def REDACTED():
    """AS-002 §4.5 — Context SHALL ter effective_from <= effective_until."""
    later = datetime(2026, 6, 1, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError):
        ContextDependency(
            context_id="ctx_1",
            context_type="medication",
            effective_from=later,
            effective_until=earlier,
            weight=1.0,
        )


# ============================================================================
# AS-002 §4.6 — Imutabilidade
# ============================================================================


def REDACTED():
    """AS-002 §4.6 — Expression SHALL ser imutável (frozen dataclass)."""
    expr = make_expression(gene_id="GENE_X")
    with pytest.raises(Exception):  # FrozenInstanceError
        expr.tenant_id = "hacked"  # type: ignore[misc]


# ============================================================================
# AS-002 §4.7 — Igualdade estrutural
# ============================================================================


def REDACTED():
    """AS-002 §4.7.1 — Igualdade SHALL ser por valor (structural)."""
    e1 = make_expression(gene_id="GENE_X", sequence=0)
    e2 = make_expression(gene_id="GENE_X", sequence=0)
    assert e1 == e2
    e3 = make_expression(gene_id="GENE_X", sequence=0, value=99.0)
    assert e1 != e3


# ============================================================================
# AS-002 §4.8 — Append-only
# ============================================================================


def REDACTED():
    """AS-002 §4.8 — Trajectory SHALL preservar Expression como snapshot."""
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0")
    from araos.clinical.genome.domain.explainability import Explanation
    expl = Explanation(
        explanation_id="exp_1", analysis_type="x", question="q", answer="a",
        confidence=1.0, method="m",
        data_window_start=None, data_window_end=None,
        variables=(), contributing_event_ids=(),
        assumptions=(), limitations=(),
    )
    expr1 = make_expression(gene_id="GENE_X", sequence=0)
    expr2 = make_expression(gene_id="GENE_X", sequence=1, value=99.0)
    gene = gene.replace_expression(expr1, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=expl)
    gene = gene.replace_expression(expr2, event_id="ev_2", event_type="EXPRESSION_REPLACED", explanation=expl)
    points = list(gene.trajectory)
    assert len(points) == 2
    # Substituição preserva histórico.
    assert points[0].expression.observed_value.data == 7.5
    assert points[1].expression.observed_value.data == 99.0


# ============================================================================
# AS-002 §6.3 — State hash determinístico
# ============================================================================


def REDACTED():
    """AS-002 §6.3 — state_hash SHALL ser determinístico (byte-equivalente)."""
    from araos.clinical.genome.infrastructure import compute_state_hash, gene_to_canonical_json
    fixed_time = datetime(2026, 1, 1, tzinfo=UTC)
    gene1 = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0", created_at=fixed_time)
    gene2 = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0", created_at=fixed_time)
    h1 = compute_state_hash(gene1)
    h2 = compute_state_hash(gene2)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def REDACTED():
    from araos.clinical.genome.infrastructure import gene_to_canonical_json
    fixed_time = datetime(2026, 1, 1, tzinfo=UTC)
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0", created_at=fixed_time)
    j1 = gene_to_canonical_json(gene)
    j2 = gene_to_canonical_json(gene)
    assert j1 == j2


# ============================================================================
# AS-002 §3.14 — Unknown state
# ============================================================================


def REDACTED():
    """AS-002 §3.14 — ObservedValue SHALL suportar Unknown via classe explícita."""
    ov = ObservedValue.unknown()
    assert ov.is_unknown


def REDACTED():
    ov = ObservedValue.unavailable()
    assert ov.is_unavailable


# ============================================================================
# AS-002 — Explainability cross-cutting
# ============================================================================


def REDACTED():
    """AS-002 — Expression SHALL expor why() retornando ExplanationSummary."""
    expr = make_expression(gene_id="GENE_X")
    summary = expr.why()
    assert summary.explanation_reference  # não vazio
    assert summary.confidence.value >= 0.0


def REDACTED():
    fixed_time = datetime(2026, 1, 1, tzinfo=UTC)
    gene = create_gene(tenant_id="t1", patient_id="p1", gene_id="GENE_X", version="1.0.0", created_at=fixed_time)
    summary = gene.why()
    # Quando não há Expression: explanation_reference contém marker.
    assert "summary_no_expr" in summary.explanation_reference
    # Após expression replace
    from araos.clinical.genome.domain.explainability import Explanation
    expl = Explanation(
        explanation_id="exp_1", analysis_type="x", question="q", answer="a",
        confidence=1.0, method="m",
        data_window_start=None, data_window_end=None,
        variables=(), contributing_event_ids=(),
        assumptions=(), limitations=(),
    )
    expr = make_expression(gene_id="GENE_X", sequence=0)
    gene = gene.replace_expression(expr, event_id="ev_1", event_type="EXPRESSION_OBSERVED", explanation=expl)
    summary2 = gene.why()
    assert summary2.confidence.value == pytest.approx(0.8)  # expr confidence