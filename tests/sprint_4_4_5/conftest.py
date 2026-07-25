"""
Sprint 4.4.5 — conftest compartilhado.

Reusa fixtures do Sprint 4.4 e adiciona fixtures
determinísticas adicionais para:
- Replay hardening (N runs consecutivos)
- Multi-tenancy stress (10 tenants)
- Concurrency (workers)
- Property-based (Hypothesis strategies)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Permitir imports do conftest do Sprint 4.4 sem duplicar fixtures.
_HERE = Path(__file__).resolve().parent
_44 = _HERE.parent / "sprint_4_4"
if str(_44) not in sys.path:
    sys.path.insert(0, str(_44))

from tests.sprint_4_4.conftest import (  # noqa: E402,F401
    TENANT_A,
    TENANT_B,
    PATIENT_A1,
    PATIENT_A2,
    PATIENT_B1,
    PatientScenario,
    _build_gene_with_trajectory,
    _gene_genome_a1,
    _gene_genome_b1,
    _make_explanation,
    _make_expression,
    _window,
    scenario_alfa,
    scenario_beta,
    window,
    make_expression,
    make_explanation_fixture,
    tenant_a,
    tenant_b,
    patient_a1,
    patient_b1,
)

from datetime import datetime, timedelta, timezone  # noqa: E402

import pytest  # noqa: E402

from araos.clinical.knowledge.domain.clinical_genome import (  # noqa: E402
    ClinicalGenomeBuilder,
)
from araos.clinical.timeline.domain.window import TimeWindow  # noqa: E402


UTC = timezone.utc


# ────────────────────────────────────────────────────────────────────
# Additional fixtures for hardening
# ────────────────────────────────────────────────────────────────────


def _multi_tenant_window(start_year: int = 2026, months: int = 6) -> TimeWindow:
    return TimeWindow(
        start=datetime(start_year, 1, 1, tzinfo=UTC),
        end=datetime(start_year, 1 + months, 1, tzinfo=UTC),
        label=f"{months}_months",
    )


@pytest.fixture
def multi_tenant_window() -> TimeWindow:
    return _multi_tenant_window()


@pytest.fixture
def longer_window() -> TimeWindow:
    return TimeWindow(
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 12, 31, tzinfo=UTC),
        label="12_months",
    )


@pytest.fixture
def shorter_window() -> TimeWindow:
    return TimeWindow(
        start=datetime(2026, 3, 1, tzinfo=UTC),
        end=datetime(2026, 6, 1, tzinfo=UTC),
        label="3_months",
    )


@pytest.fixture
def scenario_a1_2genes():
    """Cenário com 2 Genes do tenant A paciente 1."""
    return PatientScenario(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A1,
        genes=_gene_genome_a1(),
        window=_window(),
    )


@pytest.fixture
def scenario_a2_2genes():
    """Cenário com 2 Genes do tenant A paciente 2."""
    sleep = _build_gene_with_trajectory(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A2,
        gene_id="GENE_SLEEP",
        values=((4.0, 0.4, 0), (5.0, 0.6, 30), (6.5, 0.75, 60)),
    )
    anxiety = _build_gene_with_trajectory(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A2,
        gene_id="GENE_ANXIETY",
        values=((7.0, 0.7, 0), (5.5, 0.55, 30), (4.0, 0.4, 60)),
    )
    return PatientScenario(
        tenant_id=TENANT_A,
        patient_id=PATIENT_A2,
        genes=(sleep, anxiety),
        window=_window(),
    )


@pytest.fixture
def genome_builder() -> ClinicalGenomeBuilder:
    return ClinicalGenomeBuilder()
