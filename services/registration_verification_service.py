"""
Serviço de verificação automática de cadastros usando agentes IA
"""
from .crew_agents import Agent, tool
from .ai_agents import ai_manager
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
import logging

logger = logging.getLogger(__name__)

class RegistrationVerificationService:
    """Serviço para verificação automática de solicitações de cadastro"""
    
    def __init__(self):
        # Os agentes agora serão usados para a decisão final baseada nos dados das ferramentas
        self.decision_agent = self._create_decision_agent()
    
    def _create_decision_agent(self):
        """Cria agente de decisão final para o cadastro"""
        # Em modo simulado (sem CrewAI), o Agent é uma classe simples ou IA direta
        return Agent(
            role="Auditor de Cadastros Médicos",
            goal="Analisar os dados de validação e decidir se o cadastro é legítimo",
            backstory="""Você é um auditor sênior especializado em conformidade médica.
            Sua função é revisar os resultados das ferramentas automáticas e dar o veredito final
            sobre a aprovação de novos profissionais no AraOS.""",
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
            fraud_result,
            solicitacao
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
    
    def _aggregate_results(self, crm_result: dict, email_result: dict, fraud_result: dict, solicitacao: SolicitacoesCadastro) -> dict:
        """
        Agrega resultados das ferramentas e usa IA para decisão final
        """
        # Preparar contexto para a IA
        context = {
            "profissional": {
                "nome": solicitacao.nome,
                "email": solicitacao.email,
                "crm": solicitacao.crm,
                "uf": solicitacao.uf_crm,
                "especialidade": solicitacao.especialidade
            },
            "validacoes": {
                "crm": crm_result,
                "email": email_result,
                "fraude": fraud_result
            }
        }

        system_prompt = """Você é um Auditor de Conformidade Médica da Arapath. 
        Analise os dados de validação técnica e decida se o profissional deve ser aprovado, 
        revisado manualmente ou rejeitado.
        
        CRITÉRIOS DE AUTO-APROVAÇÃO:
        1. CRM válido e sem duplicidade.
        2. Email válido, corporativo/comum (não descartável) e sem duplicidade.
        3. Risco de fraude baixo.
        4. Alta confiança nas ferramentas técnicas (>85%).

        Retorne EXCLUSIVAMENTE um JSON no seguinte formato:
        {
            "recommendation": "auto_approve" | "manual_review" | "reject",
            "justification": "Texto explicando o porquê da decisão",
            "confidence_score": 0.0 a 1.0,
            "highlighted_issues": ["Lista de problemas se houver"]
        }"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Dados para auditoria: {json.dumps(context, ensure_ascii=False)}"}
            ]
            
            response = ai_manager.chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=800
            )
            
            content = response['content']
            # Limpar markdown se houver
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
            
            ai_decision = json.loads(content.strip())
            # Garantir que as chaves existem
            if "highlighted_issues" not in ai_decision:
                ai_decision["highlighted_issues"] = []
        except Exception as e:
            logger.error(f"Erro na decisão da IA: {e}")
            # Fallback seguro
            ai_decision = {
                "recommendation": "manual_review",
                "justification": f"Erro no processamento da IA: {str(e)}",
                "confidence_score": 0.0,
                "highlighted_issues": ["Falha técnica na auditoria"]
            }

        auto_approve = ai_decision.get("recommendation") == "auto_approve"
        
        return {
            "auto_approve": auto_approve,
            "overall_confidence": ai_decision.get("confidence_score", 0.0),
            "crm_validation": crm_result,
            "email_validation": email_result,
            "fraud_detection": fraud_result,
            "issues": ai_decision.get("highlighted_issues", []),
            "recommendation": ai_decision.get("recommendation", "manual_review"),
            "justification": ai_decision.get("justification", ""),
            "summary": self._generate_summary(auto_approve, ai_decision.get("highlighted_issues", []), ai_decision.get("confidence_score", 0.0))
        }
    
    def _generate_summary(self, auto_approve: bool, issues: list, confidence: float) -> str:
        """Gera resumo da verificação"""
        if auto_approve:
            return f"✅ Verificação aprovada automaticamente pela IA (confiança: {confidence:.0%})"
        elif not issues:
            return f"⚠️ Revisão manual recomendada pela IA (confiança: {confidence:.0%})"
        else:
            return f"❌ Problemas detectados pela IA: {'; '.join(issues)}"
