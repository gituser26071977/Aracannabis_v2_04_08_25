"""Testes da recuperação de senha com solicitação pendente (bug fix).

Cobre a inconsistência: email com solicitação pendente deve retornar
mensagem clara (não "email não encontrado"), e o cadastro duplicado
deve explicar que a solicitação está em análise.
"""

from __future__ import annotations

import uuid

import pytest

from config import TestingConfig
from app_cors_livre import create_app
from models import db, SolicitacoesCadastro


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
    yield app.test_client()
    with app.app_context():
        db.session.remove()
        db.drop_all()


class REDACTED:
    def REDACTED(self, client):
        email = f"pendente-{uuid.uuid4().hex[:6]}@teste.com"
        with client.application.app_context():
            db.session.add(SolicitacoesCadastro(
                nome="Paciente Pendente", email=email, status="pendente"
            ))
            db.session.commit()

        r = client.post("/api/auth/request-password-setup", json={"email": email})
        assert r.status_code == 409, r.data
        body = r.get_json()
        assert body["status"] == "pending"
        assert "aguardando aprovação" in body["error"].lower()

    def test_forgot_unknown_email_404(self, client):
        r = client.post(
            "/api/auth/request-password-setup",
            json={"email": f"naoexiste-{uuid.uuid4().hex[:6]}@teste.com"},
        )
        assert r.status_code == 404

    def REDACTED(self, client):
        email = f"dup-{uuid.uuid4().hex[:6]}@teste.com"
        with client.application.app_context():
            db.session.add(SolicitacoesCadastro(
                nome="Duplicado", email=email, status="pendente"
            ))
            db.session.commit()

        r = client.post("/api/cadastro_profissionais/solicitar-cadastro", json={
            "nome": "Outro", "email": email, "conselho_tipo": "CRM",
            "crm": "9999999", "uf_crm": "SP",
        })
        assert r.status_code == 409, r.data
        assert "em análise" in r.get_json()["error"]
