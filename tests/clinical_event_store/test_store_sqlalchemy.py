"""
Testes do Store SQLAlchemy do Clinical Event Engine.

Cobertura:
    - SqlAlchemyClinicalEventStore: append, get, query, last_hash,
      verify_chain, count com banco SQLite in-memory
    - Integração completa (round-trip)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.clinical.event_store.store import SqlAlchemyClinicalEventStore
from araos.platform.tenant.models import Base


TENANT = "tenant-1"
PATIENT = "patient-1"
OTHER_PATIENT = "patient-2"
OTHER_TENANT = "tenant-2"
DT_BASE = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def store(session) -> SqlAlchemyClinicalEventStore:
    return SqlAlchemyClinicalEventStore(session)


def _make_args(**overrides):
    base = {
        "tenant_id": TENANT,
        "patient_id": PATIENT,
        "event_type": "SCALE_APPLIED",
        "event_datetime": DT_BASE,
        "source_module": "neurodevelopmental",
        "payload": {"scale_code": "GAD7", "total_score": 5},
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════════════════
# append
# ═══════════════════════════════════════════════════════════════════════


class TestAppendSQL:
    def test_returns_event_id(self, store):
        eid = store.append(**_make_args())
        assert isinstance(eid, str)
        assert len(eid) == 36

    def test_event_retrievable_by_id(self, store):
        eid = store.append(**_make_args())
        event = store.get(eid)
        assert event is not None
        assert event["id"] == eid

    def test_first_event_links_to_genesis(self, store):
        eid = store.append(**_make_args())
        event = store.get(eid)
        assert event["previous_hash"] is None

    def REDACTED(self, store):
        e1 = store.append(**_make_args(event_type="A"))
        e2 = store.append(**_make_args(event_type="B"))
        e1_dict = store.get(e1)
        e2_dict = store.get(e2)
        assert e2_dict["previous_hash"] == e1_dict["event_hash"]

    def test_accepts_naive_datetime(self, store):
        naive_dt = datetime(2026, 7, 15, 10, 0)
        eid = store.append(**_make_args(event_datetime=naive_dt))
        event = store.get(eid)
        # Deve ser normalizado para UTC
        assert event["event_datetime"] is not None

    def test_accepts_metadata(self, store):
        eid = store.append(
            **_make_args(metadata={"correlation_id": "abc", "tags": ["x"]})
        )
        event = store.get(eid)
        assert event["metadata"]["correlation_id"] == "abc"

    def test_accepts_aggregate(self, store):
        eid = store.append(
            **_make_args(aggregate_type="scale", aggregate_id="scale-1")
        )
        event = store.get(eid)
        assert event["aggregate_type"] == "scale"
        assert event["aggregate_id"] == "scale-1"

    def test_accepts_actor(self, store):
        eid = store.append(
            **_make_args(created_by="prof-1", created_by_user="user-1")
        )
        event = store.get(eid)
        assert event["created_by"] == "prof-1"
        assert event["created_by_user"] == "user-1"

    def test_event_version_propagated(self, store):
        eid = store.append(**_make_args(event_version="2.0"))
        event = store.get(eid)
        assert event["event_version"] == "2.0"


# ═══════════════════════════════════════════════════════════════════════
# append — validação
# ═══════════════════════════════════════════════════════════════════════


class TestAppendValidationSQL:
    def test_missing_event_datetime_raises(self, store):
        with pytest.raises(ValueError):
            store.append(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="SCALE_APPLIED",
                event_datetime=None,  # type: ignore[arg-type]
                source_module="neurodevelopmental",
                payload={},
            )

    def test_missing_event_type_raises(self, store):
        with pytest.raises(ValueError):
            store.append(
                tenant_id=TENANT,
                patient_id=PATIENT,
                event_type="",
                event_datetime=DT_BASE,
                source_module="neurodevelopmental",
                payload={},
            )

    def test_missing_tenant_id_raises(self, store):
        with pytest.raises(ValueError):
            store.append(**_make_args(tenant_id=""))

    def test_missing_patient_id_raises(self, store):
        with pytest.raises(ValueError):
            store.append(**_make_args(patient_id=""))


# ═══════════════════════════════════════════════════════════════════════
# get
# ═══════════════════════════════════════════════════════════════════════


class TestGetSQL:
    def test_returns_none_for_unknown(self, store):
        assert store.get("does-not-exist") is None

    def test_returns_full_event(self, store):
        eid = store.append(**_make_args())
        e = store.get(eid)
        assert "event_hash" in e
        assert "previous_hash" in e
        assert "payload" in e
        assert "metadata" in e


# ═══════════════════════════════════════════════════════════════════════
# query
# ═══════════════════════════════════════════════════════════════════════


class TestQuerySQL:
    def test_empty_returns_empty(self, store):
        assert store.query(tenant_id=TENANT) == []

    def test_filters_by_tenant(self, store):
        store.append(**_make_args(tenant_id=TENANT))
        store.append(**_make_args(tenant_id=OTHER_TENANT))
        results = store.query(tenant_id=TENANT)
        assert len(results) == 1
        assert results[0]["tenant_id"] == TENANT

    def test_filters_by_patient(self, store):
        store.append(**_make_args(patient_id=PATIENT))
        store.append(**_make_args(patient_id=OTHER_PATIENT))
        results = store.query(tenant_id=TENANT, patient_id=PATIENT)
        assert len(results) == 1
        assert results[0]["patient_id"] == PATIENT

    def test_filters_by_event_type_exact(self, store):
        store.append(**_make_args(event_type="SCALE_APPLIED"))
        store.append(**_make_args(event_type="DIAGNOSIS_ADDED"))
        results = store.query(tenant_id=TENANT, event_types=["SCALE_APPLIED"])
        assert len(results) == 1
        assert results[0]["event_type"] == "SCALE_APPLIED"

    def REDACTED(self, store):
        store.append(**_make_args(event_type="DIAGNOSIS_ADDED"))
        store.append(**_make_args(event_type="DIAGNOSIS_REMOVED"))
        store.append(**_make_args(event_type="SCALE_APPLIED"))
        results = store.query(tenant_id=TENANT, event_types=["DIAGNOSIS_*"])
        assert len(results) == 2

    def REDACTED(self, store):
        store.append(**_make_args(event_type="A"))
        store.append(**_make_args(event_type="B"))
        store.append(**_make_args(event_type="C"))
        results = store.query(tenant_id=TENANT, event_types=["A", "C"])
        assert len(results) == 2

    def test_filters_by_aggregate_type(self, store):
        store.append(**_make_args(aggregate_type="scale", aggregate_id="s1"))
        store.append(**_make_args(aggregate_type="medication", aggregate_id="m1"))
        results = store.query(tenant_id=TENANT, aggregate_type="scale")
        assert len(results) == 1

    def test_filters_by_aggregate_id(self, store):
        store.append(**_make_args(aggregate_type="scale", aggregate_id="s1"))
        store.append(**_make_args(aggregate_type="scale", aggregate_id="s2"))
        results = store.query(
            tenant_id=TENANT, aggregate_type="scale", aggregate_id="s1"
        )
        assert len(results) == 1
        assert results[0]["aggregate_id"] == "s1"

    def test_since_filter(self, store):
        store.append(
            **_make_args(
                event_type="old", event_datetime=DT_BASE - timedelta(days=10)
            )
        )
        store.append(**_make_args(event_type="new", event_datetime=DT_BASE))
        results = store.query(tenant_id=TENANT, since=DT_BASE - timedelta(days=1))
        assert len(results) == 1
        assert results[0]["event_type"] == "new"

    def test_until_filter(self, store):
        store.append(
            **_make_args(
                event_type="old", event_datetime=DT_BASE - timedelta(days=10)
            )
        )
        store.append(**_make_args(event_type="new", event_datetime=DT_BASE))
        results = store.query(tenant_id=TENANT, until=DT_BASE - timedelta(days=1))
        assert len(results) == 1
        assert results[0]["event_type"] == "old"

    def test_limit(self, store):
        for i in range(5):
            store.append(
                **_make_args(
                    event_type=f"E{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        results = store.query(tenant_id=TENANT, limit=2)
        assert len(results) == 2

    def test_default_order_asc(self, store):
        """Default order = sequence ASC (insertion order, canonical chain)."""
        store.append(
            **_make_args(event_type="A", event_datetime=DT_BASE + timedelta(hours=2))
        )
        store.append(
            **_make_args(event_type="B", event_datetime=DT_BASE + timedelta(hours=1))
        )
        results = store.query(tenant_id=TENANT)
        # Sequence ASC = insertion order, independent of event_datetime
        assert [r["event_type"] for r in results] == ["A", "B"]

    def test_event_datetime_order_explicit(self, store):
        """event_datetime ASC deve ser explicitamente solicitado."""
        store.append(
            **_make_args(event_type="A", event_datetime=DT_BASE + timedelta(hours=2))
        )
        store.append(
            **_make_args(event_type="B", event_datetime=DT_BASE + timedelta(hours=1))
        )
        results = store.query(tenant_id=TENANT, order_by="event_datetime ASC")
        assert [r["event_type"] for r in results] == ["B", "A"]

    def test_sequence_desc_order(self, store):
        store.append(**_make_args(event_type="A"))
        store.append(**_make_args(event_type="B"))
        results = store.query(tenant_id=TENANT, order_by="sequence DESC")
        assert [r["event_type"] for r in results] == ["B", "A"]

    def test_desc_order(self, store):
        store.append(
            **_make_args(event_type="A", event_datetime=DT_BASE)
        )
        store.append(
            **_make_args(event_type="B", event_datetime=DT_BASE + timedelta(hours=1))
        )
        results = store.query(tenant_id=TENANT, order_by="event_datetime DESC")
        assert [r["event_type"] for r in results] == ["B", "A"]

    def test_created_at_order(self, store):
        store.append(**_make_args(event_type="A"))
        store.append(**_make_args(event_type="B"))
        asc = store.query(tenant_id=TENANT, order_by="created_at ASC")
        desc = store.query(tenant_id=TENANT, order_by="created_at DESC")
        assert asc[0]["event_type"] == "A"
        assert desc[0]["event_type"] == "B"

    def test_soft_delete_excluded(self, store):
        eid = store.append(**_make_args())
        # Simula soft delete
        from araos.clinical.event_store.models import ClinicalEventModel
        from araos.platform.tenant.models import generate_uuid

        s = store.db
        e = s.query(ClinicalEventModel).filter(ClinicalEventModel.id == eid).one()
        e.deleted_at = datetime.now(timezone.utc)
        s.commit()
        results = store.query(tenant_id=TENANT)
        assert len(results) == 0

    def test_include_deleted(self, store):
        eid = store.append(**_make_args())
        from araos.clinical.event_store.models import ClinicalEventModel
        s = store.db
        e = s.query(ClinicalEventModel).filter(ClinicalEventModel.id == eid).one()
        e.deleted_at = datetime.now(timezone.utc)
        s.commit()
        results = store.query(tenant_id=TENANT, include_deleted=True)
        assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════
# last_hash
# ═══════════════════════════════════════════════════════════════════════


class TestLastHashSQL:
    def test_empty_tenant(self, store):
        assert store.last_hash(TENANT) is None

    def test_returns_hash_of_last(self, store):
        store.append(**_make_args(event_type="A"))
        e2 = store.append(**_make_args(event_type="B"))
        e2_dict = store.get(e2)
        assert store.last_hash(TENANT) == e2_dict["event_hash"]

    def test_per_tenant_isolation(self, store):
        store.append(**_make_args(tenant_id=TENANT, event_type="A"))
        store.append(**_make_args(tenant_id=OTHER_TENANT, event_type="B"))
        assert store.last_hash(TENANT) != store.last_hash(OTHER_TENANT)


# ═══════════════════════════════════════════════════════════════════════
# verify_chain
# ═══════════════════════════════════════════════════════════════════════


class TestVerifyChainSQL:
    def test_empty_chain(self, store):
        assert store.verify_chain(TENANT) is True

    def test_valid_chain(self, store):
        for i in range(5):
            store.append(
                **_make_args(
                    event_type=f"E{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        assert store.verify_chain(TENANT) is True

    def test_tampered_chain_detected(self, store):
        store.append(**_make_args(event_type="A"))
        e2 = store.append(**_make_args(event_type="B"))
        # Tamper
        from araos.clinical.event_store.models import ClinicalEventModel
        s = store.db
        e = s.query(ClinicalEventModel).filter(ClinicalEventModel.id == e2).one()
        e.payload = {"scale_code": "TAMPERED", "total_score": 999}
        s.commit()
        assert store.verify_chain(TENANT) is False

    def test_per_patient_filter(self, store):
        for i in range(3):
            store.append(
                **_make_args(patient_id=PATIENT, event_type=f"P{i}")
            )
        assert store.verify_chain(TENANT, patient_id=PATIENT) is True


# ═══════════════════════════════════════════════════════════════════════
# count
# ═══════════════════════════════════════════════════════════════════════


class TestCountSQL:
    def test_empty(self, store):
        assert store.count(TENANT) == 0

    def test_counts_per_tenant(self, store):
        for i in range(3):
            store.append(**_make_args(event_type=f"E{i}"))
        store.append(**_make_args(tenant_id=OTHER_TENANT))
        assert store.count(TENANT) == 3
        assert store.count(OTHER_TENANT) == 1

    def test_counts_per_patient(self, store):
        for i in range(2):
            store.append(**_make_args(patient_id=PATIENT))
        for i in range(3):
            store.append(**_make_args(patient_id=OTHER_PATIENT))
        assert store.count(TENANT, patient_id=PATIENT) == 2
        assert store.count(TENANT, patient_id=OTHER_PATIENT) == 3
