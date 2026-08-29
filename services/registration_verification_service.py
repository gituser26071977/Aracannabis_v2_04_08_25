"""
Serviço de verificação automática de cadastros usando agentes IA
"""
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
        pass
    
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
        """Verifica CRM com validacao externa no conselho"""
        results = {}
        
        # Validar formato
        format_check = validate_crm_format(solicitacao.crm, solicitacao.uf_crm)
        results['format'] = format_check
        
        # Verificar duplicata
        duplicate_check = check_duplicate_crm(solicitacao.crm, solicitacao.uf_crm, exclude_id=solicitacao.id)
        results['duplicate'] = duplicate_check
        
        # Validar no conselho via CRMValidatorService
        external_check = {"valid": False, "confidence": 0.0}
        try:
            from services.crm_validator_service import CRMValidatorService
            ext_result = CRMValidatorService.validate_crm(solicitacao.crm, solicitacao.uf_crm)
            external_check = {
                "valid": ext_result.get("status") in ("validated", "possible_match"),
                "confidence": 0.8 if ext_result.get("status") == "validated" else 0.4,
                "details": ext_result,
                "recommendation": "approve" if ext_result.get("status") in ("validated", "possible_match") else "review",
            }
            results["external"] = external_check
        except Exception as e:
            logger.warning(f"Validacao externa CRM indisponivel: {e}")
            results["external"] = {"valid": False, "confidence": 0.0, "error": str(e)}
        
        # Determinar se é válido
        is_valid = format_check['valid'] and not duplicate_check['duplicate']
        confidence = min(
            format_check['confidence'],
            duplicate_check['confidence'],
            external_check.get("confidence", 0.5),
        )
        
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
            # Fallback determinístico: aprova se verificações técnicas passarem
            crm_ok = crm_result.get("valid", False)
            email_ok = email_result.get("valid", False)
            fraud_ok = fraud_result.get("risk_level", "high") in ("low", "medium")
            if crm_ok and email_ok and fraud_ok:
                ai_decision = {
                    "recommendation": "auto_approve",
                    "justification": "Aprovado por fallback determinístico (IA indisponível). Verificações técnicas OK.",
                    "confidence_score": 0.7,
                    "highlighted_issues": []
                }
            else:
                ai_decision = {
                    "recommendation": "manual_review",
                    "justification": f"Erro no processamento da IA + falha em verificações técnicas: {str(e)}",
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
