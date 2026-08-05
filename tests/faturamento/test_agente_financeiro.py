"""Testes do agente financeiro (Fase 1 — read-only)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

os.environ.setdefault("AGENT_LLM_DISABLED", "true")  # testes rápidos/determinísticos (fallback heurístico)

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Paciente, Consulta, PreConsulta, LancamentoFaturamento, Servico, Convenio, Recebimento


@pytest.fixture()
def app():
    app = create_app(config_obj=TestingConfig)
    with app.app_context():
        db.create_all()
        admin = Profissional(
            nome="Gestor", usuario="gestor", senha="x",
            email="gestor@teste.local", role="admin", status_cadastro="aprovado",
        )
        medico = Profissional(
            nome="Dr. Carlos", usuario="dr_carlos", senha="x",
            email="dr_carlos@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="assistencial",
        )
        secretaria = Profissional(
            nome="Secretária", usuario="secre", senha="x",
            email="secre@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="administrativo",
        )
        db.session.add_all([admin, medico, secretaria])
        db.session.commit()

        pac = Paciente(nome="Maria", telefone="11999990000")
        db.session.add(pac)
        db.session.commit()

        serv = Servico(nome="Consulta", tipo="consulta", valor_particular=200.0)
        db.session.add(serv)
        db.session.commit()

        convenio = Convenio(nome="Unimed SE", tipo="operadora")
        db.session.add(convenio)
        db.session.commit()

        # lançamento pago (do médico) + lançamento pendente (do médico) + um de outro médico
        l1 = LancamentoFaturamento(
            paciente_id=pac.id, profissional_id=medico.id, servico_id=serv.id,
            convenio_id=None, valor_total=200.0, desconto=0.0, valor_receber=200.0,
            percentual_repasse=60.0, valor_repasse=120.0, status="pago",
            data_lancamento=datetime.utcnow() - timedelta(days=2),
        )
        l2 = LancamentoFaturamento(
            paciente_id=pac.id, profissional_id=medico.id, servico_id=serv.id,
            convenio_id=convenio.id, valor_total=150.0, desconto=0.0, valor_receber=150.0,
            percentual_repasse=60.0, valor_repasse=90.0, status="pendente",
            data_lancamento=datetime.utcnow(),
        )
        db.session.add_all([l1, l2])
        db.session.commit()
        db.session.add(Recebimento(lancamento_id=l1.id, valor=200.0))
        db.session.commit()

        app.config["TEST"] = {"admin": admin.id, "medico": medico.id, "secretaria": secretaria.id}
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


def _perguntar(client, app, pergunta, user="admin"):
    return client.post("/api/faturamento/agente",
                       json={"pergunta": pergunta},
                       headers=_auth(client, app, user))


def test_classificacao_heuristica():
    from services.faturamento_agente import classificar_intencao

    assert classificar_intencao("quanto recebi neste mês?")["tipo"] == "receita"
    assert classificar_intencao("quem está inadimplente?")["tipo"] == "pendentes"
    assert classificar_intencao("qual o repasse do Dr. Carlos?")["tipo"] == "repasse"
    assert classificar_intencao("resumo da situação")["tipo"] == "resumo"
    assert classificar_intencao("quanto veio do convênio?")["tipo"] == "convenio"


def test_receita_resumo_e_pendentes(client, app):
    r = _perguntar(client, app, "quanto recebi neste mês?")
    assert r.status_code == 200, r.get_data()
    assert r.json["tipo"] == "receita"
    assert r.json["resposta"]

    r = _perguntar(client, app, "resumo do financeiro")
    assert r.json["tipo"] == "resumo"
    assert r.json["dados"]["recebido"] == 200.0

    r = _perguntar(client, app, "quem está inadimplente?")
    assert r.json["tipo"] == "pendentes"
    assert r.json["dados"]["quantidade"] == 1
    assert r.json["dados"]["total_pendente"] == 150.0


def test_repasse_por_profissional(client, app):
    r = _perguntar(client, app, "qual o repasse do Dr. Carlos?")
    assert r.status_code == 200
    assert r.json["tipo"] == "repasse"
    assert r.json["dados"]["repasse_total"] == 210.0  # 120 + 90


def test_convenio(client, app):
    r = _perguntar(client, app, "quanto veio do convênio?")
    assert r.status_code == 200
    assert r.json["tipo"] == "convenio"
    assert r.json["dados"]["quantidade"] == 1  # só o lançamento da Unimed
    assert r.json["dados"]["lancado"] == 150.0


def test_assistencial_ve_so_o_proprio(client, app):
    # médico (assistencial) consulta só os próprios lançamentos — não bloqueado
    r = _perguntar(client, app, "resumo do financeiro", user="medico")
    assert r.status_code == 200
    assert r.json["dados"]["quantidade"] == 2  # os 2 do Dr. Carlos


def test_assistencial_nao_opera(client, app):
    r = client.get("/api/faturamento/servicos", headers=_auth(client, app, "medico"))
    assert r.status_code == 403


def REDACTED(client, app):
    r = _perguntar(client, app, "qual o repasse do Dr. Carlos?", user="secretaria")
    assert r.status_code == 200
    assert r.json["tipo"] == "repasse"
    assert "privilégio" in r.json["resposta"] or "privilégio" in r.json["resposta"]


def REDACTED(client, app):
    r = _perguntar(client, app, "quem está inadimplente?", user="secretaria")
    assert r.status_code == 200
    assert r.json["tipo"] == "pendentes"
    for item in r.json["dados"]["itens"]:
        assert "profissional" not in item  # sem nome do médico


def test_secretaria_ve_agregado(client, app):
    r = _perguntar(client, app, "resumo do financeiro", user="secretaria")
    assert r.status_code == 200
    assert r.json["dados"]["recebido"] == 200.0  # agregado permitido


def REDACTED(client, app):
    # médico pergunta o repasse de outro médico → responde com o PRÓPRIO, não o de Carlos
    r = _perguntar(client, app, "qual o repasse do Dr. Carlos?", user="medico")
    assert r.status_code == 200
    assert r.json["tipo"] == "repasse"
    # escopo = próprio médico: os 2 lançamentos são do Dr. Carlos → ele "vê" os dele
    assert r.json["dados"]["quantidade"] == 2


def REDACTED(client, app):
    # secretária (administrativo, não-gestor) vê a listagem SEM valores/repasse
    r = client.get("/api/faturamento/lancamentos", headers=_auth(client, app, "secretaria"))
    assert r.status_code == 200
    assert r.json["privileged"] is False
    assert r.json["total"] >= 2  # vê os lançamentos (operacional)
    for l in r.json["lancamentos"]:
        assert "valor_receber" not in l
        assert "valor_repasse" not in l
        assert "valor_total" not in l
        assert "status_label" in l  # flag PAGO/EM ABERTO/RESTITUÍDO


def REDACTED(client, app):
    r = client.get("/api/faturamento/lancamentos", headers=_auth(client, app, "admin"))
    assert r.status_code == 200
    assert r.json["privileged"] is True
    assert r.json["total"] >= 2
    for l in r.json["lancamentos"]:
        assert "valor_receber" in l
        assert "valor_repasse" in l


def test_medico_listagem_bloqueada(client, app):
    # assistencial NÃO lista lançamentos (área administrativa); usa minha-situacao
    r = client.get("/api/faturamento/lancamentos", headers=_auth(client, app, "medico"))
    assert r.status_code == 403
