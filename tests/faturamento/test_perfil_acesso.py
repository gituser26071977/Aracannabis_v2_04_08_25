"""Testes do controle de acesso por perfil (Assistencial × Administrativo × Solo)."""

from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        # perfil efetivo NÃO derivado (explícito) para cada cenário
        prof_assist = Profissional(
            nome="Dr. Clínico", usuario="dr_clin", senha="x",
            email="dr_clin@teste.local", role="profissional",
            status_cadastro="aprovado", perfil_acesso="assistencial",
        )
        prof_admin = Profissional(
            nome="Secretária", usuario="secr", senha="x",
            email="secr@teste.local", role="profissional",
            status_cadastro="aprovado", perfil_acesso="administrativo",
        )
        solo = Profissional(
            nome="Dr. Solo", usuario="dr_solo", senha="x",
            email="dr_solo@teste.local", role="profissional",
            status_cadastro="aprovado", perfil_acesso="solo",
        )
        admin = Profissional(
            nome="Admin", usuario="adm", senha="x",
            email="adm@teste.local", role="admin", status_cadastro="aprovado",
        )
        db.session.add_all([prof_assist, prof_admin, solo, admin])
        db.session.commit()
        app.config["TEST_IDS"] = {
            "assist": prof_assist.id, "admin2": prof_admin.id,
            "solo": solo.id, "admin": admin.id,
        }
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app, key: str):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST_IDS"][key]))
    return {"Authorization": f"Bearer {token}"}


def test_resolver_perfil(app):
    from services.perfil_acesso import resolver_perfil, PERFIL_ASSISTENCIAL, PERFIL_ADMINISTRATIVO, PERFIL_SOLO

    with app.app_context():
        assert resolver_perfil(Profissional.query.get(app.config["TEST_IDS"]["assist"])) == PERFIL_ASSISTENCIAL
        assert resolver_perfil(Profissional.query.get(app.config["TEST_IDS"]["admin2"])) == PERFIL_ADMINISTRATIVO
        assert resolver_perfil(Profissional.query.get(app.config["TEST_IDS"]["solo"])) == PERFIL_SOLO
        # admin sem perfil explícito → solo (pleno)
        assert resolver_perfil(Profissional.query.get(app.config["TEST_IDS"]["admin"])) == PERFIL_SOLO


def test_acesso_por_area(client, app):
    # assistencial NÃO acessa financeiro (faturamento = administrativo)
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "assist"))
    assert r.status_code == 403

    # assistencial acessa prontuário (pacientes = assistencial)
    r = client.get("/api/pacientes", headers=_auth(client, app, "assist"))
    assert r.status_code != 403  # pode ser 200/401 por outros motivos, mas não bloqueio de perfil

    # administrativo acessa faturamento
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "admin2"))
    assert r.status_code != 403

    # administrativo NÃO acessa prontuário
    r = client.get("/api/pacientes", headers=_auth(client, app, "admin2"))
    assert r.status_code == 403

    # solo acessa ambos
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "solo"))
    assert r.status_code != 403
    r = client.get("/api/pacientes", headers=_auth(client, app, "solo"))
    assert r.status_code != 403

    # admin (sem perfil explícito) vira solo → pleno
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "admin"))
    assert r.status_code != 403
    r = client.get("/api/pacientes", headers=_auth(client, app, "admin"))
    assert r.status_code != 403


def REDACTED(client):
    # sem token → before_request ignora (rota jwt_required retorna 401 depois)
    r = client.get("/api/faturamento/servicos")
    assert r.status_code in (401, 200)  # nunca 403 por perfil
