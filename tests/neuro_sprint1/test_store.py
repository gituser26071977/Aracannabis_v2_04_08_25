"""
Testes do `store.py` (ScaleResponseStore).

Usa SQLite in-memory + SQLAlchemy core para isolar do app Flask.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.platform.tenant.models import Base
from araos.specialties.neurodevelopmental.db_models import NeuroScaleResponseModel
from araos.specialties.neurodevelopmental.scales.builtins import _register_all
from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
from araos.specialties.neurodevelopmental.scales.store import (
    ScaleResponseStore,
    StoredScaleResponse,
)


@pytest.fixture
def db_session():
    """SQLite in-memory + SQLAlchemy Core para testes isolados."""
    _register_all()
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _make_response(
    session,
    tenant_id: str = "tenant-1",
    patient_id: str = "patient-1",
    scale_code: str = "GAD7",
    applied_at: Optional[datetime] = None,
    **kwargs: Any,
) -> NeuroScaleResponseModel:
    """Helper para inserir resposta bruta direto via SQLAlchemy."""
    row = NeuroScaleResponseModel(
        id="resp-" + str(kwargs.get("seq", 1)),
        tenant_id=tenant_id,
        patient_id=patient_id,
        scale_code=scale_code,
        scale_version="1.0",
        raw_responses={"q1": 1, "q2": 1, "q3": 1, "q4": 1, "q5": 1, "q6": 1, "q7": 1},
        computed_scores={"total": 7.0},
        interpretation={
            "total": {"band": "leve", "label_pt": "Ansiedade leve"}
        },
        extra_metadata={},
        applied_at=applied_at or datetime.now(timezone.utc),
        applied_by="actor-1",
        source=kwargs.get("source", "ui"),
        status=kwargs.get("status", "final"),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


# ─── save ──────────────────────────────────────────────────────────


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    stored = store.save(
        tenant_id="t1",
        patient_id="p1",
        scale_code="GAD7",
        raw_responses={f"q{i}": 2 for i in range(1, 8)},
    )
    assert isinstance(stored, StoredScaleResponse)
    assert stored.id != ""
    assert stored.tenant_id == "t1"
    assert stored.patient_id == "p1"
    assert stored.scale_code == "GAD7"
    assert stored.scale_version == "1.0"
    assert stored.computed_scores["total"] == 14.0
    assert stored.interpretation["total"]["band"] == "moderado"


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    stored = store.save(
        tenant_id="t1",
        patient_id="p1",
        scale_code="PHQ9",
        raw_responses={f"q{i}": 1 for i in range(1, 10)},
        scale_version="1.0",
    )
    assert stored.scale_version == "1.0"


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    with pytest.raises(Exception):
        store.save(
            tenant_id="t1",
            patient_id="p1",
            scale_code="GAD7",
            raw_responses={"q1": "not_an_int"},
        )


def REDACTED(db_session):
    """validate=False pula a validação JSON Schema no runner.run()
    (mas o score_function ainda valida o domínio e lança ValueError
    se receber valores fora do range esperado)."""
    store = ScaleResponseStore(db_session)

    # Happy path com validate=False: 7 itens válidos → soma 7
    stored = store.save(
        tenant_id="t1",
        patient_id="p1",
        scale_code="GAD7",
        raw_responses={f"q{i}": 1 for i in range(1, 8)},
        validate=False,
    )
    assert stored.computed_scores["total"] == 7.0

    # Score function ainda rejeita domínio fora do range
    with pytest.raises(ValueError, match="inteiro 0-3"):
        store.save(
            tenant_id="t1",
            patient_id="p2",
            scale_code="GAD7",
            raw_responses={
                "q1": 99, "q2": 1, "q3": 1,
                "q4": 1, "q5": 1, "q6": 1, "q7": 1,
            },
            validate=False,
        )


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    with pytest.raises(Exception):  # ScaleNotFoundError
        store.save(
            tenant_id="t1",
            patient_id="p1",
            scale_code="UNKNOWN_SCALE",
            raw_responses={},
        )


def test_save_sets_actor_and_metadata(db_session):
    store = ScaleResponseStore(db_session)
    stored = store.save(
        tenant_id="t1",
        patient_id="p1",
        scale_code="PHQ9",
        raw_responses={f"q{i}": 0 for i in range(1, 10)},
        applied_by="prof-123",
        source="ai",
        status="draft",
        metadata={"context": "test"},
    )
    assert stored.applied_by == "prof-123"
    assert stored.source == "ai"
    assert stored.status == "draft"
    assert stored.metadata["context"] == "test"


# ─── get ───────────────────────────────────────────────────────────


def test_get_returns_stored_response(db_session):
    _make_response(db_session, seq=1)
    store = ScaleResponseStore(db_session)
    stored = store.get(response_id="resp-1", tenant_id="tenant-1")
    assert stored is not None
    assert stored.id == "resp-1"
    assert stored.scale_code == "GAD7"


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    stored = store.get(response_id="missing", tenant_id="tenant-1")
    assert stored is None


def test_get_is_tenant_scoped(db_session):
    _make_response(db_session, tenant_id="tenant-A", seq=1)
    store = ScaleResponseStore(db_session)
    stored = store.get(response_id="resp-1", tenant_id="tenant-B")
    assert stored is None  # tenant B não pode ver tenant A


# ─── list_for_patient ─────────────────────────────────────────────


def REDACTED(db_session):
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    _make_response(db_session, seq=1, applied_at=now - timedelta(days=2))
    _make_response(db_session, seq=2, applied_at=now)
    _make_response(db_session, seq=3, applied_at=now - timedelta(days=1))

    store = ScaleResponseStore(db_session)
    rows = store.list_for_patient(tenant_id="tenant-1", patient_id="patient-1")
    assert len(rows) == 3
    assert rows[0].id == "resp-2"  # mais recente primeiro
    assert rows[1].id == "resp-3"
    assert rows[2].id == "resp-1"


def REDACTED(db_session):
    _make_response(db_session, seq=1, scale_code="GAD7")
    _make_response(db_session, seq=2, scale_code="PHQ9")
    store = ScaleResponseStore(db_session)
    gad7 = store.list_for_patient(
        tenant_id="tenant-1", patient_id="patient-1", scale_code="GAD7"
    )
    assert len(gad7) == 1
    assert gad7[0].scale_code == "GAD7"


def REDACTED(db_session):
    _make_response(db_session, tenant_id="tenant-A", seq=1, patient_id="p1")
    _make_response(db_session, tenant_id="tenant-B", seq=2, patient_id="p1")
    store = ScaleResponseStore(db_session)
    rows_a = store.list_for_patient(tenant_id="tenant-A", patient_id="p1")
    rows_b = store.list_for_patient(tenant_id="tenant-B", patient_id="p1")
    assert len(rows_a) == 1
    assert len(rows_b) == 1
    assert rows_a[0].id != rows_b[0].id


def REDACTED(db_session):
    for i in range(1, 6):
        _make_response(db_session, seq=i)
    store = ScaleResponseStore(db_session)
    rows = store.list_for_patient(
        tenant_id="tenant-1", patient_id="patient-1", limit=3
    )
    assert len(rows) == 3


# ─── latest_for_patient ───────────────────────────────────────────


def REDACTED(db_session):
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    _make_response(db_session, seq=1, applied_at=now - timedelta(days=10))
    _make_response(db_session, seq=2, applied_at=now)
    _make_response(db_session, seq=3, applied_at=now - timedelta(days=5))

    store = ScaleResponseStore(db_session)
    latest = store.latest_for_patient(
        tenant_id="tenant-1", patient_id="patient-1", scale_code="GAD7"
    )
    assert latest is not None
    assert latest.id == "resp-2"


def REDACTED(db_session):
    store = ScaleResponseStore(db_session)
    latest = store.latest_for_patient(
        tenant_id="tenant-1", patient_id="empty", scale_code="GAD7"
    )
    assert latest is None


# ─── count_for_patient ─────────────────────────────────────────────


def REDACTED(db_session):
    _make_response(db_session, seq=1, scale_code="GAD7")
    _make_response(db_session, seq=2, scale_code="GAD7")
    _make_response(db_session, seq=3, scale_code="PHQ9")
    store = ScaleResponseStore(db_session)
    total = store.count_for_patient(tenant_id="tenant-1", patient_id="patient-1")
    assert total == 3
    gad7 = store.count_for_patient(
        tenant_id="tenant-1", patient_id="patient-1", scale_code="GAD7"
    )
    assert gad7 == 2


# ─── to_dict ──────────────────────────────────────────────────────


def REDACTED():
    stored = StoredScaleResponse(
        id="r1",
        tenant_id="t1",
        patient_id="p1",
        scale_code="GAD7",
        scale_version="1.0",
        raw_responses={"q1": 1},
        computed_scores={"total": 1.0},
        interpretation={"total": {"band": "minimo"}},
        metadata={"x": 1},
        applied_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        applied_by="actor-1",
        source="ui",
        status="final",
    )
    d = stored.to_dict()
    assert d["id"] == "r1"
    assert d["scale_code"] == "GAD7"
    assert d["applied_at"] == "2026-01-01T00:00:00+00:00"