"""Testes do fluxo de convites de associação (onboarding de médicos).

Cobre:
    - gerar convite (admin) → token + código
    - não-admin não gera convite
    - aceitar via código (logado) → vira membro
    - aceitar via token (link) com validação de email
    - revogar convite
    - convite expirado
"""

from __future__ import annotations

import uuid
from datetime import timedelta, datetime

import pytest

from config import TestingConfig
from app_cors_livre import create_app
from models import db, Profissional
from models_extra import ConviteAssociacao, UsuarioAssociacao
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    a = create_app(TestingConfig)
    with a.app_context():
        db.create_all()
    yield a
    with a.app_context():
        db.session.remove()
        db.drop_all()


def _criar_associacao(nome="Clinica Teste"):
    from association.models import Associacao

    a = Associacao(
        nome=nome,
        slug=f"slug-{uuid.uuid4().hex[:8]}",
        cnpj=f"AUTO-{uuid.uuid4().hex[:8]}",
        ativo=True,
    )
    db.session.add(a)
    db.session.flush()
    return a


def _criar_profissional(usuario, email, role="profissional"):
    p = Profissional(
        nome=f"Prof {usuario}",
        usuario=usuario,
        email=email,
        senha=generate_password_hash("Teste@123456"),
        role=role,
        status_cadastro="aprovado",
    )
    db.session.add(p)
    db.session.flush()
    return p


def _login(client, usuario, senha="Teste@123456"):
    r = client.post("/api/auth/login", json={"usuario": usuario, "senha": senha})
    assert r.status_code == 200, r.data
    return {"Authorization": f"Bearer {r.get_json()['access_token']}"}


class TestGerarConvite:
    def test_admin_gera_convite(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin.clinica", "admin@clinica.com", role="admin")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            db.session.commit()

        headers = _login(client, "admin.clinica")
        r = client.post("/api/convites", json={"email": "medico@teste.com"}, headers=headers)
        assert r.status_code == 201, r.data
        body = r.get_json()["convite"]
        assert body["token"]
        assert len(body["codigo"]) == 6
        assert body["status"] == "pendente"

    def test_nao_admin_bloqueado(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            prof = _criar_profissional("medico.semlink", "medico@x.com")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=prof.id, associacao_id=assoc.id,
                    role="member", status="active"
                )
            )
            db.session.commit()

        headers = _login(client, "medico.semlink")
        r = client.post("/api/convites", json={"email": "outro@x.com"}, headers=headers)
        assert r.status_code == 403

    def test_email_invalido(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin2", "admin2@x.com", role="admin")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            db.session.commit()
        headers = _login(client, "admin2")
        r = client.post("/api/convites", json={"email": "invalido"}, headers=headers)
        assert r.status_code == 400


class TestAceitarConvite:
    def test_aceitar_por_codigo(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            assoc_id = assoc.id
            admin = _criar_profissional("admin3", "admin3@x.com", role="admin")
            medico = _criar_profissional("medico.convidado", "medico@teste.com")
            medico_id = medico.id
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            convite = ConviteAssociacao(
                associacao_id=assoc.id, email="medico@teste.com",
                token=uuid.uuid4().hex, codigo="ABC123",
                expira_em=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(convite)
            db.session.commit()
            convite_id = convite.id

        headers = _login(client, "medico.convidado")
        r = client.post("/api/convites/aceitar", json={"codigo": "ABC123"}, headers=headers)
        assert r.status_code == 200, r.data
        assert r.get_json()["associacao_id"] == assoc_id

        with app.app_context():
            link = UsuarioAssociacao.query.filter_by(profissional_id=medico_id, associacao_id=assoc_id).first()
            assert link is not None
            assert link.status == "active"
            conv = ConviteAssociacao.query.get(convite_id)
            assert conv.status == "aceito"

    def REDACTED(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin4", "admin4@x.com", role="admin")
            _criar_profissional("medico.token", "medico.token@x.com")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            convite = ConviteAssociacao(
                associacao_id=assoc.id, email="destinatario@x.com",
                token="tok-abc", codigo="ZZZ999",
                expira_em=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(convite)
            db.session.commit()

        headers = _login(client, "medico.token")
        # email do convite != email do usuário → bloqueia
        r = client.post("/api/convites/token", json={"token": "tok-abc"}, headers=headers)
        assert r.status_code == 403

    def test_aceitar_por_token_sucesso(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin5", "admin5@x.com", role="admin")
            _criar_profissional("medico.ok", "ok@x.com")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            convite = ConviteAssociacao(
                associacao_id=assoc.id, email="ok@x.com",
                token="tok-ok", codigo="OKK111",
                expira_em=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(convite)
            db.session.commit()

        headers = _login(client, "medico.ok")
        r = client.post("/api/convites/token", json={"token": "tok-ok"}, headers=headers)
        assert r.status_code == 200, r.data


class TestRevogarConvite:
    def test_revogar(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin6", "admin6@x.com", role="admin")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            convite = ConviteAssociacao(
                associacao_id=assoc.id, email="a@x.com",
                token=uuid.uuid4().hex, codigo="REV123",
                expira_em=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(convite)
            db.session.commit()
            convite_id = convite.id

        headers = _login(client, "admin6")
        r = client.delete(f"/api/convites/{convite_id}", headers=headers)
        assert r.status_code == 200

        with app.app_context():
            conv = ConviteAssociacao.query.get(convite_id)
            assert conv.status == "revogado"


class TestConviteExpirado:
    def test_codigo_expirado(self, app):
        client = app.test_client()
        with app.app_context():
            assoc = _criar_associacao()
            admin = _criar_profissional("admin7", "admin7@x.com", role="admin")
            _criar_profissional("medico.exp", "exp@x.com")
            db.session.add(
                UsuarioAssociacao(
                    profissional_id=admin.id, associacao_id=assoc.id,
                    role="admin", status="active"
                )
            )
            convite = ConviteAssociacao(
                associacao_id=assoc.id, email="exp@x.com",
                token=uuid.uuid4().hex, codigo="EXP111",
                expira_em=datetime.utcnow() - timedelta(days=1),
            )
            db.session.add(convite)
            db.session.commit()

        headers = _login(client, "medico.exp")
        r = client.post("/api/convites/aceitar", json={"codigo": "EXP111"}, headers=headers)
        assert r.status_code == 400
