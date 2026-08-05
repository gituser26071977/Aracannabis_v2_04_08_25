"""Testes LGPD — exportação e anonimização de dados do paciente."""

from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Paciente, PreConsulta, Consulta, LancamentoFaturamento, Servico


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Profissional(
            nome="Admin", usuario="adm", senha="x",
            email="adm@teste.local", role="admin", status_cadastro="aprovado",
        )
        db.session.add(admin)
        db.session.commit()

        pac = Paciente(nome="Maria LGPD", cpf="11122233344", telefone="11999990000", email="maria@teste.local")
        db.session.add(pac)
        db.session.commit()

        db.session.add(PreConsulta(paciente_id=pac.id, queixa_principal="Insônia", intake_interview_id="iv-lgpd"))
        serv = Servico(nome="Consulta", tipo="consulta", valor_particular=200.0)
        db.session.add(serv)
        db.session.commit()
        db.session.add(LancamentoFaturamento(
            paciente_id=pac.id, profissional_id=admin.id, servico_id=serv.id,
            valor_total=200.0, desconto=0.0, valor_receber=200.0,
            percentual_repasse=100.0, valor_repasse=200.0, status="pago",
        ))
        db.session.commit()

        app.config["TEST"] = {"admin": admin.id, "pac": pac.id}
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST"]["admin"]))
    return {"Authorization": f"Bearer {token}"}


def test_exporta_dados_do_paciente(client, app):
    r = client.get(f"/api/lgpd/exportar/{app.config['TEST']['pac']}", headers=_auth(client, app))
    assert r.status_code == 200, r.get_data()
    d = r.json
    assert d["paciente"]["nome"] == "Maria LGPD"
    assert d["pre_consultas"][0]["queixa_principal"] == "Insônia"
    assert d["faturamento"][0]["valor_receber"] == 200.0


def test_anonimiza_paciente(client, app):
    pac_id = app.config["TEST"]["pac"]
    # exige confirmação
    r = client.post(f"/api/lgpd/apagar/{pac_id}", json={}, headers=_auth(client, app))
    assert r.status_code == 400

    r = client.post(f"/api/lgpd/apagar/{pac_id}", json={"confirmacao": True}, headers=_auth(client, app))
    assert r.status_code == 200, r.get_data()
    assert r.json["status"] == "anonimizado"

    with app.app_context():
        pac = Paciente.query.get(pac_id)
        assert pac.nome == "TITULAR ANONIMIZADO"
        assert pac.cpf is None and pac.telefone is None
        # pré-consulta excluída
        assert PreConsulta.query.filter_by(paciente_id=pac_id).count() == 0
        # lançamento financeiro retido (obrigação legal), sem vínculo com identidade
        assert LancamentoFaturamento.query.filter_by(paciente_id=pac_id).count() == 1
