"""Testes dos relatórios financeiros (Fase 2)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import (
    db, Profissional, Paciente, Servico, Convenio,
    LancamentoFaturamento, Recebimento,
)


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        gestor = Profissional(nome="Gestor", usuario="gestor_rel", senha="x",
                              email="gestor_rel@teste.local", role="admin", status_cadastro="aprovado")
        secr = Profissional(nome="Secretária", usuario="secr_rel", senha="x",
                            email="secr_rel@teste.local", role="profissional",
                            status_cadastro="aprovado", perfil_acesso="administrativo")
        medico = Profissional(nome="Dr. Rep", usuario="dr_rep", senha="x",
                              email="dr_rep@teste.local", role="profissional",
                              status_cadastro="aprovado", perfil_acesso="assistencial")
        db.session.add_all([gestor, secr, medico])
        db.session.commit()

        pac = Paciente(nome="Maria", telefone="11999990000")
        db.session.add(pac)
        db.session.commit()
        serv = Servico(nome="Consulta", tipo="consulta", valor_particular=200.0)
        db.session.add(serv)
        db.session.commit()
        conv = Convenio(nome="Unimed", tipo="operadora")
        db.session.add(conv)
        db.session.commit()

        l1 = LancamentoFaturamento(paciente_id=pac.id, profissional_id=medico.id, servico_id=serv.id,
                                   convenio_id=None, valor_total=200.0, desconto=0.0, valor_receber=200.0,
                                   percentual_repasse=60.0, valor_repasse=120.0, status="pago",
                                   data_lancamento=datetime.utcnow() - timedelta(days=10))
        l2 = LancamentoFaturamento(paciente_id=pac.id, profissional_id=medico.id, servico_id=serv.id,
                                   convenio_id=conv.id, valor_total=150.0, desconto=0.0, valor_receber=150.0,
                                   percentual_repasse=60.0, valor_repasse=90.0, status="pendente",
                                   data_lancamento=datetime.utcnow() - timedelta(days=20))
        db.session.add_all([l1, l2])
        db.session.commit()
        db.session.add(Recebimento(lancamento_id=l1.id, valor=200.0))
        db.session.commit()

        app.config["TEST"] = {"gestor": gestor.id, "secr": secr.id, "medico": medico.id}
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app, key):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST"][key]))
    return {"Authorization": f"Bearer {token}"}


def test_resumo_gestor(client, app):
    r = client.get("/api/faturamento/relatorios/resumo", headers=_auth(client, app, "gestor"))
    assert r.status_code == 200, r.get_data()
    d = r.json
    assert d["lancado"] == 350.0
    assert d["recebido"] == 200.0
    assert d["repasse_due"] == 210.0  # 120 + 90
    assert d["repasse_pago"] == 120.0
    assert d["a_receber"] == 150.0


def test_receita_por_convenio(client, app):
    r = client.get("/api/faturamento/relatorios/receita?agrupar_por=convenio",
                   headers=_auth(client, app, "gestor"))
    assert r.status_code == 200
    itens = {i["grupo"]: i for i in r.json["itens"]}
    assert itens["Particular"]["lancado"] == 200.0
    assert itens["Unimed"]["lancado"] == 150.0


def test_repasse_por_profissional(client, app):
    r = client.get("/api/faturamento/relatorios/repasse", headers=_auth(client, app, "gestor"))
    assert r.status_code == 200
    item = r.json["itens"][0]
    assert item["profissional"] == "Dr. Rep"
    assert item["repasse_due"] == 210.0
    assert item["repasse_pago"] == 120.0


def test_inadimplencia(client, app):
    r = client.get("/api/faturamento/relatorios/inadimplencia", headers=_auth(client, app, "gestor"))
    assert r.status_code == 200
    assert r.json["total_pendente"] == 150.0
    assert r.json["quantidade"] == 1
    assert r.json["itens"][0]["dias_atraso"] == 20


def REDACTED(client, app):
    for key in ("secr", "medico"):
        r = client.get("/api/faturamento/relatorios/resumo", headers=_auth(client, app, key))
        assert r.status_code == 403, key
