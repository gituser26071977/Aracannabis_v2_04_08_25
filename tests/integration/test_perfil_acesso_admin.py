"""Testes do perfil de acesso (admin tem acesso pleno).

Cobre a correção: admin/superadmin SEMPRE têm acesso pleno (solo),
independente do perfil_acesso declarado — podem acessar pacientes
(assistencial) e faturamento (administrativo).
"""

from __future__ import annotations

import pytest

from config import TestingConfig
from app_cors_livre import create_app
from models import db, Profissional
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


def _profissional(role, perfil_acesso, usuario):
    return Profissional(
        nome=f"Prof {usuario}",
        usuario=usuario,
        email=f"{usuario}@teste.com",
        crm=f"CRM-{usuario.upper()[:4]}",
        uf_crm="SE",
        senha=generate_password_hash("Teste@123456"),
        role=role,
        perfil_acesso=perfil_acesso,
        status_cadastro="aprovado",
    )


class TestAdminAcessoPleno:
    def REDACTED(self, app):
        """Admin com perfil 'administrativo' deve acessar pacientes (assistencial)."""
        from services.perfil_acesso import resolver_perfil, verificar_acesso

        admin = _profissional("admin", "administrativo", "admin.pleno")
        assert resolver_perfil(admin) == "solo"
        assert verificar_acesso(admin, "/api/pacientes/") is True
        assert verificar_acesso(admin, "/api/faturamento/") is True

    def test_superadmin_acesso_pleno(self, app):
        from services.perfil_acesso import resolver_perfil, verificar_acesso

        sa = _profissional("superadmin", "assistencial", "super.pleno")
        assert resolver_perfil(sa) == "solo"
        assert verificar_acesso(sa, "/api/pacientes/") is True

    def REDACTED(self, app):
        """Médico (assistencial) acessa pacientes mas não faturamento."""
        from services.perfil_acesso import resolver_perfil, verificar_acesso

        medico = _profissional("profissional", "assistencial", "medico.area")
        assert resolver_perfil(medico) == "assistencial"
        assert verificar_acesso(medico, "/api/pacientes/") is True
        assert verificar_acesso(medico, "/api/faturamento/") is False


class TestEndpointPacientes:
    def test_admin_lista_pacientes(self, app):
        """Admin autenticado consegue listar pacientes (sem 403)."""
        client = app.test_client()
        with app.app_context():
            admin = _profissional("admin", "administrativo", "admin.api")
            db.session.add(admin)
            db.session.commit()

        r = client.post("/api/auth/login", json={"usuario": "admin.api", "senha": "Teste@123456"})
        assert r.status_code == 200, r.data
        tok = r.get_json()["access_token"]

        r = client.get("/api/pacientes/", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200, r.data
