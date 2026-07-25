"""
Sprint 4.4 — Cohort Builder.

Testes cobrindo:
    - 7 CriterionOperators (EQ, NE, GT, LT, IN, NOT_IN, EXISTS).
    - PatientData required fields.
    - Criterion fields suportados (patient.age, patient.sex, etc.).
    - Cohort determinístico.
    - State_hash determinístico across runs.
    - Tenant isolation enforced.
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.domain.cohort import (
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)


def _patient(patient_id="p1", tenant_id="t1", age=10, sex="F") -> PatientData:
    return PatientData(
        patient_id=patient_id,
        tenant_id=tenant_id,
        age=age,
        sex=sex,
        diagnosis_codes=(),
    )


class TestCohortBuilderBasic:
    """Contract tests."""

    def test_returns_cohort(self):
        # Act
        criterion = Criterion(
            field="patient.age", operator=CriterionOperator.GT, value=10,
        )
        cohort = CohortBuilder().evaluate(
            patients=(_patient(age=20, patient_id="p1"),),
            tenant_id="t1",
            name="older_than_10",
            criteria=(criterion,),
        )
        # Assert
        assert hasattr(cohort, "cohort_id")
        assert hasattr(cohort, "matched_patient_ids")

    def test_empty_criteria_matches_all(self):
        # Act
        cohort = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1"), _patient(patient_id="p2")),
            tenant_id="t1",
            name="all_patients",
            criteria=(),
        )
        # Assert
        assert "p1" in cohort.matched_patient_ids
        assert "p2" in cohort.matched_patient_ids

    def test_tenant_isolation_enforced(self):
        # Act — cross-tenant patient should be excluded
        criterion = Criterion(
            field="patient.age", operator=CriterionOperator.GT, value=10,
        )
        cohort = CohortBuilder().evaluate(
            patients=(
                _patient(patient_id="p1", tenant_id="t1", age=20),
                _patient(patient_id="p2", tenant_id="t_other", age=20),
            ),
            tenant_id="t1",
            name="only_t1",
            criteria=(criterion,),
        )
        # Assert
        assert "p1" in cohort.matched_patient_ids
        assert "p2" not in cohort.matched_patient_ids


class TestCohortOperators:
    """Cada operator canônico."""

    @pytest.mark.parametrize("op", list(CriterionOperator))
    def test_operator_enum_complete(self, op):
        # Assert
        assert op.value in {"eq", "ne", "gt", "lt", "in", "not_in", "exists"}

    def test_eq_matches_correct_value(self):
        # Act
        criterion = Criterion(
            field="patient.sex", operator=CriterionOperator.EQ, value="F",
        )
        cohort = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1"), _patient(patient_id="p2")),
            tenant_id="t1",
            name="female",
            criteria=(criterion,),
        )
        # Assert — both supplied as F
        assert "p1" in cohort.matched_patient_ids
        assert "p2" in cohort.matched_patient_ids

    def test_ne_filters_correctly(self):
        # Act
        criterion = Criterion(
            field="patient.age", operator=CriterionOperator.NE, value=10,
        )
        cohort = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1", age=10), _patient(patient_id="p2", age=15)),
            tenant_id="t1",
            name="not_ten",
            criteria=(criterion,),
        )
        # Assert — p2 (age=15) is NE 10 → included; p1 (age=10) excluded
        assert "p1" not in cohort.matched_patient_ids
        assert "p2" in cohort.matched_patient_ids

    def test_gt_lt(self):
        # Act
        c1 = Criterion(field="patient.age", operator=CriterionOperator.GT, value=10)
        c2 = Criterion(field="patient.age", operator=CriterionOperator.LT, value=20)
        cohort = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1", age=15),),
            tenant_id="t1",
            name="between_10_20",
            criteria=(c1, c2),
        )
        # Assert
        assert "p1" in cohort.matched_patient_ids


class TestCohortByPatientField:
    """Patient-level filtering."""

    def test_filter_by_age(self):
        # Act
        criterion = Criterion(
            field="patient.age", operator=CriterionOperator.GT, value=18,
        )
        cohort = CohortBuilder().evaluate(
            patients=(
                _patient(patient_id="adult", age=25),
                _patient(patient_id="minor", age=10),
            ),
            tenant_id="t1",
            name="adults",
            criteria=(criterion,),
        )
        # Assert
        assert "adult" in cohort.matched_patient_ids
        assert "minor" not in cohort.matched_patient_ids


class TestCohortCompositeCriteria:
    """Múltiplos critérios = interseção."""

    def test_age_and_sex_intersection(self):
        # Act
        c1 = Criterion(field="patient.age", operator=CriterionOperator.GT, value=10)
        c2 = Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F")
        cohort = CohortBuilder().evaluate(
            patients=(_patient(age=15, sex="F"),),
            tenant_id="t1",
            name="female_over_10",
            criteria=(c1, c2),
        )
        # Assert
        assert len(cohort.matched_patient_ids) == 1

    def REDACTED(self):
        # Act
        c1 = Criterion(field="patient.age", operator=CriterionOperator.GT, value=18)
        c2 = Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F")
        cohort = CohortBuilder().evaluate(
            patients=(
                _patient(patient_id="p_correct", age=25, sex="F"),
                _patient(patient_id="p_too_young", age=10, sex="F"),
                _patient(patient_id="p_male", age=25, sex="M"),
            ),
            tenant_id="t1",
            name="female_adults",
            criteria=(c1, c2),
        )
        # Assert
        assert cohort.matched_patient_ids == ("p_correct",)


class TestCohortDeterminism:
    """Determinismo e state_hash."""

    def test_state_hash_deterministic(self):
        # Act
        c = Criterion(field="patient.age", operator=CriterionOperator.GT, value=10)
        c1 = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1", age=20),),
            tenant_id="t1",
            name="older",
            criteria=(c,),
        )
        c2 = CohortBuilder().evaluate(
            patients=(_patient(patient_id="p1", age=20),),
            tenant_id="t1",
            name="older",
            criteria=(c,),
        )
        # Assert
        assert c1.state_hash == c2.state_hash

    def test_cohort_id_format(self):
        # Act
        cohort = CohortBuilder().evaluate(
            patients=(_patient(),),
            tenant_id="t1",
            name="x",
            criteria=(),
        )
        # Assert
        assert cohort.cohort_id.startswith("cohort_")
