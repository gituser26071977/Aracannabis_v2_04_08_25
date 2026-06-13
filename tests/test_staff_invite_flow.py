"""
Testes da Fase 2 — Fluxo de Convite de Staff (Secretária / Gestor)

Cobre:
  1. POST /associations/<id>/professional-invites  com invite_type='staff'
  2. GET  /associations/<id>/professional-invites  (listagem com filtros)
  3. POST /professional-invites/<id>/revoke
  4. POST /professional-invites/<id>/resend
  5. GET  /professional-invites/<token>  (lookup público)
  6. POST /solicitar-cadastro-staff  (aceite)
  7. Validações: convite expirado, revogado, tipo errado
  8. Audit logs
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def app_with_association():
    """
    App Flask com:
      - Associação 'Clínica Teste' (id=1)
      - Profissional admin (id=1) vinculado como 'admin' da Associação
      - Profissional doctor (id=2) vinculado como 'member'
      - Convite staff pendente (token='VALID_STAFF_TOKEN', role='secretary', type='staff')
    """
    from flask import Flask, jsonify
    from flask_jwt_extended import JWTManager

    from models import db, Profissional, SolicitacoesCadastro
    from models_extra import UsuarioAssociacao, AuditLog
    from association.models import Associacao, ConviteProfissionalInstituicao, Membro, Estoque, Dispensacao, DocumentoMembro
    from association.routes import association_bp
    from routes.cadastro_profissionais import cadastro_profissionais_bp
    from middleware.permission_middleware import register_permission_middleware

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "TEST_DATABASE_URI", "sqlite:///:memory:"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "test-secret-staff-invite"
    app.config["SECRET_KEY"] = "test-secret-staff-invite"

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

        assoc = Associacao(
            id=1, nome="Clínica Teste", cnpj="12345678000199", ativo=True
        )
        db.session.add(assoc)
        db.session.commit()

        admin = Profissional(
            id=1, nome="Admin", crm=None, uf_crm=None,
            usuario="admin", email="admin@test.com",
            senha=generate_password_hash("123"),
            role="admin",
            status_cadastro="aprovado",
            email_verified=True, onboarding_completed=True,
        )
        doctor = Profissional(
            id=2, nome="Dr", crm="CRM1", uf_crm="SP",
            usuario="medico", email="med@test.com",
            senha=generate_password_hash("123"),
            role="profissional",
            status_cadastro="aprovado",
            email_verified=True, onboarding_completed=True,
        )
        db.session.add_all([admin, doctor])
        db.session.commit()

        # Admin vinculado
        link_admin = UsuarioAssociacao(
            profissional_id=admin.id, associacao_id=assoc.id,
            role="admin", status="active",
        )
        link_doc = UsuarioAssociacao(
            profissional_id=doctor.id, associacao_id=assoc.id,
            role="member", status="active",
        )
        db.session.add_all([link_admin, link_doc])
        db.session.commit()

        # Convite staff válido
        convite = ConviteProfissionalInstituicao(
            id=1,
            associacao_id=assoc.id,
            convidado_por_id=admin.id,
            nome="Maria Silva",
            email="maria@test.com",
            telefone="(11) 99999-9999",
            role="secretary",
            invite_type=ConviteProfissionalInstituicao.INVITE_TYPE_STAFF,
            token="VALID_STAFF_TOKEN",
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.session.add(convite)
        db.session.commit()

    # Os blueprints precisam registrar
    app.register_blueprint(association_bp, url_prefix="/api/association")
    app.register_blueprint(cadastro_profissionais_bp, url_prefix="/api/cadastro_profissionais")
    register_permission_middleware(app)

    return app


@pytest.fixture
def client(app_with_association):
    return app_with_association.test_client()


def _make_token(app, profissional_id):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        return create_access_token(identity=str(profissional_id))


# ═══════════════════════════════════════════════════════════════════════
# 1. POST /associations/<id>/professional-invites (invite_type=staff)
# ═══════════════════════════════════════════════════════════════════════

class TestCreateStaffInvite:
    """Cria convite de staff — apenas admin da instituição."""

    def test_admin_can_invite_secretary(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "Nova Secretária",
                "email": "nova.sec@test.com",
                "telefone": "(11) 98888-7777",
                "invite_type": "staff",
                "role": "secretary",
            },
        )
        assert res.status_code == 201, res.get_json()
        data = res.get_json()
        assert data["success"]
        assert data["convite"]["invite_type"] == "staff"
        assert data["convite"]["role"] == "secretary"
        assert "invite_link" in data
        assert "/convite-staff/" in data["invite_link"]

    def test_admin_can_invite_manager(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "Novo Gestor",
                "email": "gestor@test.com",
                "invite_type": "staff",
                "role": "manager",
            },
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["convite"]["role"] == "manager"
        assert "/convite-staff/" in data["invite_link"]

    def test_doctor_cannot_invite(self, client, app_with_association):
        """Médico (member) NÃO pode convidar — apenas admin."""
        token = _make_token(app_with_association, 2)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "X", "email": "x@test.com",
                "invite_type": "staff", "role": "secretary",
            },
        )
        assert res.status_code == 403

    def test_default_role_for_staff_is_secretary(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "Default Sec", "email": "def@test.com",
                "invite_type": "staff",
                # sem role -> deve default para 'secretary'
            },
        )
        assert res.status_code == 201
        assert res.get_json()["convite"]["role"] == "secretary"

    def test_invalid_role_for_staff_rejected(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "X", "email": "x@test.com",
                "invite_type": "staff", "role": "physician",  # não é role de staff
            },
        )
        assert res.status_code == 400
        assert "role" in res.get_json()["error"].lower()

    def test_invalid_invite_type_rejected(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "X", "email": "x@test.com",
                "invite_type": "hacker", "role": "secretary",
            },
        )
        assert res.status_code == 400

    def test_professional_invite_uses_other_link(self, client, app_with_association):
        """Convite profissional gera link /cadastro-profissionais, não /convite-staff."""
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "Dr Conv", "email": "drconv@test.com",
                "invite_type": "professional",
                # role default = 'member'
            },
        )
        assert res.status_code == 201
        data = res.get_json()
        assert data["convite"]["invite_type"] == "professional"
        assert "/cadastro-profissionais" in data["invite_link"]


# ═══════════════════════════════════════════════════════════════════════
# 2. GET /associations/<id>/professional-invites (listagem)
# ═══════════════════════════════════════════════════════════════════════

class TestListInvites:

    def test_list_all_invites(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.get(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert data["total"] >= 1
        # Convite de seed (maria@test.com) deve aparecer
        assert any(c["email"] == "maria@test.com" for c in data["convites"])
        # to_dict() por padrão NÃO expõe o token
        assert all("token" not in c or c.get("token") is None for c in data["convites"])

    def test_filter_by_invite_type(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.get(
            "/api/association/associations/1/professional-invites?invite_type=staff",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        convites = res.get_json()["convites"]
        assert all(c["invite_type"] == "staff" for c in convites)

    def test_filter_by_status(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.get(
            "/api/association/associations/1/professional-invites?status=pending",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        convites = res.get_json()["convites"]
        assert all(c["status"] == "pending" for c in convites)

    def test_filter_by_email(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.get(
            "/api/association/associations/1/professional-invites?email=maria",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        convites = res.get_json()["convites"]
        assert all("maria" in (c["email"] or "").lower() for c in convites)

    def test_non_admin_cannot_list(self, client, app_with_association):
        token = _make_token(app_with_association, 2)
        res = client.get(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# 3. POST /professional-invites/<id>/revoke
# ═══════════════════════════════════════════════════════════════════════

class TestRevokeInvite:

    def test_admin_can_revoke_pending(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["convite"]["status"] == "revoked"
        assert data["convite"]["revoked_at"] is not None

    def test_doctor_cannot_revoke(self, client, app_with_association):
        token = _make_token(app_with_association, 2)
        res = client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403

    def test_revoked_invite_cannot_be_accepted(self, client, app_with_association):
        """Após revoke, /solicitar-cadastro-staff deve falhar."""
        admin_token = _make_token(app_with_association, 1)
        client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria",
                "email": "maria@test.com",
            },
        )
        assert res.status_code == 410
        assert "revogad" in res.get_json()["error"].lower()


# ═══════════════════════════════════════════════════════════════════════
# 4. POST /professional-invites/<id>/resend
# ═══════════════════════════════════════════════════════════════════════

class TestResendInvite:

    def test_admin_can_resend(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        res = client.post(
            "/api/association/professional-invites/1/resend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        # Em modo dev, email é simulado (não enviado de verdade)

    def test_resend_revoked_fails_410(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        res = client.post(
            "/api/association/professional-invites/1/resend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 410


# ═══════════════════════════════════════════════════════════════════════
# 5. GET /professional-invites/<token> (público)
# ═══════════════════════════════════════════════════════════════════════

class TestPublicInviteLookup:

    def test_valid_token_returns_invite(self, client):
        res = client.get("/api/association/professional-invites/VALID_STAFF_TOKEN")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert data["convite"]["nome"] == "Maria Silva"
        assert data["convite"]["associacao_id"] == 1
        assert data["convite"]["invite_type"] == "staff"
        assert data["convite"]["role"] == "secretary"

    def test_invalid_token_returns_404(self, client):
        res = client.get("/api/association/professional-invites/DOES_NOT_EXIST")
        assert res.status_code == 404

    def test_revoked_token_returns_410(self, client, app_with_association):
        token = _make_token(app_with_association, 1)
        client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        res = client.get("/api/association/professional-invites/VALID_STAFF_TOKEN")
        assert res.status_code == 410


# ═══════════════════════════════════════════════════════════════════════
# 6. POST /solicitar-cadastro-staff (aceite do convite)
# ═══════════════════════════════════════════════════════════════════════

class TestAcceptStaffInvite:

    def test_admin_accepts_staff_invite(self, client, app_with_association):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Silva Atualizada",
                "email": "maria@test.com",
                "telefone": "(11) 99999-9999",
            },
        )
        assert res.status_code == 201, res.get_json()
        data = res.get_json()
        assert data["success"]
        assert data["role"] == "secretary"
        assert data["usuario"] == "maria"
        assert data["associacao_nome"] == "Clínica Teste"

    def test_accept_with_custom_password(self, client, app_with_association):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Silva",
                "email": "maria@test.com",
                "senha": "minhasenha123",
            },
        )
        assert res.status_code == 201
        # Verifica que senha foi aceita (não exposta na resposta, mas user criado)

    def test_password_too_short_rejected(self, client, app_with_association):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria",
                "email": "maria@test.com",
                "senha": "123",  # muito curta
            },
        )
        assert res.status_code == 400
        assert "8 caracteres" in res.get_json()["error"]

    def test_email_mismatch_rejected(self, client, app_with_association):
        """Se convite tem email, aceitar com email diferente -> 403."""
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Outra",
                "email": "outra@test.com",  # != maria@test.com do convite
            },
        )
        assert res.status_code == 403
        assert "outro email" in res.get_json()["error"].lower()

    def test_missing_required_fields(self, client):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={"convite_token": "VALID_STAFF_TOKEN"},  # sem nome e email
        )
        assert res.status_code == 400
        assert "obrigatório" in res.get_json()["error"].lower()

    def test_invalid_email_rejected(self, client):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Silva",
                "email": "not-an-email",
            },
        )
        assert res.status_code == 400
        assert "email" in res.get_json()["error"].lower()

    def test_invite_must_be_staff_type(self, client, app_with_association):
        """Convite do tipo 'professional' não pode ser aceito via staff endpoint."""
        from association.models import ConviteProfissionalInstituicao
        from models import db
        with app_with_association.app_context():
            prof_invite = ConviteProfissionalInstituicao(
                associacao_id=1, convidado_por_id=1,
                nome="Dr Conv", email="drconv2@test.com",
                role="member", invite_type="professional",
                token="PROF_INVITE_TOKEN",
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(prof_invite)
            db.session.commit()

        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "PROF_INVITE_TOKEN",
                "nome": "Dr Conv",
                "email": "drconv2@test.com",
            },
        )
        assert res.status_code == 400
        assert "staff" in res.get_json()["error"].lower()

    def test_invite_not_found_404(self, client):
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "DOES_NOT_EXIST",
                "nome": "Maria",
                "email": "maria@x.com",
            },
        )
        assert res.status_code == 404
        assert "convite" in res.get_json()["error"].lower() or "não encontrad" in res.get_json()["error"].lower()

    def test_accepted_invite_cannot_be_reused(self, client, app_with_association):
        """Convite aceito não pode ser aceito de novo."""
        # Primeira aceitação OK
        res1 = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Silva",
                "email": "maria@test.com",
            },
        )
        assert res1.status_code == 201

        # Segunda tentativa falha
        res2 = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Outra Pessoa",
                "email": "outra@test.com",  # email diferente
            },
        )
        assert res2.status_code == 410
        assert "revogad" in res2.get_json()["error"].lower() or "utilizad" in res2.get_json()["error"].lower()

    def test_duplicate_email_rejected(self, client, app_with_association):
        """Não pode criar conta de staff com email já existente."""
        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Clone",
                "email": "maria@test.com",
            },
        )
        assert res.status_code == 201

        # Novo convite para mesmo email
        admin_token = _make_token(app_with_association, 1)
        from association.models import ConviteProfissionalInstituicao
        from models import db
        with app_with_association.app_context():
            novo = ConviteProfissionalInstituicao(
                associacao_id=1, convidado_por_id=1,
                nome="Maria 2", email="maria@test.com",
                role="secretary", invite_type="staff",
                token="VALID_STAFF_TOKEN_2",
                expires_at=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(novo)
            db.session.commit()

        res2 = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN_2",
                "nome": "Maria 2",
                "email": "maria@test.com",
            },
        )
        assert res2.status_code == 409
        assert "existe" in res2.get_json()["error"].lower()


# ═══════════════════════════════════════════════════════════════════════
# 7. Convite expirado
# ═══════════════════════════════════════════════════════════════════════

class TestExpiredInvite:

    def test_expired_invite_returns_410(self, client, app_with_association):
        from association.models import ConviteProfissionalInstituicao
        from models import db
        with app_with_association.app_context():
            expired = ConviteProfissionalInstituicao(
                associacao_id=1, convidado_por_id=1,
                nome="Old", email="old@test.com",
                role="secretary", invite_type="staff",
                token="EXPIRED_TOKEN",
                expires_at=datetime.utcnow() - timedelta(days=1),  # expirado
            )
            db.session.add(expired)
            db.session.commit()

        res = client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "EXPIRED_TOKEN",
                "nome": "Old", "email": "old@test.com",
            },
        )
        assert res.status_code == 410

        res2 = client.get("/api/association/professional-invites/EXPIRED_TOKEN")
        assert res2.status_code == 410


# ═══════════════════════════════════════════════════════════════════════
# 8. Audit logs
# ═══════════════════════════════════════════════════════════════════════

class TestAuditLogs:

    def test_invite_create_logs(self, client, app_with_association):
        from models_extra import AuditLog
        from models import db
        token = _make_token(app_with_association, 1)
        client.post(
            "/api/association/associations/1/professional-invites",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "nome": "Audit Test", "email": "audit@test.com",
                "invite_type": "staff", "role": "secretary",
            },
        )
        with app_with_association.app_context():
            entries = AuditLog.query.filter_by(action="invite.create").all()
            assert any(
                e.details and e.details.get("invite_type") == "staff"
                for e in entries
            )

    def test_invite_revoke_logs(self, client, app_with_association):
        from models_extra import AuditLog
        token = _make_token(app_with_association, 1)
        client.post(
            "/api/association/professional-invites/1/revoke",
            headers={"Authorization": f"Bearer {token}"},
        )
        with app_with_association.app_context():
            entries = AuditLog.query.filter_by(action="invite.revoke").all()
            assert len(entries) >= 1
            assert entries[0].details.get("invite_type") == "staff"

    def test_invite_accept_logs(self, client, app_with_association):
        from models_extra import AuditLog
        client.post(
            "/api/cadastro_profissionais/solicitar-cadastro-staff",
            json={
                "convite_token": "VALID_STAFF_TOKEN",
                "nome": "Maria Silva",
                "email": "maria@test.com",
            },
        )
        with app_with_association.app_context():
            entries = AuditLog.query.filter_by(action="invite.accept").all()
            assert len(entries) >= 1
            assert entries[0].details.get("invite_type") == "staff"
            assert entries[0].details.get("role") == "secretary"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
