
import unittest
import json
from unittest.mock import patch, MagicMock
from app_cors_livre import create_app
from models import db, Sintoma, Paciente, Profissional
from association.models import Associacao
import os
from datetime import datetime

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-key'
    JWT_SECRET_KEY = 'jwt-test-key'

class SintomasUnitTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        
        # 1. Criar Associacao
        self.assoc = Associacao(nome="Assoc Teste", cnpj="12345678000199")
        db.session.add(self.assoc)
        db.session.flush()

        # 2. Criar Profissional
        self.prof = Profissional(
            nome="Dr. Teste",
            crm="12345",
            uf_crm="SP",
            usuario="drteste",
            senha="123"
        )
        db.session.add(self.prof)
        db.session.flush()

        # 3. Criar paciente de teste
        self.paciente = Paciente(
            nome="Paciente Teste",
            email="paciente@teste.com",
            cpf="12345678901",
            associacao_id=self.assoc.id,
            profissional_responsavel_id=self.prof.id,
            data_nascimento=datetime(1990, 1, 1).date()
        )
        db.session.add(self.paciente)
        db.session.commit()

        # Mock JWT identity NO MODULO DE ROTAS (onde é importado)
        self.patcher_jwt = patch('routes.sintomas.get_jwt_identity', return_value=str(self.prof.id))
        self.mock_jwt = self.patcher_jwt.start()
        
        # Mock verify_jwt_in_request (pode ser no original pois o decorator o chama)
        self.patcher_verify = patch('flask_jwt_extended.view_decorators.verify_jwt_in_request', return_value=None)
        self.mock_verify = self.patcher_verify.start()

    def tearDown(self):
        self.patcher_jwt.stop()
        self.patcher_verify.stop()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_listar_sintomas_padrao(self):
        """Testa listagem de sintomas padrão."""
        response = self.client.get('/api/sintomas/sintomas-padrao')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('sintomas_padrao', data)

    def test_registrar_e_listar_sintoma_paciente(self):
        """Testa o registro e listagem de sintomas de um paciente."""
        novo_sintoma = {
            "data": "2025-01-26",
            "sintoma": "Insônia",
            "intensidade": 8
        }
        # Nota: Como o decorator verifica o token, e estamos mockando a verificação,
        # o request deve passar mesmo sem header real.
        response = self.client.post(f'/api/sintomas/paciente/{self.paciente.id}',
                                    data=json.dumps(novo_sintoma),
                                    content_type='application/json',
                                    headers={'X-CSRF-Token': 'test-token'})
        
        if response.status_code != 201:
            print(f"DEBUG: Status {response.status_code}, Response: {response.data}")
            
        self.assertEqual(response.status_code, 201)
        
        response = self.client.get(f'/api/sintomas/paciente/{self.paciente.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['sintomas']), 1)
        self.assertEqual(data['sintomas'][0]['sintoma'], "Insônia")

    def test_dados_grafico(self):
        """Testa o endpoint de dados de gráfico."""
        s1 = Sintoma(paciente_id=self.paciente.id, data=datetime(2025, 1, 1).date(), sintoma="Dor", intensidade=5)
        s2 = Sintoma(paciente_id=self.paciente.id, data=datetime(2025, 1, 2).date(), sintoma="Dor", intensidade=7)
        db.session.add_all([s1, s2])
        db.session.commit()

        response = self.client.get(f'/api/sintomas/grafico/paciente/{self.paciente.id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(len(data['dados_grafico']) >= 1)

if __name__ == '__main__':
    unittest.main()
