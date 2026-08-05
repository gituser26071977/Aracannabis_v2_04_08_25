"""
Testes do Publisher do Clinical Event Engine.

Cobertura:
    - publish: happy path
    - Validação contra catálogo
    - Validação contra JSON Schema
    - Default event_datetime
    - Default event_version
    - Fan-out para o Bus (com FakeBus)
    - Erros: UnknownEventType, EventValidation
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest

from araos.clinical.event_store.publisher import (
    ClinicalEventPublisher,
    EventValidationError,
    UnknownEventTypeError,
)
from araos.clinical.event_store.store import InMemoryClinicalEventStore


TENANT = "tenant-1"
PATIENT = "patient-1"


class FakeBus:
    """Stub mínimo de Event Bus para testes do publisher."""

    def __init__(self) -> None:
        self.published: List[Any] = []
        self.fail_on_publish = False

    def publish(self, envelope: Any) -> None:
        if self.fail_on_publish:
            raise RuntimeError("simulated bus failure")
        self.published.append(envelope)

    def publish_sync(self, envelope: Any) -> None:
        if self.fail_on_publish:
            raise RuntimeError("simulated bus failure")
        self.published.append(envelope)


@pytest.fixture
def store() -> InMemoryClinicalEventStore:
    return InMemoryClinicalEventStore()


@pytest.fixture
def bus() -> FakeBus:
    return FakeBus()


@pytest.fixture
def publisher(store, bus) -> ClinicalEventPublisher:
    return ClinicalEventPublisher(store=store, bus=bus)


# ═══════════════════════════════════════════════════════════════════════
# publish — happy path
# ═══════════════════════════════════════════════════════════════════════


class TestPublishHappyPath:
    def test_returns_event_id(self, publisher):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert eid is not None
        assert len(eid) == 36

    def test_event_is_persisted(self, publisher, store):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        event = store.get(eid)
        assert event is not None
        assert event["event_type"] == "SCALE_APPLIED"

    def test_event_published_to_bus(self, publisher, bus):
        publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert len(bus.published) == 1
        envelope = bus.published[0]
        assert envelope.event_type == "SCALE_APPLIED"
        assert envelope.tenant_id == TENANT

    def test_default_event_datetime_is_now(self, publisher, store):
        before = datetime.now(timezone.utc)
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        after = datetime.now(timezone.utc)
        event = store.get(eid)
        ev_dt = datetime.fromisoformat(event["event_datetime"])
        assert before <= ev_dt <= after

    def REDACTED(self, publisher, store):
        custom_dt = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            event_datetime=custom_dt,
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        event = store.get(eid)
        ev_dt = datetime.fromisoformat(event["event_datetime"])
        assert ev_dt == custom_dt

    def test_actor_fields_propagated(self, publisher, store):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="DIAGNOSIS_ADDED",
            payload={"cid10": "F84.0", "label": "TEA"},
            created_by="prof-1",
            created_by_user="user-1",
        )
        event = store.get(eid)
        assert event["created_by"] == "prof-1"
        assert event["created_by_user"] == "user-1"

    def test_aggregate_propagated(self, publisher, store):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
            aggregate_type="scale",
            aggregate_id="scale-123",
        )
        event = store.get(eid)
        assert event["aggregate_type"] == "scale"
        assert event["aggregate_id"] == "scale-123"

    def test_metadata_propagated(self, publisher, store):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
            metadata={"correlation_id": "abc-123", "tags": ["urgent"]},
        )
        event = store.get(eid)
        assert event["metadata"]["correlation_id"] == "abc-123"


# ═══════════════════════════════════════════════════════════════════════
# publish — erros
# ═══════════════════════════════════════════════════════════════════════


class TestPublishErrors:
    def test_unknown_event_type_raises(self, publisher):
        with pytest.raises(UnknownEventTypeError):
            publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="NOT_A_REAL_EVENT",
                payload={},
            )

    def REDACTED(self, publisher, store):
        with pytest.raises(UnknownEventTypeError):
            publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="NOT_A_REAL_EVENT",
                payload={},
            )
        assert store.count(TENANT) == 0

    def REDACTED(
        self, publisher, bus
    ):
        with pytest.raises(UnknownEventTypeError):
            publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="NOT_A_REAL_EVENT",
                payload={},
            )
        assert bus.published == []


# ═══════════════════════════════════════════════════════════════════════
# Validação contra JSON Schema
# ═══════════════════════════════════════════════════════════════════════


class TestPayloadValidation:
    """Cenários onde há json_schema registrado no catálogo.

    Como o catálogo de produção ainda não tem schemas, este teste
    monkey-patch o catálogo para incluir um event_type com schema.
    """

    def test_invalid_payload_raises(self, store, bus):
        from araos.clinical.event_store import catalog as catalog_module
        from araos.clinical.event_store.catalog import (
            ClinicalEventDefinition,
        )

        # Adiciona evento de teste com schema
        catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"] = (
            ClinicalEventDefinition(
                event_type="TEST_WITH_SCHEMA",
                domain="clinical",
                producer="core",
                description="Test",
                json_schema={
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                    "required": ["x"],
                },
            )
        )
        try:
            publisher = ClinicalEventPublisher(
                store=store, bus=bus, validate_payload=True
            )
            with pytest.raises(EventValidationError):
                publisher.publish(
                    tenant_id=TENANT,
                    patient_id=PATIENT,
                    event_type="TEST_WITH_SCHEMA",
                    payload={"x": "not_an_integer"},
                )
        finally:
            del catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"]

    def test_valid_payload_accepted(self, store, bus):
        from araos.clinical.event_store import catalog as catalog_module
        from araos.clinical.event_store.catalog import (
            ClinicalEventDefinition,
        )

        catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"] = (
            ClinicalEventDefinition(
                event_type="TEST_WITH_SCHEMA",
                domain="clinical",
                producer="core",
                description="Test",
                json_schema={
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                    "required": ["x"],
                },
            )
        )
        try:
            publisher = ClinicalEventPublisher(
                store=store, bus=bus, validate_payload=True
            )
            eid = publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="TEST_WITH_SCHEMA",
                payload={"x": 42},
            )
            assert eid is not None
        finally:
            del catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"]

    def test_validation_can_be_disabled(self, store, bus):
        from araos.clinical.event_store import catalog as catalog_module
        from araos.clinical.event_store.catalog import (
            ClinicalEventDefinition,
        )

        catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"] = (
            ClinicalEventDefinition(
                event_type="TEST_WITH_SCHEMA",
                domain="clinical",
                producer="core",
                description="Test",
                json_schema={
                    "type": "object",
                    "properties": {"x": {"type": "integer"}},
                    "required": ["x"],
                },
            )
        )
        try:
            publisher = ClinicalEventPublisher(
                store=store, bus=bus, validate_payload=False
            )
            # Sem validação, payload inválido passa
            eid = publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="TEST_WITH_SCHEMA",
                payload={"x": "not_an_integer"},
            )
            assert eid is not None
        finally:
            del catalog_module.CLINICAL_EVENT_CATALOG["TEST_WITH_SCHEMA"]


# ═══════════════════════════════════════════════════════════════════════
# Bus é opcional
# ═══════════════════════════════════════════════════════════════════════


class TestBusIsOptional:
    def test_publish_without_bus_works(self, store):
        publisher = ClinicalEventPublisher(store=store, bus=None)
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        assert eid is not None
        assert store.get(eid) is not None

    def REDACTED(self, store, bus):
        bus.fail_on_publish = True
        publisher = ClinicalEventPublisher(store=store, bus=bus)
        # Não deve lançar — graceful degradation
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        # Event foi persistido mesmo com falha no bus
        assert eid is not None
        assert store.get(eid) is not None


# ═══════════════════════════════════════════════════════════════════════
# Hash chain via publisher
# ═══════════════════════════════════════════════════════════════════════


class TestChainViaPublisher:
    def REDACTED(self, publisher, store):
        for i in range(5):
            publisher.publish(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="SCALE_APPLIED",
                payload={"scale_code": "GAD7", "total_score": i},
            )
        assert store.verify_chain(TENANT) is True

    def test_event_version_from_catalog(self, publisher, store):
        eid = publisher.publish(
            tenant_id=TENANT,
            patient_id=PATIENT,
            event_type="SCALE_APPLIED",
            payload={"scale_code": "GAD7", "total_score": 5},
        )
        event = store.get(eid)
        # Catálogo define version "1.0" para SCALE_APPLIED
        assert event["event_version"] == "1.0"
