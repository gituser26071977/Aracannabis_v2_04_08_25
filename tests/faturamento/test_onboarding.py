"""Testes do onboarding de pacientes (cadastro admin + fila de pendências)."""

from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Paciente


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Profissional(
            nome="Admin", usuario="adm", senha="x",
            email="adm@teste.local", role="admin", status_cadastro="aprovado",
        )
        secretaria = Profissional(
            nome="Secretária", usuario="sec", senha="x",
            email="sec@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="administrativo",
        )
        medico = Profissional(
            nome="Dr. Clínico", usuario="dr", senha="x",
            email="dr@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="assistencial",
        )
        db.session.add_all([admin, secretaria, medico])
        db.session.commit()

        existente = Paciente(nome="Maria Duplicada", cpf="11122233344", telefone="11999990000")
        db.session.add(existente)
        db.session.commit()

        app.config["TEST"] = {"admin": admin.id, "sec": secretaria.id, "medico": medico.id, "existente": existente.id}
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app, key: str):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST"][key]))
    return {"Authorization": f"Bearer {token}"}


def REDACTED(client, app):
    r = client.post("/api/onboarding/paciente", json={
        "nome": "João Novo", "telefone": "(11) 98888-7777", "queixa": "Dor",
    }, headers=_auth(client, app, "sec"))
    assert r.status_code == 201, r.get_data()
    assert r.json["resultado"]["status"] == "criado"
    assert r.json["resultado"]["paciente_id"]


def test_duplicado_vira_pendencia(client, app):
    r = client.post("/api/onboarding/paciente", json={
        "nome": "Maria Duplicada", "cpf": "111.222.333-44", "telefone": "11999990000",
        "queixa": "Nova queixa",
    }, headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    resultado = r.json["resultado"]
    assert resultado["status"] == "pendente"
    assert resultado["motivo"] == "duplicado"
    assert resultado["duplicados"]

    # fila de pendências
    r = client.get("/api/onboarding/pendentes", headers=_auth(client, app, "sec"))
    assert r.json["total"] == 1

    pendente_id = resultado["onboarding_id"]
    # confirmar usando o existente
    r = client.post(f"/api/onboarding/pendentes/{pendente_id}/confirmar",
                    json={"acao": "usar_existente"}, headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    assert r.json["resultado"]["usado_existente"] is True
    assert r.json["resultado"]["paciente_id"] == app.config["TEST"]["existente"]

    # fila vazia depois
    r = client.get("/api/onboarding/pendentes", headers=_auth(client, app, "sec"))
    assert r.json["total"] == 0


def REDACTED(client, app):
    r = client.post("/api/onboarding/paciente", json={
        "telefone": "11977776666", "queixa": "Só o telefone"
    }, headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    assert r.json["resultado"]["motivo"] == "dados_incompletos"

    pendente_id = r.json["resultado"]["onboarding_id"]
    # confirmar preenchendo nome
    r = client.post(f"/api/onboarding/pendentes/{pendente_id}/confirmar",
                    json={"dados": {"nome": "Paciente Completo", "telefone": "11977776666"}},
                    headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    assert r.json["resultado"]["usado_existente"] is False
    assert r.json["resultado"]["paciente_id"]


def test_descartar_pendencia(client, app):
    r = client.post("/api/onboarding/paciente", json={
        "nome": "Descartável", "cpf": "11122233344",
    }, headers=_auth(client, app, "sec"))
    pendente_id = r.json["resultado"]["onboarding_id"]
    r = client.post(f"/api/onboarding/pendentes/{pendente_id}/descartar", json={},
                    headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    r = client.get("/api/onboarding/pendentes", headers=_auth(client, app, "sec"))
    assert r.json["total"] == 0


def REDACTED(client, app):
    r = client.get("/api/onboarding/pendentes", headers=_auth(client, app, "medico"))
    assert r.status_code == 403


def test_sugestao_heuristica_de_texto(client, app):
    r = client.post("/api/onboarding/paciente/sugerir",
                    json={"texto": "Maria Souza, telefone 11955554444, cpf 12345678901, dor nas costas"},
                    headers=_auth(client, app, "sec"))
    assert r.status_code == 200
    s = r.json["sugestao"]
    assert s.get("telefone") == "11955554444" or s.get("cpf") == "12345678901"
