
import unittest
import json
from app_cors_livre import create_app
from unittest.mock import patch
import os

class CadastroProfissionaisTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Mock do serviço de e-mail para evitar o envio de e-mails reais
        self.email_patcher = patch('services.email_service.email_service')
        self.mock_email_service = self.email_patcher.start()
        self.mock_email_service.send_approval_email.return_value = True
        self.mock_email_service.send_rejection_email.return_value = True

    def tearDown(self):
        self.email_patcher.stop()

    def test_solicitar_cadastro_sucesso(self):
        """Testa o cadastro de um novo profissional com sucesso."""
        novo_profissional = {
            "nome": "Dr. Novo Medico",
            "email": "novo.medico@teste.com",
            "crm": "987654",
            "uf_crm": "SP",
            "telefone": "11987654321",
            "especialidade": "Cardiologia",
            "instituicao": "Hospital Teste"
        }
        
        response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                    data=json.dumps(novo_profissional),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Solicitação de cadastro enviada com sucesso', data['message'])

    def test_solicitar_cadastro_email_duplicado(self):
        """Testa o bloqueio de cadastro com e-mail duplicado."""
        # Primeiro, cadastra um profissional
        profissional_existente = {
            "nome": "Dr. Ja Existe",
            "email": "existente@teste.com",
            "crm": "112233",
            "uf_crm": "RJ",
            "especialidade": "Neurologia"
        }
        self.client.post('/cadastro-profissionais/solicitar-cadastro',
                         data=json.dumps(profissional_existente),
                         content_type='application/json')

        # Tenta cadastrar novamente com o mesmo e-mail
        novo_com_email_duplicado = {
            "nome": "Dr. Outro Nome",
            "email": "existente@teste.com",
            "crm": "334455",
            "uf_crm": "MG",
            "especialidade": "Psiquiatria"
        }
        response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                    data=json.dumps(novo_com_email_duplicado),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Email já cadastrado')

    def test_solicitar_cadastro_crm_duplicado(self):
        """Testa o bloqueio de cadastro com CRM duplicado."""
        # Primeiro, cadastra um profissional
        profissional_existente = {
            "nome": "Dr. CRM Unico",
            "email": "crm.unico@teste.com",
            "crm": "998877",
            "uf_crm": "BA",
            "especialidade": "Oncologia"
        }
        self.client.post('/cadastro-profissionais/solicitar-cadastro',
                         data=json.dumps(profissional_existente),
                         content_type='application/json')

        # Tenta cadastrar outro com o mesmo CRM
        novo_com_crm_duplicado = {
            "nome": "Dr. Outro Medico",
            "email": "outro.medico@teste.com",
            "crm": "998877",
            "uf_crm": "BA",
            "especialidade": "Clínica Médica"
        }
        response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                    data=json.dumps(novo_com_crm_duplicado),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'CRM já cadastrado')

    def test_validacao_campos_obrigatorios(self):
        """Testa a validação de campos obrigatórios."""
        campos_obrigatorios = ["nome", "email", "crm", "uf_crm"]
        for campo in campos_obrigatorios:
            dados_incompletos = {
                "nome": "Incompleto",
                "email": "incompleto@teste.com",
                "crm": "123123",
                "uf_crm": "SC"
            }
            del dados_incompletos[campo]
            
            response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                        data=json.dumps(dados_incompletos),
                                        content_type='application/json')
            
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['error'], f'Campo {campo} é obrigatório')

if __name__ == '__main__':
    # É importante garantir que o ambiente esteja configurado para teste
    # Por exemplo, usando um banco de dados de teste em memória ou um arquivo de teste
    os.environ['FLASK_ENV'] = 'testing'
    unittest.main()
