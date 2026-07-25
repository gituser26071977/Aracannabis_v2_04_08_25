"""
Sprint 4.4 — conftest compartilhado.

Fornece fixtures determinísticas para o teste suite do
Clinical Knowledge Engine v1.0.

Invariantes:
- Tenants e pacientes fixos (sem geração aleatória).
- Timestamps fixos em UTC (timezone-aware).
- Genes reconstruídos via ReplayEngine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest

from araos.clinical.genome.domain.aggregate import ClinicalGene, create_gene
from araos.clinical.genome.domain.aggregate.evidence import EvidenceReference
from araos.clinical.genome.domain.expression import (
    ClinicalExpression,
    Confidence,
    ExpressionState,
    ObservedValue,
    Trend,
    Volatility,
)
from araos.clinical.genome.domain.explainability import Explanation
from araos.clinical.timeline.domain.window import TimeWindow


UTC = timezone.utc
TENANT_A = "tenant_alfa"
TENANT_B = "tenant_beta"
PATIENT_A1 = "patient_a1"
PATIENT_A2 = "patient_a2"
PATIENT_B1 = "patient_b1"


def _make_explanation(exp_id: str = "exp_test") -> Explanation:
    return Explanation(
        explanation_id=exp_id,
        analysis_type="clinical",
        question="q_test",
        answer="a_test",
        confidence=1.0,
        method="test_method",
        data_window_start=None,
        data_window_end=None,
        variables=(),
        contributing_event_ids=(),
        assumptions=(),
        limitations=(),
    )


def _make_expression(
    gene_id: str,
    patient_id: str,
    tenant_id: str,
    value: float,
    confidence: float,
    sequence: int,
    days_offset: int,
    event_id_prefix: str,
) -> ClinicalExpression:
    """Helper — cria ClinicalExpression com timestamps fixos."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    vt = base + timedelta(days=days_offset)
    return ClinicalExpression(
        gene_id=gene_id,
        tenant_id=tenant_id,
        patient_id=patient_id,
        observed_value=ObservedValue(data=value, unit="score"),
        confidence=Confidence(value=confidence),
        trend=Trend.STABLE,
        volatility=Volatility.LOW,
        last_update=vt,
        valid_time=vt,
        transaction_time=vt,
        explanation_reference=f"{event_id_prefix}_expl",
        evidence_references=(
            EvidenceReference(
                event_id=f"{event_id_prefix}_ev_{sequence}",
                event_type="ASSESSMENT_APPLIED",
                observed_at=vt,
                contributing_weight=1.0,
            ),
        ),
        context_references=(),
        state=ExpressionState.CANONICAL,
        sequence=sequence,
    )


@dataclass(frozen=True)
class PatientScenario:
    """Cenário sintético de paciente."""

    tenant_id: str
    patient_id: str
    genes: tuple[ClinicalGene, ...]
    window: TimeWindow


def _build_gene_with_trajectory(
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    values: Sequence[tuple[float, float, int]],
) -> ClinicalGene:
    """Reconstrói ClinicalGene aplicando expressão por sequência."""
    expl = _make_explanation(f"exp_{gene_id}")
    gene = create_gene(
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        version="1.0.0",
    )
    for idx, (value, conf, days) in enumerate(values):
        expr = _make_expression(
            gene_id=gene_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            value=value,
            confidence=conf,
            sequence=idx,
            days_offset=days,
            event_id_prefix=f"ev_{gene_id}",
        )
        gene = gene.replace_expression(
            new_expression=expr,
            event_id=f"ev_{gene_id}_{idx}",
            event_type="EXPRESSION_OBSERVED",
            explanation=expl,
        )
    return gene


def _gene_genome_a1() -> tuple[ClinicalGene, ...]:
    """Paciente paciente_a1 com 2 Genes (sleep, anxiety) — perfil TEA + sono."""
    sleep_gene = _build_gene_with_trajectory(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A1,
        gene_id="GENE_SLEEP",
        values=(
            (3.0, 0.3, 0),
            (4.5, 0.5, 30),
            (6.0, 0.7, 60),
            (7.5, 0.85, 90),
        ),
    )
    anxiety_gene = _build_gene_with_trajectory(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A1,
        gene_id="GENE_ANXIETY",
        values=(
            (8.0, 0.9, 0),
            (6.5, 0.75, 30),
            (5.0, 0.5, 60),
            (3.5, 0.3, 90),
        ),
    )
    return (sleep_gene, anxiety_gene)


def _gene_genome_b1() -> tuple[ClinicalGene, ...]:
    """Paciente paciente_b1 com Gene válido (testa correlações 1-gene)."""
    return (
        _build_gene_with_trajectory(
            tenant_id=TENANT_B,
            patient_id=PATIENT_B1,
            gene_id="GENE_B1_SLEEP",
            values=(
                (4.0, 0.4, 0),
                (5.5, 0.6, 30),
                (7.0, 0.8, 60),
            ),
        ),
    )


def _window() -> TimeWindow:
    return TimeWindow(
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 6, 1, tzinfo=UTC),
        label="6_months",
    )


@pytest.fixture
def tenant_a() -> str:
    return TENANT_A


@pytest.fixture
def tenant_b() -> str:
    return TENANT_B


@pytest.fixture
def patient_a1() -> str:
    return PATIENT_A1


@pytest.fixture
def patient_a2() -> str:
    return PATIENT_A2


@pytest.fixture
def patient_b1() -> str:
    return PATIENT_B1


@pytest.fixture
def window() -> TimeWindow:
    return _window()


@pytest.fixture
def scenario_alfa() -> PatientScenario:
    """Cenário alfa: paciente com 2 Genes correlacionados."""
    return PatientScenario(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A1,
        genes=_gene_genome_a1(),
        window=_window(),
    )


@pytest.fixture
def scenario_beta() -> PatientScenario:
    """Cenário beta: paciente com 1 Gene."""
    return PatientScenario(
        tenant_id=TENANT_B,
        patient_id=PATIENT_B1,
        genes=_gene_genome_b1(),
        window=_window(),
    )


@pytest.fixture
def make_expression():
    """Helper exposto para criar expressions em testes."""
    return _make_expression


@pytest.fixture
def make_explanation_fixture():
    """Helper exposto para criar Explanation em testes."""
    return _make_explanation
