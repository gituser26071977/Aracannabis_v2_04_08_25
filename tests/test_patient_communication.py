"""Testes de consentimento/opt-out e da campanha do Portal do Paciente."""

from __future__ import annotations

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Paciente, PatientConvite, Profissional, Associacao
from models_extra import UsuarioAssociacao


@pytest.fixture()
def app():
    application = create_app(config_obj=TestingConfig)
    with application.app_context():
        db.create_all()
        yield application


def _auth(application, identity="1"):
    with application.app_context():
        return create_access_token(identity=identity)


def test_endpoint_comunicacao_registra_consentimento_e_opt_out(app):
    client = app.test_client()
    with app.app_context():
        prof = Profissional(
            nome="Admin Teste", usuario="admin_teste", senha="x", role="admin"
        )
        db.session.add(prof)
        db.session.flush()
        assoc = Associacao(nome="Consultório Teste", cnpj="AUTO-TESTE-1", ativo=True)
        db.session.add(assoc)
        db.session.flush()
        db.session.add(UsuarioAssociacao(
            profissional_id=prof.id, associacao_id=assoc.id,
            role="admin", status="active",
        ))
        p = Paciente(
            nome="Fulano Teste", cpf="11122233344",
            telefone="5579999999999", associacao_id=assoc.id,
        )
        db.session.add(p)
        db.session.commit()
        pid = p.id
        prof_id = prof.id

    headers = {"Authorization": f"Bearer {_auth(app, str(prof_id))}"}
    r = client.post(
        f"/api/lgpd/comunicacao/{pid}",
        json={"aceita_comunicacao_whatsapp": True},
        headers=headers,
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json()["aceita_comunicacao_whatsapp"] is True

    r = client.post(
        f"/api/lgpd/comunicacao/{pid}",
        json={"opt_out": True, "opt_out_motivo": "pediu para não receber"},
        headers=headers,
    )
    body = r.get_json()
    assert r.status_code == 200
    assert body["opt_out_em"] is not None
    assert body["aceita_comunicacao_whatsapp"] is False

    r = client.get(f"/api/lgpd/comunicacao/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["opt_out_motivo"] == "pediu para não receber"


def test_campanha_seleciona_somente_elegiveis(app):
    from scripts.campanha_portal_paciente import (
        render_mensagem,
        selecionar_destinatarios,
    )

    with app.app_context():
        autorizado = Paciente(
            nome="Ana Autorizada", cpf="11122233344", telefone="5579999990001",
            aceita_comunicacao_whatsapp=True,
        )
        recusou = Paciente(
            nome="Bia Recusou", cpf="22233344455", telefone="5579999990002",
            aceita_comunicacao_whatsapp=False,
        )
        nao_informado = Paciente(
            nome="Caio Não Informado", cpf="33344455566", telefone="5579999990003",
        )
        sem_telefone = Paciente(
            nome="Dora Sem Fone", cpf="44455566677",
            aceita_comunicacao_whatsapp=True,
        )
        db.session.add_all([autorizado, recusou, nao_informado, sem_telefone])
        db.session.commit()

        padrao = selecionar_destinatarios()
        assert [p.nome for p in padrao] == ["Ana Autorizada"]

        ampliado = selecionar_destinatarios(incluir_sem_consentimento=True)
        nomes = {p.nome for p in ampliado}
        assert nomes == {"Ana Autorizada", "Caio Não Informado"}
        assert "Bia Recusou" not in nomes
        assert "Dora Sem Fone" not in nomes

    assert "Ana" in render_mensagem("Ana Autorizada")
    assert "https://" in render_mensagem("Ana Autorizada")


def test_check_numbers_mapeia_resposta(app, monkeypatch):
    from services.whatsapp_service import WhatsAppService

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return [
                {"number": "5579999990001", "exists": True, "jid": "5579999990001@s.whatsapp.net"},
                {"number": "5579999990002", "exists": False},
            ]

    monkeypatch.setenv("WHATSAPP_API_KEY", "test-key")
    monkeypatch.setattr(
        "services.whatsapp_service.requests.post",
        lambda *a, **k: FakeResponse(),
    )

    svc = WhatsAppService(instance_name="teste")
    dados = svc.check_numbers(["5579999990001", "5579999990002"])
    assert dados["5579999990001"]["exists"] is True
    assert dados["5579999990002"]["exists"] is False


def test_patient_convite_to_dict(app):
    with app.app_context():
        p = Paciente(nome="Log Teste", cpf="99988877766", telefone="5579988887777")
        db.session.add(p)
        db.session.flush()
        convite = PatientConvite(
            paciente_id=p.id, canal="whatsapp", template="convite_portal",
            status="enviado", provider_id="ABC123",
        )
        db.session.add(convite)
        db.session.commit()
        assert convite.to_dict()["status"] == "enviado"
