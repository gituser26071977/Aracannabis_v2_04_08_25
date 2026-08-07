"""Testes da certificação digital (Bird ID/CESS) — config e início de assinatura."""

from __future__ import annotations

import io

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, SignatureTransaction


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        medico = Profissional(
            nome="Dr. Assina", usuario="dr_assina", senha="x",
            email="dr_assina@teste.local", role="profissional", status_cadastro="aprovado",
            crm="CRM123", uf_crm="SE", conselho_tipo="CRM", perfil_acesso="assistencial",
        )
        db.session.add(medico)
        db.session.commit()
        app.config["TEST"] = {"medico": medico.id}
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST"]["medico"]))
    return {"Authorization": f"Bearer {token}"}


def test_salvar_config(client, app):
    r = client.post("/api/certificacao-digital/config", json={
        "provedor": "birdid", "client_id": "cli-1", "client_secret": "sec-1",
        "certificate_alias": "CERTIF:123",
    }, headers=_auth(client, app))
    assert r.status_code == 200, r.get_data()
    assert r.json["config"]["certificate_alias"] == "CERTIF:123"
    assert r.json["config"]["status"] == "pendente"

    r = client.get("/api/certificacao-digital/config", headers=_auth(client, app))
    assert r.status_code == 200
    assert r.json["config"]["client_secret_set"] is True


def test_iniciar_assinatura(client, app, monkeypatch):
    from routes import certificacao_digital as routes_mod

    def fake_iniciar(pdf_bytes, *, provedor, profissional_id, nome_documento, motivo):
        assert pdf_bytes == b"%PDF-fake"
        tx = SignatureTransaction(config_id=1, tcn="tcn-test-123", status="aguardando")
        return tx

    monkeypatch.setattr(routes_mod, "iniciar_assinatura", fake_iniciar)

    client.post("/api/certificacao-digital/config", json={
        "provedor": "birdid", "client_id": "cli-1", "client_secret": "sec-1",
        "certificate_alias": "CERTIF:123",
    }, headers=_auth(client, app))

    r = client.post(
        "/api/certificacao-digital/assinar",
        data={"file": (io.BytesIO(b"%PDF-fake"), "laudo.pdf")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    assert r.status_code == 200, r.get_data()
    assert r.json["tcn"] == "tcn-test-123"
    assert r.json["status"] == "aguardando"


def test_assinar_sem_config(client, app, monkeypatch):
    from routes import certificacao_digital as routes_mod

    def fake_iniciar(*args, **kwargs):
        raise ValueError("certificação digital não configurada para este profissional")

    monkeypatch.setattr(routes_mod, "iniciar_assinatura", fake_iniciar)
    r = client.post(
        "/api/certificacao-digital/assinar",
        data={"file": (io.BytesIO(b"%PDF-fake"), "laudo.pdf")},
        content_type="multipart/form-data",
        headers=_auth(client, app),
    )
    assert r.status_code == 400


def REDACTED(client, app):
    r = client.get("/api/certificacao-digital/assinatura/tcn-inexistente",
                   headers=_auth(client, app))
    assert r.status_code == 404
