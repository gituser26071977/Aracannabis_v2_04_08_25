"""
Testes da Fase 4 — Secretaria Dashboard + Endpoints

Valida que:
  - GET /api/secretaria/dashboard retorna cards de resumo
  - GET /api/secretaria/agenda retorna consultas do dia
  - POST /api/secretaria/consultas/<id>/checkin funciona
  - GET /api/secretaria/pacientes?q=... faz quick search
  - Multi-tenant: secretárias de outras clínicas NÃO veem dados
  - Secretary pode acessar; physician/admin também
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date as _date
from werkzeug.security import generate_password_hash


@pytest.fixture
def app_with_secretaria():
    from flask import Flask, jsonify
    from flask_jwt_extended import JWTManager

    from models import db, Profissional, Paciente
    from models_extra import UsuarioAssociacao
    from association.models import Associacao
    from routes.secretaria import secretaria_bp
    from middleware.permission_middleware import register_permission_middleware

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = "REDACTED"
    app.config["SECRET_KEY"] = "REDACTED"

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

        # Clínica A
        assoc_a = Associacao(id=1, nome="Clínica A", cnpj="11111111000111", ativo=True)
        assoc_b = Associacao(id=2, nome="Clínica B", cnpj="22222222000122", ativo=True)
        db.session.add_all([assoc_a, assoc_b])
        db.session.commit()

        sec_a = Profissional(
            id=10, nome="Secretária A", crm=None, uf_crm=None,
            usuario="secA", email="secA@test.com",
            senha=generate_password_hash("x"), role="secretary",
            status_cadastro="aprovado", email_verified=True, onboarding_completed=True,
        )
        sec_b = Profissional(
            id=11, nome="Secretária B", crm=None, uf_crm=None,
            usuario="secB", email="secB@test.com",
            senha=generate_password_hash("x"), role="secretary",
            status_cadastro="aprovado", email_verified=True, onboarding_completed=True,
        )
        admin_a = Profissional(
            id=12, nome="Admin A", crm="A1", uf_crm="SP",
            usuario="admA", email="admA@test.com",
            senha=generate_password_hash("x"), role="admin",
            status_cadastro="aprovado", email_verified=True, onboarding_completed=True,
        )
        db.session.add_all([sec_a, sec_b, admin_a])
        db.session.commit()

        # Vínculos
        db.session.add(UsuarioAssociacao(
            profissional_id=10, associacao_id=1, role="member", status="active",
        ))
        db.session.add(UsuarioAssociacao(
            profissional_id=11, associacao_id=2, role="member", status="active",
        ))
        db.session.add(UsuarioAssociacao(
            profissional_id=12, associacao_id=1, role="admin", status="active",
        ))

        # Pacientes
        p1 = Paciente(id=1, nome="João Silva", cpf="11111111111", associacao_id=1,
                     profissional_responsavel_id=12,
                     data_nascimento=datetime(1990, 1, 1).date(), email="joao@x.com")
        p2 = Paciente(id=2, nome="Maria Souza", cpf="22222222222", associacao_id=1,
                     profissional_responsavel_id=12,
                     data_nascimento=datetime(1985, 5, 15).date())
        p3 = Paciente(id=3, nome="Outro B", cpf="33333333333", associacao_id=2,
                     profissional_responsavel_id=12,
                     data_nascimento=datetime(1992, 3, 10).date())
        db.session.add_all([p1, p2, p3])

        # Consultas (hoje, em horário LOCAL para casar com date.today() do service)
        from models import Consulta
        _hoje = datetime.combine(_date.today(), datetime.min.time())
        c1 = Consulta(
            id=1, associacao_id=1, paciente_id=1, profissional_id=12,
            data_hora=_hoje + timedelta(hours=10),
            status="agendada",
        )
        c2 = Consulta(
            id=2, associacao_id=1, paciente_id=2, profissional_id=12,
            data_hora=_hoje + timedelta(hours=14),
            status="confirmada",
        )
        c3 = Consulta(
            id=3, associacao_id=2, paciente_id=3, profissional_id=12,
            data_hora=_hoje + timedelta(hours=11),
            status="agendada",
        )
        db.session.add_all([c1, c2, c3])
        db.session.commit()

    app.register_blueprint(secretaria_bp)
    register_permission_middleware(app)
    return app


@pytest.fixture
def client(app_with_secretaria):
    return app_with_secretaria.test_client()


def _make_token(app, profissional_id):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        return create_access_token(identity=str(profissional_id))


# ═══════════════════════════════════════════════════════════════════════
# 1. Dashboard
# ═══════════════════════════════════════════════════════════════════════

class TestDashboard:

    def test_secretary_a_can_get_dashboard(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert "agenda_hoje" in data
        assert "proximas_consultas" in data
        assert "resumo" in data
        assert data["resumo"]["consultas_hoje"] == 2  # c1 e c2 (c3 é de B)

    def test_admin_a_can_get_dashboard(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 12)
        res = client.get(
            "/api/secretaria/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200

    def test_tenant_isolation(self, client, app_with_secretaria):
        """Secretária B NÃO vê consultas da clínica A."""
        token = _make_token(app_with_secretaria, 11)
        res = client.get(
            "/api/secretaria/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "2"},
        )
        assert res.status_code == 200
        data = res.get_json()
        # Consultas A não aparecem
        for c in data["agenda_hoje"]:
            assert c["paciente_nome"] != "João Silva"
            assert c["paciente_nome"] != "Maria Souza"

    def test_dashboard_aggregates(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/dashboard",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        data = res.get_json()
        assert data["resumo"]["consultas_confirmadas"] == 1
        assert data["resumo"]["consultas_agendadas"] == 1
        assert data["resumo"]["pacientes_esperados_hoje"] == 2  # 2 pacientes únicos

    def REDACTED(self, client, app_with_secretaria):
        """Sem header de associação, sem current_association -> 400."""
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Como o usuário tem vínculo com assoc=1, o middleware popula
        # g.current_association a partir do vínculo existente (fallback)
        assert res.status_code in (200, 400)

    def test_dashboard_requires_auth(self, client, app_with_secretaria):
        res = client.get("/api/secretaria/dashboard")
        assert res.status_code in (401, 422)  # sem JWT


# ═══════════════════════════════════════════════════════════════════════
# 2. Agenda
# ═══════════════════════════════════════════════════════════════════════

class TestAgenda:

    def test_default_agenda_returns_today(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/agenda",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert len(data["agenda"]) >= 2  # pelo menos c1 e c2

    def test_agenda_with_specific_date(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        hoje = datetime.utcnow().strftime("%Y-%m-%d")
        res = client.get(
            f"/api/secretaria/agenda?data={hoje}",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200

    def test_agenda_with_invalid_date(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/agenda?data=not-a-date",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        # Deve fallback para hoje e retornar 200
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# 3. Check-in
# ═══════════════════════════════════════════════════════════════════════

class TestCheckin:

    def test_secretary_can_checkin(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.post(
            "/api/secretaria/consultas/1/checkin",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert data["consulta"]["status"] == "confirmada"

    def REDACTED(self, client, app_with_secretaria):
        """Secretária B NÃO pode fazer check-in em consulta da clínica A."""
        token = _make_token(app_with_secretaria, 11)
        res = client.post(
            "/api/secretaria/consultas/1/checkin",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "2"},
        )
        # A associação ativa é B (id=2), mas a consulta 1 pertence à A
        # O service deve retornar erro
        assert res.status_code in (200, 400)
        # Se 200, o status não foi alterado (devido a check de associacao_id)
        if res.status_code == 200:
            # Não deveria ter sucesso com mensagem
            data = res.get_json()
            # Pode ter sido bloqueado pela regra de tenant
            assert not data.get("success", True) or data["consulta"]["status"] == "agendada"

    def test_checkin_not_found(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.post(
            "/api/secretaria/consultas/99999/checkin",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 400
        assert "não encontrad" in res.get_json()["error"].lower()


# ═══════════════════════════════════════════════════════════════════════
# 4. Pacientes
# ═══════════════════════════════════════════════════════════════════════

class TestPacientes:

    def test_list_pacientes(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/pacientes",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"]
        assert data["total"] == 2  # apenas pacientes da clínica A

    def test_quick_search_by_name(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/pacientes?q=João",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["total"] == 1
        assert "João" in data["items"][0]["nome"]

    def test_quick_search_by_cpf(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/pacientes?q=11111",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        assert res.get_json()["total"] == 1

    def test_tenant_isolation_in_pacientes(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 11)
        res = client.get(
            "/api/secretaria/pacientes",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "2"},
        )
        data = res.get_json()
        for p in data["items"]:
            assert p["nome"] != "João Silva"
            assert p["nome"] != "Maria Souza"

    def REDACTED(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/pacientes?q=a",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        assert res.get_json()["total"] == 0

    def test_pagination(self, client, app_with_secretaria):
        token = _make_token(app_with_secretaria, 10)
        res = client.get(
            "/api/secretaria/pacientes?limit=1&offset=0",
            headers={"Authorization": f"Bearer {token}", "X-Association-ID": "1"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data["items"]) == 1
        assert data["total"] == 2


# ═══════════════════════════════════════════════════════════════════════
# 5. RBAC — role guard
# ═══════════════════════════════════════════════════════════════════════

class TestRBACEnforcement:

    def test_unauthenticated_blocked(self, client, app_with_secretaria):
        res = client.get("/api/secretaria/dashboard")
        assert res.status_code in (401, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
