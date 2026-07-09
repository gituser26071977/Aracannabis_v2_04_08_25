import unittest
import json
from app_cors_livre import create_app
from unittest.mock import patch, MagicMock
import os


# Patch global aplicado antes do import do módulo — necessário porque
# `services.email_service` não expõe uma instância `email_service` em
# escopo de módulo (apenas a classe EmailService). O patch substitui a
# classe por uma versão mockada que não dispara SMTP real.
EMAIL_PATCHER = patch(
    'services.email_service.EmailService',
    new=MagicMock(),
)
EMAIL_PATCHER.start()


class CadastroProfissionaisTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # =====================================================================
    # rc.15 — profissional de saúde (CRM/CRP/COREN/CRN/CREFITO)
    # Contrato atual: 201 sucesso, 409 email dup, 409 crm dup, 400 inválido.
    # =====================================================================

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

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('Solicitação enviada', data['message'])

    def REDACTED(self):
        """Testa o bloqueio de cadastro com e-mail duplicado."""
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

        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Email já cadastrado')

    def REDACTED(self):
        """Testa o bloqueio de cadastro com CRM duplicado (partial unique)."""
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

        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Registro já cadastrado')

    def test_validacao_campos_obrigatorios(self):
        """Testa a validação de campos obrigatórios (nome + email)."""
        for campo in ('nome', 'email'):
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

    # =====================================================================
    # rc.16 — staff/secretária (conselho_tipo='NONE') sem CRM/UF
    # Antes do fix: 409 "Dados duplicados." (NotNullViolation mascarada).
    # Depois do fix: 201 sucesso + múltiplos staffs sem colidir.
    # =====================================================================

    def REDACTED(self):
        """Staff (conselho_tipo='NONE') sem CRM/UF deve ser aceito (201)."""
        payload = {
            "nome": "Maria Secretária",
            "email": "maria.staff@teste.com",
            "crm": "",
            "uf_crm": "",
            "telefone": "11999999999",
            "especialidade": "",
            "instituicao": "Clínica Y",
            "tipo_vinculo": "pessoal",
            "conselho_tipo": "NONE",
        }
        response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('id', data)

    def REDACTED(self):
        """Múltiplos staffs com NULL/NULL não devem colidir (partial unique)."""
        primeiro = {
            "nome": "João Gestor",
            "email": "joao.gestor@teste.com",
            "crm": "",
            "uf_crm": "",
            "tipo_vinculo": "pessoal",
            "conselho_tipo": "NONE",
        }
        segundo = {
            "nome": "Ana Administrativa",
            "email": "ana.admin@teste.com",
            "crm": "",
            "uf_crm": "",
            "tipo_vinculo": "pessoal",
            "conselho_tipo": "NONE",
        }
        r1 = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                              data=json.dumps(primeiro),
                              content_type='application/json')
        r2 = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                              data=json.dumps(segundo),
                              content_type='application/json')

        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)

    def REDACTED(self):
        """Staff com email duplicado deve retornar 409 'Email já cadastrado'."""
        payload = {
            "nome": "Maria Secretária",
            "email": "maria.staff.dup@teste.com",
            "crm": "",
            "uf_crm": "",
            "tipo_vinculo": "pessoal",
            "conselho_tipo": "NONE",
        }
        r1 = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                              data=json.dumps(payload),
                              content_type='application/json')
        self.assertEqual(r1.status_code, 201)

        payload["nome"] = "Maria Segunda"
        r2 = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                              data=json.dumps(payload),
                              content_type='application/json')

        self.assertEqual(r2.status_code, 409)
        data = json.loads(r2.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'Email já cadastrado')

    def REDACTED(self):
        """CRM com formato inválido deve retornar 400 com mensagem específica."""
        payload = {
            "nome": "Dr Foo",
            "email": "dr.foo.invalido@teste.com",
            "crm": "INVALID_X",
            "uf_crm": "SP",
            "tipo_vinculo": "pessoal",
            "conselho_tipo": "CRM",
        }
        response = self.client.post('/cadastro-profissionais/solicitar-cadastro',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data.get('conselho_tipo'), 'CRM')


if __name__ == '__main__':
    os.environ['FLASK_ENV'] = 'testing'
    unittest.main()