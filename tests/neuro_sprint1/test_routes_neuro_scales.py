"""
Testes da rota Flask `routes/neuro_scales.py`.

Usa Flask test client + SQLite in-memory + JWT mock.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.platform.tenant.models import Base
from araos.specialties.neurodevelopmental.db_models import NeuroScaleResponseModel
from araos.specialties.neurodevelopmental.scales.builtins import _register_all
from araos.specialties.neurodevelopmental.scales.store import ScaleResponseStore
from routes.neuro_scales import neuro_scales_bp


# ─── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def app():
    """Flask app mínimo com blueprint registrado + SQLite in-memory."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-key"

    JWTManager(app)

    # Banco SQLite in-memory compartilhado via conexão estática
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Injeta session no app config para as rotas usarem via `db.session`
    app.config["DB_SESSION"] = session
    app.config["DB_ENGINE"] = engine

    # Monkeypatch: faz `from models import db` funcionar retornando nossa session
    import sys
    import types

    fake_models = types.ModuleType("models")
    fake_models.db = MagicMock()
    fake_models.db.session = session
    sys.modules["models"] = fake_models

    app.register_blueprint(neuro_scales_bp)
    _register_all()

    yield app

    session.close()
    engine.dispose()
    if "models" in sys.modules:
        del sys.modules["models"]


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header():
    """Header de autenticação JWT válido para os testes."""
    with patch("flask_jwt_extended.view_decorators.verify_jwt_in_request") as mock:
        # Mock do JWT: retorna identity como dict com tenant_id
        from flask_jwt_extended import create_access_token

        token = create_access_token(
            identity={"user_id": "actor-1", "tenant_id": "tenant-1"}
        )
        yield {"Authorization": f"Bearer {token}"}


def _insert_response(
    session, tenant_id="tenant-1", patient_id="p1", scale_code="GAD7", rid=None
):
    import uuid as _uuid

    row = NeuroScaleResponseModel(
        id=rid or f"resp-{_uuid.uuid4().hex[:12]}",
        tenant_id=tenant_id,
        patient_id=patient_id,
        scale_code=scale_code,
        scale_version="1.0",
        raw_responses={f"q{i}": 1 for i in range(1, 8)},
        computed_scores={"total": 7.0},
        interpretation={"total": {"band": "leve", "label_pt": "Leve"}},
        extra_metadata={},
        applied_at=datetime.now(timezone.utc),
        applied_by="actor-1",
        source="ui",
        status="final",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


# ─── /catalog ──────────────────────────────────────────────────────


def test_catalog_returns_all_scales(client, auth_header):
    res = client.get("/api/neuro/scales/catalog", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()
    assert "scales" in data
    assert data["total"] >= 2  # GAD7 + PHQ9
    codes = {s["code"] for s in data["scales"]}
    assert "GAD7" in codes
    assert "PHQ9" in codes


def test_catalog_filters_by_age(client, auth_header):
    res = client.get(
        "/api/neuro/scales/catalog?age_months=120", headers=auth_header  # 10 anos
    )
    assert res.status_code == 200
    data = res.get_json()
    # PHQ9 ≥144, GAD7 ≥168 → nenhuma aplicável aos 10 anos
    codes = {s["code"] for s in data["scales"]}
    assert "GAD7" not in codes
    assert "PHQ9" not in codes


def REDACTED(client, auth_header):
    res = client.get(
        "/api/neuro/scales/catalog?age_months=abc", headers=auth_header
    )
    assert res.status_code == 400


def test_catalog_requires_jwt(client):
    res = client.get("/api/neuro/scales/catalog")
    assert res.status_code == 401


# ─── GET /<code> ───────────────────────────────────────────────────


def REDACTED(client, auth_header):
    res = client.get("/api/neuro/scales/GAD7", headers=auth_header)
    assert res.status_code == 200
    data = res.get_json()
    assert data["code"] == "GAD7"
    assert data["name"] == "Generalized Anxiety Disorder 7-item"
    assert "json_schema" in data
    assert "properties" in data["json_schema"]


def test_get_unknown_scale_returns_404(client, auth_header):
    res = client.get("/api/neuro/scales/UNKNOWN", headers=auth_header)
    assert res.status_code == 404
    assert res.get_json()["error"] == "scale_not_found"


def test_get_specific_version(client, auth_header):
    res = client.get("/api/neuro/scales/PHQ9?version=1.0", headers=auth_header)
    assert res.status_code == 200


# ─── POST /<code>/apply ───────────────────────────────────────────


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/GAD7/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={
            "patient_id": "patient-abc",
            "raw_responses": {f"q{i}": 2 for i in range(1, 8)},
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["scale_code"] == "GAD7"
    assert data["tenant_id"] == "tenant-1"
    assert data["computed_scores"]["total"] == 14.0
    assert data["interpretation"]["total"]["band"] == "moderado"


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/GAD7/apply",
        headers=auth_header,  # sem X-Association-ID
        json={"patient_id": "p1", "raw_responses": {"q1": 1}},
    )
    assert res.status_code == 400
    assert res.get_json()["error"] == "tenant_required"


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/GAD7/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={"raw_responses": {"q1": 1}},
    )
    assert res.status_code == 400


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/GAD7/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={
            "patient_id": "p1",
            "raw_responses": {"q1": 99},  # fora do range
        },
    )
    assert res.status_code == 400
    assert res.get_json()["error"] == "validation_error"


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/UNKNOWN/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={"patient_id": "p1", "raw_responses": {"q1": 1}},
    )
    assert res.status_code == 404


def REDACTED(client, auth_header):
    responses = {f"q{i}": 0 for i in range(1, 9)} | {"q9": 2}
    res = client.post(
        "/api/neuro/scales/PHQ9/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={"patient_id": "p1", "raw_responses": responses},
    )
    assert res.status_code == 201
    data = res.get_json()
    rec = data["interpretation"]["total"]["recommendation"]
    assert "ATENÇÃO" in rec


def REDACTED(client, auth_header):
    res = client.post(
        "/api/neuro/scales/PHQ9/apply",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
        json={
            "patient_id": "p1",
            "raw_responses": {f"q{i}": 1 for i in range(1, 10)},
            "metadata": {"aplicador": "Dr. Teste", "contexto": "rotina"},
            "source": "ai",
            "status": "draft",
        },
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["source"] == "ai"
    assert data["status"] == "draft"


# ─── GET /responses/<id> ──────────────────────────────────────────


def test_get_response_by_id(client, auth_header, app):
    session = app.config["DB_SESSION"]
    row = _insert_response(session, rid="resp-test")
    res = client.get(
        "/api/neuro/scales/responses/resp-test",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["id"] == "resp-test"
    assert data["scale_code"] == "GAD7"


def test_get_response_not_found(client, auth_header):
    res = client.get(
        "/api/neuro/scales/responses/missing",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 404


def REDACTED(client, auth_header, app):
    session = app.config["DB_SESSION"]
    row = _insert_response(session, tenant_id="tenant-A")
    res = client.get(
        f"/api/neuro/scales/responses/{row.id}",
        headers={**auth_header, "X-Association-ID": "tenant-B"},
    )
    assert res.status_code == 404  # tenant isolation


# ─── GET /responses ──────────────────────────────────────────────


def test_list_responses_for_patient(client, auth_header, app):
    session = app.config["DB_SESSION"]
    _insert_response(session, patient_id="p1", scale_code="GAD7")
    res = client.get(
        "/api/neuro/scales/responses?patient_id=p1",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] >= 1
    assert any(r["scale_code"] == "GAD7" for r in data["responses"])


def REDACTED(client, auth_header, app):
    session = app.config["DB_SESSION"]
    _insert_response(session, patient_id="p1", scale_code="GAD7")
    _insert_response(session, patient_id="p1", scale_code="PHQ9")
    res = client.get(
        "/api/neuro/scales/responses?patient_id=p1&scale_code=PHQ9",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 1
    assert data["responses"][0]["scale_code"] == "PHQ9"


def REDACTED(client, auth_header):
    res = client.get(
        "/api/neuro/scales/responses",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 400


def test_list_responses_invalid_limit(client, auth_header):
    res = client.get(
        "/api/neuro/scales/responses?patient_id=p1&limit=abc",
        headers={**auth_header, "X-Association-ID": "tenant-1"},
    )
    assert res.status_code == 400