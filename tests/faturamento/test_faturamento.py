"""Testes do módulo Faturamento Clínico (Fase 1 — núcleo).

Cobre: CRUD convênios/serviços/tabela/percentuais, lançamento (particular e
convênio), recebimento parcial/pago, estorno, visibilidade por role.
"""

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
        admin = Profissional(
            nome="Admin Teste", usuario="admin_t", senha="x",
            email="admin_t@teste.local", role="admin", status_cadastro="aprovado",
        )
        prof = Profissional(
            nome="Dr. Teste", usuario="dr_t", senha="x",
            email="dr_t@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="solo",
        )
        prof2 = Profissional(
            nome="Dra. Teste2", usuario="dr_t2", senha="x",
            email="dr_t2@teste.local", role="profissional", status_cadastro="aprovado",
            perfil_acesso="administrativo",
        )
        db.session.add_all([admin, prof, prof2])
        db.session.commit()
        app.config["TEST_IDS"] = {
            "admin": admin.id, "prof": prof.id, "prof2": prof2.id,
        }
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _auth(client, app, user_id: str):
    with app.app_context():
        token = create_access_token(identity=str(app.config["TEST_IDS"][user_id]))
    return {"Authorization": f"Bearer {token}"}


def _post(client, path, token, body):
    return client.post(path, json=body, headers=token)


def REDACTED(app, client):
    admin = _auth(client, app, "admin")
    prof = _auth(client, app, "prof")

    # sem auth → 401
    r = client.get("/api/faturamento/servicos")
    assert r.status_code == 401

    # cria convênio + serviço (admin)
    r = _post(client, "/api/faturamento/convenios", admin, {"nome": "Unimed SE", "registro_ans": "012345"})
    assert r.status_code == 201, r.get_data()
    convenio_id = r.json["convenio"]["id"]

    r = _post(client, "/api/faturamento/servicos", admin, {"nome": "Consulta", "tipo": "consulta", "valor_particular": 200})
    assert r.status_code == 201, r.get_data()
    consulta_id = r.json["servico"]["id"]

    r = _post(client, "/api/faturamento/servicos", admin, {"nome": "Retorno", "tipo": "retorno", "valor_particular": 100})
    assert r.status_code == 201
    retorno_id = r.json["servico"]["id"]

    # percentual do Dr. Teste por serviço (consulta 60%, retorno global 50%)
    r = _post(client, "/api/faturamento/profissionais/%s/percentuais" % app.config["TEST_IDS"]["prof"],
              admin, {"servico_id": consulta_id, "percentual": 60})
    assert r.status_code == 200
    r = _post(client, "/api/faturamento/profissionais/%s/percentuais" % app.config["TEST_IDS"]["prof"],
              admin, {"servico_id": None, "percentual": 50})
    assert r.status_code == 200

    # tabela do convênio: consulta = R$150 fixo
    r = _post(client, "/api/faturamento/convenios/%s/tabela" % convenio_id, admin,
              {"servico_id": consulta_id, "valor": 150})
    assert r.status_code == 200, r.get_data()

    # profissional com perfil ADMINISTRATIVO (secretária) NÃO pode configurar (403)
    prof2 = _auth(client, app, "prof2")
    r = _post(client, "/api/faturamento/servicos", prof2, {"nome": "X"})
    assert r.status_code == 403

    # ── lançamento PARTICULAR (sem convenio) — consulta R$200, %60
    r = _post(client, "/api/faturamento/lancamentos", prof,
              {"servico_id": consulta_id, "forma_pagamento": "pix"})
    assert r.status_code == 201, r.get_data()
    lanc = r.json["lancamento"]
    assert lanc["modalidade"] == "particular"
    assert lanc["valor_total"] == 200.0
    assert lanc["percentual_repasse"] == 60.0
    assert lanc["valor_repasse"] == 120.0
    assert lanc["status"] == "pendente"
    l_particular = lanc["id"]

    # ── lançamento CONVÊNIO (com desconto) — valor R$150, %60
    r = _post(client, "/api/faturamento/lancamentos", prof,
              {"servico_id": consulta_id, "convenio_id": convenio_id, "desconto": 10,
               "forma_pagamento": "cartao"})
    assert r.status_code == 201, r.get_data()
    lanc = r.json["lancamento"]
    assert lanc["modalidade"] == "convenio"
    assert lanc["valor_total"] == 150.0
    assert lanc["valor_receber"] == 140.0
    assert lanc["valor_repasse"] == 84.0  # 60% de 140
    l_convenio = lanc["id"]

    # retorno usa % global 50%
    r = _post(client, "/api/faturamento/lancamentos", prof,
              {"servico_id": retorno_id})
    assert r.status_code == 201
    assert r.json["lancamento"]["valor_repasse"] == 50.0  # 50% de 100

    # ── recebimento parcial → pago
    r = _post(client, "/api/faturamento/lancamentos/%s/receber" % l_particular, prof, {"valor": 80, "forma_pagamento": "pix"})
    assert r.status_code == 200
    assert r.json["lancamento"]["status"] == "parcial"
    r = _post(client, "/api/faturamento/lancamentos/%s/receber" % l_particular, prof, {"valor": 120, "forma_pagamento": "dinheiro"})
    assert r.status_code == 200
    assert r.json["lancamento"]["status"] == "pago"
    assert r.json["lancamento"]["valor_recebido"] == 200.0

    # ── visibilidade: secretária (administrativo, não-gestor) vê tudo MASCARADO
    prof2 = _auth(client, app, "prof2")
    r = client.get("/api/faturamento/lancamentos", headers=prof2)
    assert r.status_code == 200
    assert r.json["privileged"] is False
    assert r.json["total"] == 3  # operacional: vê os lançamentos sem valores
    for l in r.json["lancamentos"]:
        assert "valor_receber" not in l and "valor_repasse" not in l

    # admin vê tudo (3 lançamentos) + filtros
    r = client.get("/api/faturamento/lancamentos", headers=admin)
    assert r.json["total"] == 3
    r = client.get("/api/faturamento/lancamentos?modalidade=particular", headers=admin)
    assert r.json["total"] == 2  # consulta + retorno (sem convênio)
    r = client.get("/api/faturamento/lancamentos?modalidade=convenio", headers=admin)
    assert r.json["total"] == 1
    r = client.get("/api/faturamento/lancamentos?status=pago", headers=admin)
    assert r.json["total"] == 1

    # ── estorno do lançamento de convênio (admin)
    r = _post(client, "/api/faturamento/lancamentos/%s/estornar" % l_convenio, admin, {})
    assert r.status_code == 200
    assert r.json["lancamento"]["status"] == "cancelado"
