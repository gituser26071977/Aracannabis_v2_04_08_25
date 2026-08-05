"""
Testes do Catálogo do Clinical Event Engine.

Cobertura:
    - get_event_definition
    - is_known_event_type
    - list_event_types
    - count_event_types
    - Conteúdo do catálogo (eventos iniciais do ADR-0001)
"""

from __future__ import annotations

import pytest

from araos.clinical.event_store.catalog import (
    CLINICAL_EVENT_CATALOG,
    ClinicalEventDefinition,
    EventProducer,
    EventStatus,
    count_event_types,
    get_event_definition,
    is_known_event_type,
    list_event_types,
)


# ═══════════════════════════════════════════════════════════════════════
# Catálogo contém eventos do ADR-0001
# ═══════════════════════════════════════════════════════════════════════


REQUIRED_EVENTS = [
    # Paciente
    "PATIENT_CREATED",
    "PATIENT_UPDATED",
    # Diagnóstico
    "DIAGNOSIS_ADDED",
    "DIAGNOSIS_REMOVED",
    "DIAGNOSIS_UPDATED",
    "DIAGNOSIS_STATUS_CHANGED",
    # Escalas
    "SCALE_APPLIED",
    "SCALE_UPDATED",
    # Medicações
    "MEDICATION_STARTED",
    "MEDICATION_ADJUSTED",
    "MEDICATION_STOPPED",
    # Cannabis
    "CANNABIS_ADJUSTED",
    # Terapias
    "THERAPY_STARTED",
    "THERAPY_FINISHED",
    # Contexto
    "SCHOOL_CHANGED",
    "SLEEP_CHANGED",
    "WEIGHT_CHANGED",
    "HEIGHT_CHANGED",
    # Críticos
    "CRISIS_RECORDED",
    "HOSPITALIZATION",
    "SURGERY",
    # Exames
    "LABORATORY_RESULT",
    "IMAGING_RESULT",
    # Atendimento
    "CONSULTATION_PERFORMED",
    "FAMILY_MEETING",
    "CARE_PLAN_UPDATED",
]


class TestCatalogContent:
    @pytest.mark.parametrize("event_type", REQUIRED_EVENTS)
    def test_required_event_present(self, event_type: str):
        assert event_type in CLINICAL_EVENT_CATALOG
        definition = CLINICAL_EVENT_CATALOG[event_type]
        assert isinstance(definition, ClinicalEventDefinition)
        assert definition.event_type == event_type
        assert definition.domain == "clinical"
        assert definition.status == EventStatus.ACTIVE

    @pytest.mark.parametrize("event_type", REQUIRED_EVENTS)
    def test_required_event_is_sensitive(self, event_type: str):
        # LGPD: todos os eventos clínicos são sensíveis por padrão
        assert CLINICAL_EVENT_CATALOG[event_type].sensitive is True

    def test_has_description(self):
        for event_type, definition in CLINICAL_EVENT_CATALOG.items():
            assert definition.description, f"{event_type} missing description"

    def test_has_producer(self):
        for event_type, definition in CLINICAL_EVENT_CATALOG.items():
            assert definition.producer, f"{event_type} missing producer"


# ═══════════════════════════════════════════════════════════════════════
# API: get_event_definition
# ═══════════════════════════════════════════════════════════════════════


class TestGetEventDefinition:
    def test_returns_definition_for_known(self):
        d = get_event_definition("SCALE_APPLIED")
        assert d is not None
        assert d.event_type == "SCALE_APPLIED"

    def test_returns_none_for_unknown(self):
        assert get_event_definition("NOT_A_REAL_EVENT") is None

    def test_returns_none_for_empty(self):
        assert get_event_definition("") is None


# ═══════════════════════════════════════════════════════════════════════
# API: is_known_event_type
# ═══════════════════════════════════════════════════════════════════════


class TestIsKnownEventType:
    def test_true_for_known(self):
        assert is_known_event_type("SCALE_APPLIED") is True

    def test_false_for_unknown(self):
        assert is_known_event_type("UNKNOWN_EVENT") is False

    def test_false_for_empty(self):
        assert is_known_event_type("") is False


# ═══════════════════════════════════════════════════════════════════════
# API: list_event_types
# ═══════════════════════════════════════════════════════════════════════


class TestListEventTypes:
    def test_returns_all_by_default(self):
        all_types = list_event_types()
        assert len(all_types) == count_event_types()

    def REDACTED(self):
        # Como não há deprecated por padrão, active_only == all
        active = list_event_types(active_only=True)
        all_types = list_event_types(active_only=False)
        assert len(active) == len(all_types)

    def test_filter_by_producer(self):
        neuro_events = list_event_types(producer="neurodevelopmental")
        assert all(d.producer == "neurodevelopmental" for d in neuro_events)
        assert any(d.event_type == "SCALE_APPLIED" for d in neuro_events)
        assert any(d.event_type == "SCALE_UPDATED" for d in neuro_events)

    def test_filter_by_producer_cannabis(self):
        cannabis_events = list_event_types(producer="cannabis")
        assert all(d.producer == "cannabis" for d in cannabis_events)
        assert any(d.event_type == "CANNABIS_ADJUSTED" for d in cannabis_events)

    def test_filter_by_producer_core(self):
        core_events = list_event_types(producer="core")
        assert len(core_events) >= 10  # Maioria dos eventos é core
        assert any(d.event_type == "PATIENT_CREATED" for d in core_events)

    def test_returns_list_of_definitions(self):
        events = list_event_types()
        assert all(isinstance(d, ClinicalEventDefinition) for d in events)


# ═══════════════════════════════════════════════════════════════════════
# API: count_event_types
# ═══════════════════════════════════════════════════════════════════════


class TestCountEventTypes:
    def test_count_matches_catalog_size(self):
        assert count_event_types() == len(CLINICAL_EVENT_CATALOG)

    def test_count_at_least_25(self):
        # ADR-0001 lista 26 eventos iniciais
        assert count_event_types() >= 25


# ═══════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════


class TestEnums:
    def test_event_status_values(self):
        assert EventStatus.ACTIVE.value == "active"
        assert EventStatus.DEPRECATED.value == "deprecated"

    def test_event_producer_values(self):
        assert EventProducer.CORE.value == "core"
        assert EventProducer.NEURODEVELOPMENTAL.value == "neurodevelopmental"
        assert EventProducer.CANNABIS.value == "cannabis"
