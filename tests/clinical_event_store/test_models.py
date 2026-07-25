"""
Testes do Model SQLAlchemy do Clinical Event Engine.

Cobertura:
    - ClinicalEventModel: estrutura, to_dict
    - Tabela e índices
    - Round-trip via SQLAlchemy in-memory
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from araos.clinical.event_store.models import ClinicalEventModel
from araos.platform.tenant.models import Base


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════
# Estrutura da tabela
# ═══════════════════════════════════════════════════════════════════════


class TestTableStructure:
    def test_tablename(self):
        assert ClinicalEventModel.__tablename__ == "clinical_events"

    def test_pk_is_id(self, engine):
        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("clinical_events")
        assert pk["constrained_columns"] == ["id"]

    def test_required_columns_exist(self, engine):
        inspector = inspect(engine)
        cols = {c["name"] for c in inspector.get_columns("clinical_events")}
        required = {
            "id", "tenant_id", "patient_id", "event_type",
            "event_version", "event_datetime", "source_module",
            "payload", "event_metadata", "aggregate_type", "aggregate_id",
            "created_by", "created_by_user", "created_at", "updated_at",
            "deleted_at", "previous_hash", "event_hash", "sequence",
        }
        missing = required - cols
        assert not missing, f"missing columns: {missing}"

    def test_indexes_exist(self, engine):
        inspector = inspect(engine)
        indexes = {i["name"] for i in inspector.get_indexes("clinical_events")}
        required = {
            "REDACTED",
            "ix_clinical_events_event_type",
            "ix_clinical_events_aggregate",
            "ix_clinical_events_source_module",
            "ix_clinical_events_tenant_sequence",
            "ix_clinical_events_deleted_at",
        }
        missing = required - indexes
        assert not missing, f"missing indexes: {missing}"

    def REDACTED(self, engine):
        inspector = inspect(engine)
        uqs = inspector.get_unique_constraints("clinical_events")
        names = {u["name"] for u in uqs if u.get("name")}
        assert "uq_clinical_events_tenant_sequence" in names

    def test_tenant_id_fk(self, engine):
        inspector = inspect(engine)
        fks = inspector.get_foreign_keys("clinical_events")
        tenant_fks = [
            fk for fk in fks if "tenant_id" in fk["constrained_columns"]
        ]
        assert len(tenant_fks) == 1
        fk = tenant_fks[0]
        # FK aponta para a PK da tabela pai (id), não para uma coluna com mesmo nome
        assert fk["referred_table"] == "araos_organizations"
        assert fk["referred_columns"] == ["id"]
        assert fk["constrained_columns"] == ["tenant_id"]


# ═══════════════════════════════════════════════════════════════════════
# to_dict
# ═══════════════════════════════════════════════════════════════════════


class TestToDict:
    def _make(self) -> ClinicalEventModel:
        return ClinicalEventModel(
            id="ev-1",
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            event_version="1.0",
            event_datetime=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc),
            source_module="neurodevelopmental",
            payload={"scale_code": "GAD7", "total_score": 5},
            event_metadata={"correlation_id": "abc"},
            aggregate_type="scale",
            aggregate_id="scale-1",
            created_by="prof-1",
            created_by_user="user-1",
            created_at=datetime(2026, 7, 15, 10, 0, 5, tzinfo=timezone.utc),
            updated_at=None,
            deleted_at=None,
            previous_hash="0" * 64,
            event_hash="a" * 64,
            sequence=1,
        )

    def test_to_dict_returns_dict(self):
        e = self._make()
        d = e.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_includes_all_fields(self):
        e = self._make()
        d = e.to_dict()
        assert d["id"] == "ev-1"
        assert d["tenant_id"] == "t-1"
        assert d["patient_id"] == "p-1"
        assert d["event_type"] == "SCALE_APPLIED"
        assert d["event_version"] == "1.0"
        assert d["source_module"] == "neurodevelopmental"
        assert d["payload"] == {"scale_code": "GAD7", "total_score": 5}
        assert d["metadata"] == {"correlation_id": "abc"}  # renomeia event_metadata
        assert d["aggregate_type"] == "scale"
        assert d["aggregate_id"] == "scale-1"
        assert d["created_by"] == "prof-1"
        assert d["created_by_user"] == "user-1"

    def test_to_dict_serializes_datetimes(self):
        e = self._make()
        d = e.to_dict()
        assert isinstance(d["event_datetime"], str)
        assert "2026" in d["event_datetime"]

    def REDACTED(self):
        e = ClinicalEventModel(
            id="ev-2",
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            event_datetime=datetime.now(timezone.utc),
            source_module="neurodevelopmental",
            payload={},
            event_metadata={},
            event_hash="x" * 64,
            sequence=42,
        )
        d = e.to_dict()
        assert d["aggregate_type"] is None
        assert d["aggregate_id"] is None
        assert d["updated_at"] is None
        assert d["deleted_at"] is None
        assert d["previous_hash"] is None
        assert d["sequence"] == 42


# ═══════════════════════════════════════════════════════════════════════
# Round-trip SQLAlchemy
# ═══════════════════════════════════════════════════════════════════════


class TestRoundTrip:
    def test_persist_and_retrieve(self, db_session):
        e = ClinicalEventModel(
            id="ev-rt-1",
            tenant_id="t-1",
            patient_id="p-1",
            event_type="DIAGNOSIS_ADDED",
            event_datetime=datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc),
            source_module="core",
            payload={"cid10": "F84.0", "label": "TEA"},
            event_metadata={},
            event_hash="abc123" * 11 + "abcd",  # 64 chars
            sequence=1,
        )
        db_session.add(e)
        db_session.commit()

        retrieved = (
            db_session.query(ClinicalEventModel)
            .filter(ClinicalEventModel.id == "ev-rt-1")
            .one()
        )
        assert retrieved.event_type == "DIAGNOSIS_ADDED"
        assert retrieved.payload == {"cid10": "F84.0", "label": "TEA"}
        assert retrieved.event_hash.startswith("abc123")
        assert retrieved.sequence == 1

    def test_json_columns_accept_dicts(self, db_session):
        e = ClinicalEventModel(
            id="ev-json-1",
            tenant_id="t-1",
            patient_id="p-1",
            event_type="SCALE_APPLIED",
            event_datetime=datetime(2026, 7, 15, tzinfo=timezone.utc),
            source_module="neurodevelopmental",
            payload={"nested": {"key": [1, 2, 3]}},
            event_metadata={"tags": ["a", "b"]},
            event_hash="x" * 64,
            sequence=2,
        )
        db_session.add(e)
        db_session.commit()
        retrieved = (
            db_session.query(ClinicalEventModel)
            .filter(ClinicalEventModel.id == "ev-json-1")
            .one()
        )
        assert retrieved.payload == {"nested": {"key": [1, 2, 3]}}
        assert retrieved.event_metadata == {"tags": ["a", "b"]}
        assert retrieved.sequence == 2
