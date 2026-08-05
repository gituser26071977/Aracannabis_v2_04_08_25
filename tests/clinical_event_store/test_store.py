"""
Testes do Store (InMemory) do Clinical Event Engine.

Cobertura:
    - append: básico, validação, hash chain link
    - get: por id
    - query: filtros, wildcard, ordenação, range de data, soft delete
    - last_hash
    - verify_chain
    - count
    - Thread safety
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.event_store.store import InMemoryClinicalEventStore


TENANT = "tenant-1"
PATIENT = "patient-1"
OTHER_PATIENT = "patient-2"
OTHER_TENANT = "tenant-2"
DT_BASE = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def store() -> InMemoryClinicalEventStore:
    return InMemoryClinicalEventStore()


def _make_event_args(
    **overrides,
):
    """Helper para gerar kwargs de append com defaults sensatos."""
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
# append — happy paths
# ═══════════════════════════════════════════════════════════════════════


class TestAppend:
    def test_returns_event_id(self, store):
        eid = store.append(**_make_event_args())
        assert isinstance(eid, str)
        assert len(eid) == 36  # UUID4

    def test_event_is_retrievable_by_id(self, store):
        eid = store.append(**_make_event_args())
        event = store.get(eid)
        assert event is not None
        assert event["id"] == eid

    def test_event_has_required_fields(self, store):
        eid = store.append(**_make_event_args())
        e = store.get(eid)
        assert e["tenant_id"] == TENANT
        assert e["patient_id"] == PATIENT
        assert e["event_type"] == "SCALE_APPLIED"
        assert e["source_module"] == "neurodevelopmental"
        assert e["event_version"] == "1.0"
        assert e["event_hash"] is not None
        assert len(e["event_hash"]) == 64

    def test_first_event_links_to_genesis(self, store):
        eid = store.append(**_make_event_args())
        e = store.get(eid)
        assert e["previous_hash"] is None  # primeiro evento

    def test_second_event_links_to_first(self, store):
        e1_id = store.append(**_make_event_args(event_type="A"))
        e1 = store.get(e1_id)
        e2_id = store.append(**_make_event_args(event_type="B"))
        e2 = store.get(e2_id)
        assert e2["previous_hash"] == e1["event_hash"]

    def test_accepts_optional_metadata(self, store):
        eid = store.append(
            **_make_event_args(metadata={"correlation_id": "abc", "tags": ["x"]})
        )
        e = store.get(eid)
        assert e["metadata"]["correlation_id"] == "abc"

    def test_accepts_aggregate(self, store):
        eid = store.append(
            **_make_event_args(
                aggregate_type="scale",
                aggregate_id="scale-123",
            )
        )
        e = store.get(eid)
        assert e["aggregate_type"] == "scale"
        assert e["aggregate_id"] == "scale-123"

    def test_accepts_actor_fields(self, store):
        eid = store.append(
            **_make_event_args(
                created_by="prof-1",
                created_by_user="user-1",
            )
        )
        e = store.get(eid)
        assert e["created_by"] == "prof-1"
        assert e["created_by_user"] == "user-1"

    def REDACTED(self, store):
        payload = {"x": 1}
        eid = store.append(**_make_event_args(payload=payload))
        payload["x"] = 999  # mutação externa
        e = store.get(eid)
        assert e["payload"]["x"] == 1  # inalterado


# ═══════════════════════════════════════════════════════════════════════
# append — validação
# ═══════════════════════════════════════════════════════════════════════


class TestAppendValidation:
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
            store.append(**_make_event_args(tenant_id=""))

    def test_missing_patient_id_raises(self, store):
        with pytest.raises(ValueError):
            store.append(**_make_event_args(patient_id=""))


# ═══════════════════════════════════════════════════════════════════════
# get
# ═══════════════════════════════════════════════════════════════════════


class TestGet:
    def test_returns_none_for_unknown_id(self, store):
        assert store.get("nonexistent-id") is None

    def test_returns_event_dict(self, store):
        eid = store.append(**_make_event_args())
        e = store.get(eid)
        assert isinstance(e, dict)
        assert "event_hash" in e
        assert "previous_hash" in e


# ═══════════════════════════════════════════════════════════════════════
# query — filtros básicos
# ═══════════════════════════════════════════════════════════════════════


class TestQuery:
    def test_empty_store_returns_empty(self, store):
        assert store.query(tenant_id=TENANT) == []

    def test_filters_by_tenant(self, store):
        store.append(**_make_event_args(tenant_id=TENANT))
        store.append(**_make_event_args(tenant_id=OTHER_TENANT))
        results = store.query(tenant_id=TENANT)
        assert len(results) == 1
        assert results[0]["tenant_id"] == TENANT

    def test_filters_by_patient(self, store):
        store.append(**_make_event_args(patient_id=PATIENT))
        store.append(**_make_event_args(patient_id=OTHER_PATIENT))
        results = store.query(tenant_id=TENANT, patient_id=PATIENT)
        assert len(results) == 1
        assert results[0]["patient_id"] == PATIENT

    def test_filters_by_event_type_exact(self, store):
        store.append(**_make_event_args(event_type="SCALE_APPLIED"))
        store.append(**_make_event_args(event_type="DIAGNOSIS_ADDED"))
        results = store.query(
            tenant_id=TENANT, event_types=["SCALE_APPLIED"]
        )
        assert len(results) == 1
        assert results[0]["event_type"] == "SCALE_APPLIED"

    def REDACTED(self, store):
        store.append(**_make_event_args(event_type="DIAGNOSIS_ADDED"))
        store.append(**_make_event_args(event_type="DIAGNOSIS_REMOVED"))
        store.append(**_make_event_args(event_type="SCALE_APPLIED"))
        results = store.query(
            tenant_id=TENANT, event_types=["DIAGNOSIS_*"]
        )
        assert len(results) == 2
        assert all(
            r["event_type"].startswith("DIAGNOSIS_") for r in results
        )

    def test_filters_by_aggregate(self, store):
        store.append(
            **_make_event_args(
                aggregate_type="scale", aggregate_id="scale-1"
            )
        )
        store.append(
            **_make_event_args(
                aggregate_type="medication", aggregate_id="med-1"
            )
        )
        results = store.query(
            tenant_id=TENANT, aggregate_type="scale"
        )
        assert len(results) == 1
        assert results[0]["aggregate_id"] == "scale-1"


# ═══════════════════════════════════════════════════════════════════════
# query — ordenação e range
# ═══════════════════════════════════════════════════════════════════════


class TestQueryOrdering:
    def test_default_order_is_sequence_asc(self, store):
        """Default order = sequence ASC (insertion order, canonical chain)."""
        store.append(
            **_make_event_args(
                event_type="A", event_datetime=DT_BASE + timedelta(hours=2)
            )
        )
        store.append(
            **_make_event_args(
                event_type="B", event_datetime=DT_BASE + timedelta(hours=1)
            )
        )
        store.append(
            **_make_event_args(
                event_type="C", event_datetime=DT_BASE
            )
        )
        results = store.query(tenant_id=TENANT)
        assert [r["event_type"] for r in results] == ["A", "B", "C"]

    def test_event_datetime_order_explicit(self, store):
        """event_datetime ASC deve ser explicitamente solicitado."""
        store.append(
            **_make_event_args(
                event_type="A", event_datetime=DT_BASE + timedelta(hours=2)
            )
        )
        store.append(
            **_make_event_args(
                event_type="B", event_datetime=DT_BASE + timedelta(hours=1)
            )
        )
        store.append(
            **_make_event_args(
                event_type="C", event_datetime=DT_BASE
            )
        )
        results = store.query(tenant_id=TENANT, order_by="event_datetime ASC")
        assert [r["event_type"] for r in results] == ["C", "B", "A"]

    def test_sequence_desc_order(self, store):
        store.append(**_make_event_args(event_type="A"))
        store.append(**_make_event_args(event_type="B"))
        results = store.query(tenant_id=TENANT, order_by="sequence DESC")
        assert [r["event_type"] for r in results] == ["B", "A"]

    def test_desc_order(self, store):
        store.append(
            **_make_event_args(
                event_type="A", event_datetime=DT_BASE
            )
        )
        store.append(
            **_make_event_args(
                event_type="B", event_datetime=DT_BASE + timedelta(hours=1)
            )
        )
        results = store.query(
            tenant_id=TENANT, order_by="event_datetime DESC"
        )
        assert [r["event_type"] for r in results] == ["B", "A"]


class TestQueryDateRange:
    def test_since_filter(self, store):
        store.append(
            **_make_event_args(
                event_type="old", event_datetime=DT_BASE - timedelta(days=10)
            )
        )
        store.append(
            **_make_event_args(
                event_type="new", event_datetime=DT_BASE
            )
        )
        results = store.query(tenant_id=TENANT, since=DT_BASE - timedelta(days=1))
        assert len(results) == 1
        assert results[0]["event_type"] == "new"

    def test_until_filter(self, store):
        store.append(
            **_make_event_args(
                event_type="old", event_datetime=DT_BASE - timedelta(days=10)
            )
        )
        store.append(
            **_make_event_args(
                event_type="new", event_datetime=DT_BASE
            )
        )
        results = store.query(tenant_id=TENANT, until=DT_BASE - timedelta(days=1))
        assert len(results) == 1
        assert results[0]["event_type"] == "old"

    def test_limit(self, store):
        for i in range(5):
            store.append(
                **_make_event_args(
                    event_type=f"E{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        results = store.query(tenant_id=TENANT, limit=2)
        assert len(results) == 2


# ═══════════════════════════════════════════════════════════════════════
# query — soft delete (excluído por padrão)
# ═══════════════════════════════════════════════════════════════════════


class TestSoftDelete:
    def test_excludes_deleted_by_default(self, store):
        eid = store.append(**_make_event_args())
        e = store.get(eid)
        e["deleted_at"] = "2026-07-15T12:00:00+00:00"
        results = store.query(tenant_id=TENANT)
        assert len(results) == 0

    def REDACTED(self, store):
        eid = store.append(**_make_event_args())
        e = store.get(eid)
        e["deleted_at"] = "2026-07-15T12:00:00+00:00"
        results = store.query(tenant_id=TENANT, include_deleted=True)
        assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════
# last_hash
# ═══════════════════════════════════════════════════════════════════════


class TestLastHash:
    def test_returns_none_for_empty_tenant(self, store):
        assert store.last_hash(TENANT) is None

    def test_returns_hash_of_last_event(self, store):
        e1 = store.append(**_make_event_args(event_type="A"))
        e2 = store.append(**_make_event_args(event_type="B"))
        last = store.get(e2)
        assert store.last_hash(TENANT) == last["event_hash"]

    def test_separates_by_tenant(self, store):
        store.append(**_make_event_args(tenant_id=TENANT, event_type="A"))
        store.append(**_make_event_args(tenant_id=OTHER_TENANT, event_type="B"))
        # Cada tenant tem seu próprio last_hash
        assert store.last_hash(TENANT) is not None
        assert store.last_hash(OTHER_TENANT) is not None
        assert store.last_hash(TENANT) != store.last_hash(OTHER_TENANT)


# ═══════════════════════════════════════════════════════════════════════
# verify_chain
# ═══════════════════════════════════════════════════════════════════════


class TestVerifyChain:
    def test_empty_chain_is_valid(self, store):
        assert store.verify_chain(TENANT) is True

    def test_valid_chain(self, store):
        for i in range(5):
            store.append(
                **_make_event_args(
                    event_type=f"E{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        assert store.verify_chain(TENANT) is True

    def test_tampered_chain_detected(self, store):
        e1 = store.append(**_make_event_args(event_type="A"))
        store.append(**_make_event_args(event_type="B"))
        e1_dict = store.get(e1)
        e1_dict["payload"]["total_score"] = 999  # tampering
        assert store.verify_chain(TENANT) is False

    def test_filtered_verify_chain(self, store):
        # Adiciona eventos para 2 pacientes
        for i in range(3):
            store.append(
                **_make_event_args(
                    patient_id=PATIENT,
                    event_type=f"P{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        for i in range(3):
            store.append(
                **_make_event_args(
                    patient_id=OTHER_PATIENT,
                    event_type=f"O{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        # A hash chain é PER-TENANT (não per-patient). O parâmetro patient_id
        # em verify_chain é informativo e filtra os eventos reportados, mas a
        # integridade da chain é sempre verificada no nível do tenant.
        # Aqui verificamos que a chain completa do tenant permanece íntegra
        # mesmo com múltiplos pacientes.
        assert store.verify_chain(TENANT) is True
        # verify_chain com patient_id ainda passa — usa a chain completa do tenant
        assert store.verify_chain(TENANT, patient_id=PATIENT) is True


# ═══════════════════════════════════════════════════════════════════════
# count
# ═══════════════════════════════════════════════════════════════════════


class TestCount:
    def test_empty_store_zero(self, store):
        assert store.count(TENANT) == 0

    def test_counts_all_events_for_tenant(self, store):
        for i in range(3):
            store.append(
                **_make_event_args(
                    event_type=f"E{i}",
                    event_datetime=DT_BASE + timedelta(minutes=i),
                )
            )
        store.append(**_make_event_args(tenant_id=OTHER_TENANT))
        assert store.count(TENANT) == 3

    def test_counts_per_patient(self, store):
        for i in range(2):
            store.append(
                **_make_event_args(patient_id=PATIENT, event_type=f"P{i}")
            )
        for i in range(3):
            store.append(
                **_make_event_args(patient_id=OTHER_PATIENT, event_type=f"O{i}")
            )
        assert store.count(TENANT, patient_id=PATIENT) == 2
        assert store.count(TENANT, patient_id=OTHER_PATIENT) == 3


# ═══════════════════════════════════════════════════════════════════════
# Thread safety
# ═══════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def REDACTED(self, store):
        results = []
        errors = []

        def worker(idx: int):
            try:
                eid = store.append(
                    **_make_event_args(
                        event_type=f"E{idx}",
                        event_datetime=DT_BASE + timedelta(seconds=idx),
                    )
                )
                results.append(eid)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(i,)) for i in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(results) == 20
        # Chain deve permanecer íntegra mesmo com concorrência
        assert store.verify_chain(TENANT) is True


# ═══════════════════════════════════════════════════════════════════════
# clear (helper de teste)
# ═══════════════════════════════════════════════════════════════════════


class TestClear:
    def test_clear_empties_store(self, store):
        store.append(**_make_event_args())
        store.clear()
        assert store.count(TENANT) == 0
        assert store.last_hash(TENANT) is None
