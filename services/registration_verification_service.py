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
        """Verifica o registro profissional conforme o TIPO de conselho.

        Antes validava sempre como CRM (médico). Agora roteia pelo
        `conselho_tipo` da solicitação:
          - CRM      → validação externa no CFM (CRMValidatorService)
          - CREFITO  → validação CREFITO (fisioterapia / terapia ocupacional)
          - demais   → validação de formato + revisão manual (validação
                       externa ainda não implementada para o conselho)
        """
        from services.conselho_validator import (
            normalizar_tipo_conselho,
            validar_conselho,
            CONSELHO_CRM,
            CONSELHO_CREFITO,
        )

        tipo = normalizar_tipo_conselho(
            getattr(solicitacao, "conselho_tipo", None) or CONSELHO_CRM
        )

        results = {"conselho_tipo": tipo}

        # Validar formato conforme o tipo de conselho
        fmt = validar_conselho(solicitacao.crm, solicitacao.uf_crm, tipo)
        format_check = {
            "valid": fmt["valido"],
            "confidence": 0.9 if fmt["valido"] else 0.4,
            "reason": "; ".join(fmt["erros"]) if fmt["erros"] else "Formato válido",
        }
        results["format"] = format_check

        # Verificar duplicidade (número + UF)
        duplicate_check = check_duplicate_crm(solicitacao.crm, solicitacao.uf_crm, exclude_id=solicitacao.id)
        results["duplicate"] = duplicate_check

        # Validar externamente conforme o conselho
        external_check = {"valid": False, "confidence": 0.0}
        try:
            if tipo == CONSELHO_CREFITO:
                from services.crefito_validator_service import CREFITOValidatorService
                ext_result = CREFITOValidatorService.validate_crefito(solicitacao.crm, solicitacao.uf_crm)
            elif tipo == CONSELHO_CRM:
                from services.crm_validator_service import CRMValidatorService
                ext_result = CRMValidatorService.validate_crm(solicitacao.crm, solicitacao.uf_crm)
            else:
                ext_result = {
                    "status": "not_supported",
                    "error": f"Validação externa para o conselho {tipo} ainda não implementada — revisão manual.",
                }

            status = ext_result.get("status")
            external_check = {
                "valid": status in ("validated", "possible_match"),
                "confidence": 0.8 if status == "validated" else (0.4 if status == "possible_match" else 0.0),
                "details": ext_result,
                "recommendation": "approve" if status in ("validated", "possible_match") else "review",
            }
            results["external"] = external_check
        except Exception as e:
            logger.warning(f"Validacao externa ({tipo}) indisponivel: {e}")
            results["external"] = {"valid": False, "confidence": 0.0, "error": str(e)}

        # Determinar se é válido
        is_valid = format_check["valid"] and not duplicate_check["duplicate"]
        confidence = min(
            format_check["confidence"],
            duplicate_check["confidence"],
            external_check.get("confidence", 0.5),
        )

        return {
            "valid": is_valid,
            "confidence": confidence,
            "details": results,
            "recommendation": "approve" if is_valid else "reject",
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
                "especialidade": solicitacao.especialidade,
                "conselho_tipo": crm_result.get("details", {}).get("conselho_tipo"),
            },
            "validacoes": {
                "crm": crm_result,
                "email": email_result,
                "fraude": fraud_result
            }
        }

        system_prompt = """Você é um Auditor de Conformidade de Cadastros Profissionais da Arapath.
        Analise os dados de validação técnica e decida se o profissional deve ser aprovado,
        revisado manualmente ou rejeitado.

        IMPORTANTE — o profissional pode ter DIFERENTES conselhos de classe:
          - CRM     → Médico
          - CREFITO → Fisioterapeuta / Terapeuta Ocupacional
          - CRP     → Psicólogo
          - COREN   → Enfermeiro
          - CRN     → Nutricionista
          - CRFa    → Fonoaudiólogo
        Valide o número contra o conselho declarado (campo "conselho_tipo").
        NUNCA aponte incompatibilidade apenas porque o profissional NÃO tem CRM —
        fisioterapeutas usam CREFITO, psicólogos usam CRP, etc.

        CRITÉRIOS DE AUTO-APROVAÇÃO:
        1. Número de registro válido (formato correto para o tipo de conselho) e sem duplicidade.
        2. Email válido, corporativo/comum (não descartável) e sem duplicidade.
        3. Risco de fraude baixo.
        4. Alta confiança nas ferramentas técnicas (>85%).
        Se a validação externa do conselho não estiver disponível (ex.: o portal do
        CREFITO exige verificação humana/CAPTCHA), recomende "manual_review" — NUNCA
        "reject" — e explique que falta verificação externa, sem inventar reprovação.

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
            "conselho_tipo": crm_result.get("details", {}).get("conselho_tipo"),
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
