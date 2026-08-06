"""Testes do upload de documentos no onboarding (OCR mockado)."""

from __future__ import annotations

import io

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, OnboardingDocumento


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        gestor = Profissional(
            nome="Gestor", usuario="gestor_doc", senha="x",
            email="gestor_doc@teste.local", role="admin", status_cadastro="aprovado",
        )
        db.session.add(gestor)
        db.session.commit()
        app.config["TEST"] = {"gestor": gestor.id}
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST"]["gestor"]))
    return {"Authorization": f"Bearer {token}"}


def _mock_ocr(monkeypatch):
    """Substitui o OCR por um resultado determinístico."""
    from services import onboarding_pacientes as service_mod

    def fake(arquivo_bytes, filename):
        return {
            "sugestao": {"nome": "Maria Documento", "telefone": "11988887777", "queixa": "Dor"},
            "texto_extraido": "Maria Documento - Dor nas costas",
            "confianca": 0.85,
        }

    monkeypatch.setattr(service_mod, "sugerir_dados_de_documento", fake)


def REDACTED(client, app, monkeypatch):
    _mock_ocr(monkeypatch)
    r = client.post(
        "/api/onboarding/paciente/upload",
        data={"file": (io.BytesIO(b"fake-png-bytes"), "documento.png")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    assert r.status_code == 200, r.get_data()
    d = r.json
    assert d["sugestao"]["nome"] == "Maria Documento"
    assert d["texto_extraido"] == "Maria Documento - Dor nas costas"
    assert d["documento_id"]

    with app.app_context():
        doc = OnboardingDocumento.query.get(d["documento_id"])
        assert doc is not None
        assert doc.paciente_id is None  # ainda não vinculado


def test_upload_formato_invalido(client, app):
    r = client.post(
        "/api/onboarding/paciente/upload",
        data={"file": (io.BytesIO(b"x"), "doc.exe")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    assert r.status_code == 400


def REDACTED(client, app, monkeypatch):
    _mock_ocr(monkeypatch)
    r = client.post(
        "/api/onboarding/paciente/upload",
        data={"file": (io.BytesIO(b"fake-png-bytes"), "documento.png")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    doc_id = r.json["documento_id"]

    r = client.post("/api/onboarding/paciente", json={
        "nome": "Maria Documento",
        "telefone": "11988887777",
        "documento_id": doc_id,
    }, headers=_auth(client, app))
    assert r.status_code == 201, r.get_data()
    pac_id = r.json["resultado"]["paciente_id"]

    with app.app_context():
        doc = OnboardingDocumento.query.get(doc_id)
        assert doc.paciente_id == pac_id


def test_download_documento(client, app, monkeypatch):
    _mock_ocr(monkeypatch)
    r = client.post(
        "/api/onboarding/paciente/upload",
        data={"file": (io.BytesIO(b"fake-png-bytes"), "documento.png")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    doc_id = r.json["documento_id"]
    r = client.get(f"/api/onboarding/documentos/{doc_id}/arquivo", headers=_auth(client, app))
    assert r.status_code == 200
