
import unittest
import json
from unittest.mock import patch, MagicMock
from app_cors_livre import create_app
from models import db, SolicitacoesCadastro
import os

class RegistrationAIVerificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Mock AI Manager
        self.ai_patcher = patch('services.registration_verification_service.ai_manager')
        self.mock_ai_manager = self.ai_patcher.start()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.ai_patcher.stop()

    @patch('services.registration_verification_service.validate_crm_format')
    @patch('services.registration_verification_service.check_duplicate_crm')
    @patch('services.registration_verification_service.validate_email_format')
    @patch('services.registration_verification_service.verify_email_domain')
    @patch('services.registration_verification_service.detect_disposable_email')
    @patch('services.registration_verification_service.check_duplicate_email')
    @patch('services.registration_verification_service.analyze_registration_timing')
    def REDACTED(self, mock_timing, mock_dup_email, mock_disp_email, mock_dom_email, mock_format_email, mock_dup_crm, mock_format_crm):
        """Testa o fluxo de verificação com auto-aprovação da IA."""
        # Criar uma solicitação fake
        solicitacao = SolicitacoesCadastro(
            nome="Dr. Teste IA",
            email="teste.ia@example.com",
            crm="123456",
            uf_crm="SP",
            especialidade="Clínica Médica",
            status="pendente"
        )
        db.session.add(solicitacao)
        db.session.commit()

        # Mock da resposta da IA
        self.mock_ai_manager.chat_completion.return_value = {
            'content': json.dumps({
                "recommendation": "auto_approve",
                "justification": "Tudo parece correto. CRM válido e email profissional.",
                "confidence_score": 0.95,
                "highlighted_issues": []
            })
        }

        # Mocks para CRM
        mock_format_crm.return_value = {"valid": True, "confidence": 1.0}
        mock_dup_crm.return_value = {"duplicate": False, "confidence": 1.0}
        
        # Mocks para Email
        mock_format_email.return_value = {"valid": True, "confidence": 1.0}
        mock_dom_email.return_value = {"valid": True, "confidence": 1.0}
        mock_disp_email.return_value = {"disposable": False, "confidence": 1.0}
        mock_dup_email.return_value = {"duplicate": False, "confidence": 1.0}
        
        # Mocks para Fraude/Timing
        mock_timing.return_value = {"risk": "low", "confidence": 1.0}

        from services.registration_verification_service import RegistrationVerificationService
        service = RegistrationVerificationService()
        result = service.verify_registration(solicitacao.id)

        self.assertTrue(result['auto_approve'])
        self.assertEqual(result['recommendation'], "auto_approve")
        
        # Recarregar do banco para verificar se salvou
        solicitacao_atualizada = db.session.get(SolicitacoesCadastro, solicitacao.id)
        verif_data = json.loads(solicitacao_atualizada.verificacao_automatica)
        self.assertEqual(verif_data['recommendation'], "auto_approve")

    @patch('services.registration_verification_service.validate_crm_format')
    @patch('services.registration_verification_service.check_duplicate_crm')
    @patch('services.registration_verification_service.validate_email_format')
    @patch('services.registration_verification_service.verify_email_domain')
    @patch('services.registration_verification_service.detect_disposable_email')
    @patch('services.registration_verification_service.check_duplicate_email')
    @patch('services.registration_verification_service.analyze_registration_timing')
    def REDACTED(self, mock_timing, mock_dup_email, mock_disp_email, mock_dom_email, mock_format_email, mock_dup_crm, mock_format_crm):
        """Testa o fluxo de verificação com recomendação de revisão manual."""
        solicitacao = SolicitacoesCadastro(
            nome="Dr. Risco",
            email="risco@descartavel.com",
            crm="654321",
            uf_crm="RJ",
            status="pendente"
        )
        db.session.add(solicitacao)
        db.session.commit()

        # Mock da resposta da IA para revisão manual
        self.mock_ai_manager.chat_completion.return_value = {
            'content': json.dumps({
                "recommendation": "manual_review",
                "justification": "Email parece suspeito.",
                "confidence_score": 0.6,
                "highlighted_issues": ["Email descartável detectado"]
            })
        }

        # Mocks para CRM
        mock_format_crm.return_value = {"valid": True, "confidence": 1.0}
        mock_dup_crm.return_value = {"duplicate": False, "confidence": 1.0}
        
        # Mocks para Email (Falha no domínio/descartável)
        mock_format_email.return_value = {"valid": True, "confidence": 1.0}
        mock_dom_email.return_value = {"valid": False, "confidence": 0.5}
        mock_disp_email.return_value = {"disposable": True, "confidence": 1.0}
        mock_dup_email.return_value = {"duplicate": False, "confidence": 1.0}
        
        # Mocks para Fraude/Timing
        mock_timing.return_value = {"risk": "medium", "confidence": 0.8}

        from services.registration_verification_service import RegistrationVerificationService
        service = RegistrationVerificationService()
        result = service.verify_registration(solicitacao.id)

        self.assertFalse(result['auto_approve'])
        self.assertEqual(result['recommendation'], "manual_review")
        
        solicitacao_atualizada = db.session.get(SolicitacoesCadastro, solicitacao.id)
        verif_data = json.loads(solicitacao_atualizada.verificacao_automatica)
        self.assertIn("Email descartável detectado", verif_data['issues'])

if __name__ == '__main__':
    unittest.main()
