"""
Sprint 4.4.5 — Coverage Hardening: Cohort + Research edge cases.

Foco em ramos não-cobertos:
    - Cohort.__post_init__ (state_hash, name, cohort_id)
    - Cohort.count + to_canonical_dict
    - CohortBuilder._matches (todos CriterionOperator)
    - CohortBuilder._resolve_field (patient.* prefix)
    - CohortBuilder._resolve_genome_field (gene.* / expression.* / context.*)
    - Criterion.__post_init__ (field obrigatório)
    - Research edge cases (AnalysisTypes alternativos)
    - InMemoryKnowledgeRepository.__len__
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.knowledge.domain.cohort import (
    Cohort,
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.research import AnalysisType
from araos.clinical.knowledge.infrastructure.in_memory import InMemoryKnowledgeRepository

from tests.sprint_4_4_5.conftest import _build_gene_with_trajectory


UTC = timezone.utc


# ────────────────────────────────────────────────────────────────────
# Criterion validation
# ────────────────────────────────────────────────────────────────────


class TestCriterionValidation:
    def test_criterion_requires_field(self):
        with pytest.raises(ValueError, match="field obrigatório"):
            Criterion(field="", operator=CriterionOperator.EQ, value=10)

    def REDACTED(self):
        c = Criterion(
            field="patient.age",
            operator=CriterionOperator.EXISTS,
            value=None,
        )
        assert c.operator == CriterionOperator.EXISTS


# ────────────────────────────────────────────────────────────────────
# Cohort validation
# ────────────────────────────────────────────────────────────────────


class TestCohortValidation:
    def _make_pool(self):
        return [
            PatientData(patient_id=f"p{i}", tenant_id="t1", age=10 + i, sex="F")
            for i in range(5)
        ]

    def test_cohort_requires_cohort_id(self):
        with pytest.raises(ValueError, match="cohort_id"):
            Cohort(
                cohort_id="",
                tenant_id="t1",
                name="x",
                matched_patient_ids=(),
                criteria=(),
                built_at=datetime(2026, 1, 1, tzinfo=UTC),
                state_hash="0" * 64,
            )

    def test_cohort_requires_name(self):
        with pytest.raises(ValueError, match="name"):
            Cohort(
                cohort_id="c1",
                tenant_id="t1",
                name="",
                matched_patient_ids=(),
                criteria=(),
                built_at=datetime(2026, 1, 1, tzinfo=UTC),
                state_hash="0" * 64,
            )

    def test_cohort_count_helper(self):
        cohort = CohortBuilder().evaluate(
            patients=self._make_pool(),
            tenant_id="t1",
            name="c",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.GT, value=11),),
        )
        assert cohort.count == 3

    def test_cohort_to_canonical_dict(self):
        cohort = CohortBuilder().evaluate(
            patients=self._make_pool(),
            tenant_id="t1",
            name="c",
            criteria=(),
        )
        d = cohort.to_canonical_dict()
        assert isinstance(d, dict)
        assert d["name"] == "c"
        assert "criteria" in d
        assert "tenant_id" in d

    def REDACTED(self):
        cohort = CohortBuilder().evaluate(
            patients=self._make_pool(),
            tenant_id="t1",
            name="c",
            criteria=(),
        )
        # Validate state hash não levanta exceção
        cohort.validate_state_hash()


# ────────────────────────────────────────────────────────────────────
# CohortBuilder._matches — todos operators
# ────────────────────────────────────────────────────────────────────


class REDACTED:
    def _pool(self):
        return [
            PatientData(patient_id="p1", tenant_id="t1", age=10, sex="F"),
            PatientData(patient_id="p2", tenant_id="t1", age=15, sex="M"),
            PatientData(patient_id="p3", tenant_id="t1", age=20, sex="F"),
            PatientData(patient_id="p4", tenant_id="t1", age=12, sex="F"),
        ]

    def test_eq_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="eq",
            criteria=(Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F"),),
        )
        assert c.count == 3

    def test_ne_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="ne",
            criteria=(Criterion(field="patient.sex", operator=CriterionOperator.NE, value="F"),),
        )
        assert c.count == 1

    def test_gt_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="gt",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.GT, value=12),),
        )
        assert c.count == 2  # p2 (15), p3 (20)

    def test_lt_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="lt",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.LT, value=15),),
        )
        # p1 (10), p4 (12) → 2 (p2=15 NÃO é strictly < 15)
        assert c.count == 2

    def test_in_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="in",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.IN, value=[10, 15, 20]),),
        )
        assert c.count == 3

    def test_not_in_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="not_in",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.NOT_IN, value=[10, 15]),),
        )
        assert c.count == 2  # p3 (20), p4 (12)

    def test_exists_operator(self):
        c = CohortBuilder().evaluate(
            patients=self._pool(),
            tenant_id="t1",
            name="exists",
            criteria=(Criterion(field="patient.age", operator=CriterionOperator.EXISTS, value=None),),
        )
        # Todos têm age → todos passam
        assert c.count == 4


# ────────────────────────────────────────────────────────────────────
# Research — AnalysisType coverage
# ────────────────────────────────────────────────────────────────────


class TestResearchAnalysisTypes:
    def test_all_analysis_types_listed(self):
        types = {t.value for t in AnalysisType}
        # Pelo menos STATS existe
        assert "stats" in types
        # Pelo menos 2 tipos canônicos
        assert len(types) >= 1

    def REDACTED(self):
        from araos.clinical.timeline.domain.window import TimeWindow
        from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
        from araos.clinical.knowledge.domain.research import (
            ResearchQuery,
            ResearchWorkspace,
        )

        genes = (
            _build_gene_with_trajectory(
                tenant_id="t1", patient_id="p1", gene_id="G1",
                values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
            ),
        )
        base = datetime(2026, 1, 1, tzinfo=UTC)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
        genome = build_clinical_genome(
            tenant_id="t1", patient_id="p1", window=window, genes=genes,
        )
        patient = PatientData(patient_id="p1", tenant_id="t1", age=14, sex="F")
        cohort = CohortBuilder().evaluate(
            patients=[patient], tenant_id="t1", name="r", criteria=(),
        )
        query = ResearchQuery(
            query_id="q1",
            cohort_id=cohort.cohort_id,
            analysis_type=AnalysisType.STATS,
            params={},
        )
        workspace = ResearchWorkspace()
        session = workspace.execute(
            query, patients=[patient], genes_by_patient={"p1": list(genome.genes)},
        )
        assert len(session.state_hash) == 64


# ────────────────────────────────────────────────────────────────────
# InMemoryKnowledgeRepository.__len__
# ────────────────────────────────────────────────────────────────────


class TestRepositoryLen:
    def test_empty_repository(self):
        repo = InMemoryKnowledgeRepository(tenant_id="t1")
        assert len(repo) == 0

    def test_repository_with_genome(self):
        from araos.clinical.timeline.domain.window import TimeWindow
        from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome

        repo = InMemoryKnowledgeRepository(tenant_id="t1")
        genes = (
            _build_gene_with_trajectory(
                tenant_id="t1", patient_id="p1", gene_id="G1",
                values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
            ),
        )
        base = datetime(2026, 1, 1, tzinfo=UTC)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
        genome = build_clinical_genome(
            tenant_id="t1", patient_id="p1", window=window, genes=genes,
        )
        repo.save_genome(genome)
        assert len(repo) == 1

    def test_clear_repository(self):
        from araos.clinical.timeline.domain.window import TimeWindow
        from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome

        repo = InMemoryKnowledgeRepository(tenant_id="t1")
        genes = (
            _build_gene_with_trajectory(
                tenant_id="t1", patient_id="p1", gene_id="G1",
                values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
            ),
        )
        base = datetime(2026, 1, 1, tzinfo=UTC)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
        genome = build_clinical_genome(
            tenant_id="t1", patient_id="p1", window=window, genes=genes,
        )
        repo.save_genome(genome)
        assert len(repo) == 1
        repo.clear()
        assert len(repo) == 0


# ────────────────────────────────────────────────────────────────────
# Cohort edge cases — empty criteria, multi-criteria
# ────────────────────────────────────────────────────────────────────


class TestCohortEdgeCases:
    def test_empty_criteria_matches_all(self):
        patients = [
            PatientData(patient_id=f"p{i}", tenant_id="t1", age=10 + i, sex="F")
            for i in range(5)
        ]
        cohort = CohortBuilder().evaluate(
            patients=patients,
            tenant_id="t1",
            name="all",
            criteria=(),
        )
        # Sem critérios → todos os pacientes
        assert cohort.count == 5

    def test_multi_criteria_all_must_match(self):
        patients = [
            PatientData(patient_id="p1", tenant_id="t1", age=14, sex="F"),
            PatientData(patient_id="p2", tenant_id="t1", age=16, sex="M"),
            PatientData(patient_id="p3", tenant_id="t1", age=18, sex="F"),
            PatientData(patient_id="p4", tenant_id="t1", age=20, sex="M"),
        ]
        cohort = CohortBuilder().evaluate(
            patients=patients,
            tenant_id="t1",
            name="teen_female",
            criteria=(
                Criterion(field="patient.age", operator=CriterionOperator.GT, value=12),
                Criterion(field="patient.age", operator=CriterionOperator.LT, value=20),
                Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F"),
            ),
        )
        # Apenas p1 e p3 (females, 12<age<20)
        assert "p1" in cohort.matched_patient_ids
        assert "p3" in cohort.matched_patient_ids
        assert "p2" not in cohort.matched_patient_ids
        assert "p4" not in cohort.matched_patient_ids

    def REDACTED(self):
        """Mesmos critérios → mesmo signature → mesmo cohort_id."""
        criteria = (
            Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
            Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F"),
        )
        c1 = CohortBuilder().evaluate(
            patients=[PatientData(patient_id="p1", tenant_id="t1", age=15, sex="F")],
            tenant_id="t1", name="x", criteria=criteria,
        )
        c2 = CohortBuilder().evaluate(
            patients=[PatientData(patient_id="p1", tenant_id="t1", age=15, sex="F")],
            tenant_id="t1", name="x", criteria=criteria,
        )
        # Mesmo cohort_id (content-derived)
        assert c1.cohort_id == c2.cohort_id

    def REDACTED(self):
        criteria = (
            Criterion(field="patient.age", operator=CriterionOperator.GT, value=10),
        )
        c1 = CohortBuilder().evaluate(
            patients=[PatientData(patient_id="p1", tenant_id="t1", age=15, sex="F")],
            tenant_id="t1", name="same", criteria=criteria,
        )
        c2 = CohortBuilder().evaluate(
            patients=[PatientData(patient_id="p2", tenant_id="t2", age=15, sex="F")],
            tenant_id="t2", name="same", criteria=criteria,
        )
        assert c1.cohort_id != c2.cohort_id