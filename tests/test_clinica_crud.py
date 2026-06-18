"""
Tests para CRUD completo de Clínica (PUT/DELETE) com soft delete.

Cobre:
  - PUT atualiza dados da clínica
  - PUT exige que user seja admin da clínica
  - PUT valida CNPJ
  - DELETE soft-deleta (ativo=False) sem remover do banco
  - DELETE exige que user seja admin
  - DELETE gera entrada em audit_log
  - GET /my-associations filtra ativos
"""
import unittest
import os
from datetime import datetime
from unittest.mock import patch

os.environ.setdefault("TESTING", "1")

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Profissional, Plano, Assinatura
from association.models import Associacao
from models_extra import UsuarioAssociacao, AuditLog


class TestClinicaCRUD(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Plano premium com flag habilitada
            self.plano_premium = Plano(
                nome='Premium',
                slug='premium',
                preco_mensal=199.90,
                permite_gestao_clinica=True,
            )
            db.session.add(self.plano_premium)
            db.session.commit()

            # User premium admin
            self.user_premium = Profissional(
                nome='Dr Premium',
                email='premium@test.com',
                crm='CRM-SP-111',
                uf_crm='SP',
                conselho_tipo='CRM',
                usuario='premium_user',
                senha='x',
                role='profissional',
            )
            db.session.add(self.user_premium)
            db.session.flush()
            db.session.add(Assinatura(
                profissional_id=self.user_premium.id,
                plano_id=self.plano_premium.id,
                status='active',
            ))

            # User premium membro (não-admin) da clínica
            self.user_membro = Profissional(
                nome='Dr Membro',
                email='membro@test.com',
                crm='CRM-SP-333',
                uf_crm='SP',
                conselho_tipo='CRM',
                usuario='membro_user',
                senha='x',
                role='profissional',
            )
            db.session.add(self.user_membro)
            db.session.flush()
            db.session.add(Assinatura(
                profissional_id=self.user_membro.id,
                plano_id=self.plano_premium.id,
                status='active',
            ))

            # Clínica já existente
            self.clinica = Associacao(
                nome='Clínica Aurora',
                slug='clinica-aurora',
                cnpj='11222333000181',
                email='contato@aurora.com',
                endereco='Rua X, 100',
                telefone='11999990000',
                ativo=True,
            )
            db.session.add(self.clinica)
            db.session.flush()

            # user_premium é admin
            db.session.add(UsuarioAssociacao(
                profissional_id=self.user_premium.id,
                associacao_id=self.clinica.id,
                role='admin',
                status='active',
            ))
            # user_membro é membro comum
            db.session.add(UsuarioAssociacao(
                profissional_id=self.user_membro.id,
                associacao_id=self.clinica.id,
                role='member',
                status='active',
            ))

            db.session.commit()

            # Captura IDs para uso fora do app context
            self._user_premium_id = self.user_premium.id
            self._user_membro_id = self.user_membro.id
            self._clinica_id = self.clinica.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, user):
        """Cria JWT válido para o user (in-process)."""
        from flask_jwt_extended import create_access_token
        with self.app.app_context():
            # Acessa o ID enquanto a sessão está ativa
            user_id = db.session.merge(user).id
            return create_access_token(identity=str(user_id))

    def _auth_headers(self, token):
        return {'Authorization': f'Bearer {token}'}

    def _patch_plan_enforcement_off(self):
        """Mock que faz decorator acreditar que plan_enforcement está off."""
        return patch(
            'routes.auth_decorators.FeatureFlagService.is_enabled',
            return_value=False,
        )

    # --- Testes ---

    def REDACTED(self):
        """Admin da clínica pode atualizar dados."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_premium)

            resp = self.client.put(
                f'/api/association/associations/{self.clinica.id}',
                json={'nome': 'Aurora Centro', 'telefone': '1133334444'},
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 200, resp.json)
        self.assertEqual(resp.json['nome'], 'Aurora Centro')
        self.assertEqual(resp.json['telefone'], '1133334444')

    def test_put_bloqueia_membro_nao_admin(self):
        """Membro comum NÃO pode atualizar (não é admin)."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_membro)

            resp = self.client.put(
                f'/api/association/associations/{self.clinica.id}',
                json={'nome': 'Hack'},
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 403)
        self.assertIn('administrador', resp.json.get('error', '').lower())

    def test_put_valida_cnpj(self):
        """CNPJ inválido retorna 400."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_premium)

            resp = self.client.put(
                f'/api/association/associations/{self.clinica.id}',
                json={'cnpj': '00000000000000'},
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 400)
        self.assertIn('cnpj', resp.json.get('error', '').lower())

    def test_delete_soft_delete(self):
        """DELETE seta ativo=False mas mantém linha no banco."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_premium)

            resp = self.client.delete(
                f'/api/association/associations/{self.clinica.id}',
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 200, resp.json)
        self.assertTrue(resp.json['deleted'])
        self.assertFalse(resp.json['ativo'])

        # Linha ainda existe
        with self.app.app_context():
            assoc = Associacao.query.get(self.clinica.id)
            self.assertIsNotNone(assoc)
            self.assertFalse(assoc.ativo)

    def REDACTED(self):
        """Membro comum NÃO pode desativar."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_membro)

            resp = self.client.delete(
                f'/api/association/associations/{self.clinica.id}',
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 403)

    def test_delete_gera_audit_log(self):
        """DELETE cria entrada no audit_log (LGPD)."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_premium)

            self.client.delete(
                f'/api/association/associations/{self.clinica.id}',
                headers=self._auth_headers(token),
            )

        with self.app.app_context():
            audit = AuditLog.query.filter_by(
                action='clinica.desativada',
            ).filter(
                AuditLog.resource_id == str(self.clinica.id)
            ).first()
            self.assertIsNotNone(audit, 'AuditLog entry not found')
            self.assertEqual(audit.resource_type, 'associacao')
            self.assertTrue(audit.details.get('soft_delete'))

    def test_list_filtra_ativas(self):
        """GET /my-associations filtra ativo=True após soft delete."""
        with self._patch_plan_enforcement_off():
            token = self._login(self.user_premium)

            # Desativa
            self.client.delete(
                f'/api/association/associations/{self.clinica.id}',
                headers=self._auth_headers(token),
            )

            # Lista
            resp = self.client.get(
                '/api/association/my-associations',
                headers=self._auth_headers(token),
            )
        self.assertEqual(resp.status_code, 200)
        ids = [c['id'] for c in resp.json]
        self.assertNotIn(self.clinica.id, ids)


if __name__ == '__main__':
    unittest.main()
