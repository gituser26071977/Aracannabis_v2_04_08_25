"""
Tests para gating por plano em endpoints de Clínica.

Cobre:
  - Plano básico recebe 403 em GET /my-associations (com plan_enforcement ON)
  - Plano básico recebe 403 em POST
  - Plano premium recebe 200
  - Plano enterprise recebe 200
  - Admin bypass recebe 200 (não 403)
"""
import unittest
import os
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("TESTING", "1")

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Plano, Assinatura
from models_extra import UsuarioAssociacao
from association.models import Associacao


def _plan_enforcement(value):
    """Helper: mock do feature flag."""
    return patch(
        'routes.auth_decorators.FeatureFlagService.is_enabled',
        return_value=value,
    )


class TestPlanGating(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Planos
            self.plano_basico = Plano(
                nome='Básico', slug='basico',
                preco_mensal=49.90, permite_gestao_clinica=False,
            )
            self.plano_premium = Plano(
                nome='Premium', slug='premium',
                preco_mensal=199.90, permite_gestao_clinica=True,
            )
            self.plano_enterprise = Plano(
                nome='Enterprise', slug='enterprise',
                preco_mensal=499.90, permite_gestao_clinica=True,
            )
            db.session.add_all([self.plano_basico, self.plano_premium, self.plano_enterprise])
            db.session.flush()

            # Usuários em cada plano
            self.user_basico = self._make_user('basico@test.com', 'CRM-1', self.plano_basico)
            self.user_premium = self._make_user('premium@test.com', 'CRM-2', self.plano_premium)
            self.user_enterprise = self._make_user('enterprise@test.com', 'CRM-3', self.plano_enterprise)

            # Superadmin global (bypass)
            self.user_admin = Profissional(
                nome='Admin Master',
                email='admin@test.com',
                crm='ADMIN-1',
                uf_crm='SP',
                conselho_tipo='NONE',
                usuario='admin_user',
                senha='x',
                role='admin',
            )
            db.session.add(self.user_admin)
            db.session.commit()

            # Captura IDs para uso fora do app context
            self._user_basico_id = self.user_basico.id
            self._user_premium_id = self.user_premium.id
            self._user_enterprise_id = self.user_enterprise.id
            self._user_admin_id = self.user_admin.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _make_user(self, email, crm, plano):
        user = Profissional(
            nome=f'User {email}',
            email=email,
            crm=crm,
            uf_crm='SP',
            conselho_tipo='CRM',
            usuario=email.split('@')[0],
            senha='x',
            role='profissional',
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(Assinatura(
            profissional_id=user.id,
            plano_id=plano.id,
            status='active',
        ))
        db.session.commit()
        return user

    def _login(self, user):
        from flask_jwt_extended import create_access_token
        with self.app.app_context():
            user_id = db.session.merge(user).id
            return create_access_token(identity=str(user_id))

    def _login_id(self, user_id):
        """Login direto por ID (evita merge em object detached)."""
        from flask_jwt_extended import create_access_token
        with self.app.app_context():
            return create_access_token(identity=str(user_id))

    def _auth(self, token):
        return {'Authorization': f'Bearer {token}'}

    def _create_clinica_for(self, user):
        """Cria clínica e vincula user como admin."""
        with self.app.app_context():
            user_id = db.session.merge(user).id
            email = db.session.merge(user).email
            c = Associacao(
                nome=f'Clinica {email}',
                cnpj='11222333000181',
                email=email,
                ativo=True,
            )
            db.session.add(c)
            db.session.flush()
            db.session.add(UsuarioAssociacao(
                profissional_id=user_id,
                associacao_id=c.id,
                role='admin',
                status='active',
            ))
            db.session.commit()
            return c.id

    def test_basico_recebe_403(self):
        """Plano básico NÃO pode listar clínicas (enforcement ON)."""
        with _plan_enforcement(True):
            token = self._login(self.user_basico)

            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth(token),
            )
        self.assertEqual(resp.status_code, 403)
        body = resp.json
        self.assertIn('plan_required', body)
        self.assertEqual(body['plan_required'], 'premium')
        self.assertEqual(body['upgrade_url'], '/planos')
        self.assertFalse(body['permite_gestao_clinica'])

    def test_basico_recebe_403_em_post(self):
        """Plano básico NÃO pode criar clínica (enforcement ON)."""
        with _plan_enforcement(True):
            token = self._login(self.user_basico)

            resp = self.client.post(
                '/api/association/associations',
                json={'nome': 'Teste', 'cnpj': '11222333000181'},
                headers=self._auth(token),
            )
        self.assertEqual(resp.status_code, 403)

    def test_premium_recebe_200(self):
        """Plano premium pode listar (enforcement ON)."""
        with _plan_enforcement(True):
            self._create_clinica_for(self.user_premium)
            token = self._login(self.user_premium)

            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth(token),
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertGreaterEqual(len(resp.json), 1)

    def test_enterprise_recebe_200(self):
        """Plano enterprise pode criar + listar (enforcement ON)."""
        with _plan_enforcement(True):
            token = self._login(self.user_enterprise)

            resp = self.client.post(
                '/api/association/associations',
                json={'nome': 'Enterprise Clinic', 'cnpj': '11222333000181'},
                headers=self._auth(token),
            )
            self.assertEqual(resp.status_code, 201)

            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth(token),
            )
        self.assertEqual(resp.status_code, 200)

    def test_admin_bypass(self):
        """Admin global recebe 200 mesmo com enforcement ON (sem clínica vinculada, lista vazia)."""
        with _plan_enforcement(True):
            token = self._login(self.user_admin)

            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth(token),
            )
        # Admin sem vínculo recebe 200 com lista vazia (não 403)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)

    def REDACTED(self):
        """Com plan_enforcement OFF, plano básico também acessa (dev mode)."""
        with _plan_enforcement(False):
            self._create_clinica_for(self.user_basico)
            token = self._login(self.user_basico)

            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth(token),
            )
        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
