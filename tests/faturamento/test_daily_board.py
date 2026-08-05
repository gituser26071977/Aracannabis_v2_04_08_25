"""Testes do Daily Board + integração intake→SIAP + financeiro discreto do médico."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Paciente, Consulta, PreConsulta, LancamentoFaturamento, Servico


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        medico = Profissional(
            nome="Dr. Clínico", usuario="dr_clin", senha="x",
            email="dr_clin@teste.local", role="profissional",
            status_cadastro="aprovado", perfil_acesso="assistencial",
        )
        admin = Profissional(
            nome="Admin", usuario="adm", senha="x",
            email="adm@teste.local", role="admin", status_cadastro="aprovado",
        )
        db.session.add_all([medico, admin])
        db.session.commit()

        pac = Paciente(nome="Maria Paciente", telefone="11999990000", data_nascimento=None)
        db.session.add(pac)
        db.session.commit()

        consulta = Consulta(
            paciente_id=pac.id, profissional_id=medico.id,
            data_hora=datetime.utcnow(), status="confirmada",
        )
        db.session.add(consulta)
        db.session.commit()

        pre = PreConsulta(
            paciente_id=pac.id, queixa_principal="Insônia", intensidade="7",
            canal="web", intake_interview_id="iv-1", araos_patient_id="intake:abc",
        )
        db.session.add(pre)
        db.session.commit()

        serv = Servico(nome="Consulta", tipo="consulta", valor_particular=200.0)
        db.session.add(serv)
        db.session.commit()
        lanc = LancamentoFaturamento(
            paciente_id=pac.id, profissional_id=medico.id, servico_id=serv.id,
            convenio_id=None, valor_total=200.0, desconto=0.0, valor_receber=200.0,
            percentual_repasse=60.0, valor_repasse=120.0, status="pendente",
        )
        db.session.add(lanc)
        db.session.commit()

        app.config["TEST"] = {"medico": medico.id, "admin": admin.id, "pac": pac.id}
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
    # upsert: novo paciente pelo telefone
    r = client.post("/api/intake/patient", json={
        "patient_name": "João Novo", "phone": "(11) 98888-7777",
        "queixa_principal": "Dor nas costas", "intensidade": "5",
        "canal": "telegram", "interview_id": "iv-2", "araos_patient_id": "intake:def",
    })
    assert r.status_code == 201, r.get_data()
    pac_id = r.json["paciente_id"]

    # idempotente (mesmo interview_id)
    r2 = client.post("/api/intake/patient", json={
        "patient_name": "João Novo", "phone": "(11) 98888-7777",
        "queixa_principal": "Dor nas costas", "intensidade": "5",
        "canal": "telegram", "interview_id": "iv-2",
    })
    assert r2.status_code == 200  # não recria
    assert r2.json["paciente_id"] == pac_id

    with app.app_context():
        assert Paciente.query.get(pac_id).telefone == "11988887777"
        pre = PreConsulta.query.filter_by(intake_interview_id="iv-2").first()
        assert pre is not None and pre.paciente_id == pac_id


def REDACTED(client, app):
    with app.app_context():
        pac_id = app.config["TEST"]["pac"]
    r = client.post("/api/intake/patient", json={
        "patient_name": "Maria Paciente", "phone": "11999990000",
        "queixa_principal": "Nova queixa", "canal": "web", "interview_id": "iv-3",
    })
    assert r.json["paciente_id"] == pac_id  # mesmo paciente, não duplicou


def test_daily_board_medico(client, app):
    r = client.get("/api/dashboard/pacientes-do-dia", headers=_auth(client, app, "medico"))
    assert r.status_code == 200
    assert r.json["total"] == 1
    item = r.json["pacientes"][0]
    assert item["paciente_nome"] == "Maria Paciente"
    assert item["pre_consulta"]["feita"] is True
    assert item["pre_consulta"]["queixa_principal"] == "Insônia"


def test_financeiro_discreto_do_medico(client, app):
    # assistencial acessa a própria situação financeira (exceção read-only)
    r = client.get("/api/faturamento/minha-situacao", headers=_auth(client, app, "medico"))
    assert r.status_code == 200, r.get_data()
    d = r.json
    assert d["total_lancado"] == 200.0
    assert d["pendente"] == 200.0
    assert d["repasse_due"] == 120.0

    # mas assistencial NÃO opera faturamento (config/geral ainda 403)
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "medico"))
    assert r.status_code == 403
