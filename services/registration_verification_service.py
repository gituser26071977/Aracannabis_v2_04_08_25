"""
Serviço de verificação automática de cadastros usando agentes IA
"""
from crewai import Agent
from models import SolicitacoesCadastro, db
from services.registration_verification_tools import (
    validate_crm_format,
    check_duplicate_crm,
    validate_email_format,
    verify_email_domain,
    detect_disposable_email,
    check_duplicate_email,
    analyze_registration_timing
)
import json


class RegistrationVerificationService:
    """Serviço para verificação automática de solicitações de cadastro"""
    
    def __init__(self):
        self.crm_validator = self._create_crm_validator()
        self.email_verifier = self._create_email_verifier()
        self.fraud_detector = self._create_fraud_detector()
    
    def _create_crm_validator(self):
        """Cria agente validador de CRM"""
        return Agent(
            role="Validador de CRM",
            goal="Verificar se o CRM fornecido é válido e não está duplicado",
            backstory="""Você é um especialista em validação de registros profissionais.
            Sua função é verificar se o CRM fornecido está no formato correto e se não
            há duplicatas no sistema.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_email_verifier(self):
        """Cria agente verificador de email"""
        return Agent(
            role="Verificador de Email",
            goal="Validar se o email é legítimo e não é descartável",
            backstory="""Você é um especialista em validação de emails.
            Sua função é verificar se o email fornecido é válido, se o domínio existe,
            e se não é um serviço de email descartável.""",
            verbose=True,
            allow_delegation=False
        )
    
    def _create_fraud_detector(self):
        """Cria agente detector de fraude"""
        return Agent(
            role="Detector de Fraude",
            goal="Identificar padrões suspeitos em solicitações de cadastro",
            backstory="""Você é um especialista em detecção de fraudes.
            Sua função é analisar padrões de cadastro e identificar comportamentos
            suspeitos como duplicatas, timing anormal, ou dados inconsistentes.""",
            verbose=True,
            allow_delegation=False
        )
    
    def verify_registration(self, solicitacao_id: int) -> dict:
        """
        Executa verificação completa de uma solicitação
        
        Args:
            solicitacao_id: ID da solicitação a ser verificada
        
        Returns:
            dict com resultado da verificação
        """
        solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
        if not solicitacao:
            return {
                "success": False,
                "error": "Solicitação não encontrada"
            }
        
        # Executar verificações
        crm_result = self._verify_crm(solicitacao)
        email_result = self._verify_email(solicitacao)
        fraud_result = self._verify_fraud(solicitacao)
        
        # Agregar resultados
        final_result = self._aggregate_results(
            crm_result, 
            email_result, 
            fraud_result
        )
        
        # Salvar resultado na solicitação
        solicitacao.verificacao_automatica = json.dumps(final_result)
        db.session.commit()
        
        return final_result
    
    def _verify_crm(self, solicitacao: SolicitacoesCadastro) -> dict:
        """Verifica CRM"""
        results = {}
        
        # Validar formato
        format_check = validate_crm_format(solicitacao.crm, solicitacao.uf_crm)
        results['format'] = format_check
        
        # Verificar duplicata
        duplicate_check = check_duplicate_crm(solicitacao.crm, solicitacao.uf_crm, exclude_id=solicitacao.id)
        results['duplicate'] = duplicate_check
        
        # Determinar se é válido
        is_valid = format_check['valid'] and not duplicate_check['duplicate']
        confidence = min(format_check['confidence'], duplicate_check['confidence'])
        
        return {
            "valid": is_valid,
            "confidence": confidence,
            "details": results,
            "recommendation": "approve" if is_valid else "reject"
        }
    
    def _verify_email(self, solicitacao: SolicitacoesCadastro) -> dict:
        """Verifica email"""
        results = {}
        
        # Validar formato
        format_check = validate_email_format(solicitacao.email)
        results['format'] = format_check
        
        # Verificar domínio
        domain_check = verify_email_domain(solicitacao.email)
        results['domain'] = domain_check
        
        # Detectar descartável
        disposable_check = detect_disposable_email(solicitacao.email)
        results['disposable'] = disposable_check
        
        # Verificar duplicata
        duplicate_check = check_duplicate_email(solicitacao.email, exclude_id=solicitacao.id)
        results['duplicate'] = duplicate_check
        
        # Determinar se é válido
        is_valid = (
            format_check['valid'] and 
            domain_check['valid'] and 
            not disposable_check['disposable'] and
            not duplicate_check['duplicate']
        )
        
        confidence = min(
            format_check['confidence'],
            domain_check['confidence'],
            disposable_check['confidence'],
            duplicate_check['confidence']
        )
        
        return {
            "valid": is_valid,
            "confidence": confidence,
            "details": results,
            "recommendation": "approve" if is_valid else "review"
        }
    
    def _verify_fraud(self, solicitacao: SolicitacoesCadastro) -> dict:
        """Detecta fraude"""
        results = {}
        
        # Analisar timing
        timing_check = analyze_registration_timing(solicitacao.id)
        results['timing'] = timing_check
        
        # Calcular score de risco
        risk_score = 0.0
        if timing_check['risk'] == 'high':
            risk_score = 0.8
        elif timing_check['risk'] == 'medium':
            risk_score = 0.4
        else:
            risk_score = 0.1
        
        return {
            "risk_level": timing_check['risk'],
            "risk_score": risk_score,
            "confidence": timing_check['confidence'],
            "details": results,
            "recommendation": "approve" if risk_score < 0.5 else "review"
        }
    
    def _aggregate_results(self, crm_result: dict, email_result: dict, fraud_result: dict) -> dict:
        """
        Agrega resultados dos agentes em decisão final
        
        Args:
            crm_result: Resultado da verificação de CRM
            email_result: Resultado da verificação de email
            fraud_result: Resultado da detecção de fraude
        
        Returns:
            dict com decisão final
        """
        # Calcular confiança geral
        overall_confidence = (
            crm_result['confidence'] * 0.4 +
            email_result['confidence'] * 0.4 +
            fraud_result['confidence'] * 0.2
        )
        
        # Determinar se deve auto-aprovar
        auto_approve = (
            crm_result['valid'] and
            email_result['valid'] and
            fraud_result['risk_score'] < 0.5 and
            overall_confidence > 0.85
        )
        
        # Coletar issues
        issues = []
        if not crm_result['valid']:
            issues.append(f"CRM: {crm_result['details']['format'].get('reason', 'Inválido')}")
        if crm_result['details']['duplicate']['duplicate']:
            issues.append(f"CRM: {crm_result['details']['duplicate']['reason']}")
        if not email_result['valid']:
            for check_name, check_result in email_result['details'].items():
                if not check_result.get('valid', True) or check_result.get('duplicate', False) or check_result.get('disposable', False):
                    issues.append(f"Email: {check_result.get('reason', 'Problema detectado')}")
        if fraud_result['risk_score'] >= 0.5:
            issues.append(f"Fraude: {fraud_result['details']['timing']['reason']}")
        
        return {
            "auto_approve": auto_approve,
            "overall_confidence": overall_confidence,
            "crm_validation": crm_result,
            "email_validation": email_result,
            "fraud_detection": fraud_result,
            "issues": issues,
            "recommendation": "auto_approve" if auto_approve else "manual_review",
            "summary": self._generate_summary(auto_approve, issues, overall_confidence)
        }
    
    def _generate_summary(self, auto_approve: bool, issues: list, confidence: float) -> str:
        """Gera resumo da verificação"""
        if auto_approve:
            return f"✅ Verificação aprovada automaticamente (confiança: {confidence:.0%})"
        elif not issues:
            return f"⚠️ Revisão manual recomendada (confiança: {confidence:.0%})"
        else:
            return f"❌ Problemas detectados: {'; '.join(issues)}"
