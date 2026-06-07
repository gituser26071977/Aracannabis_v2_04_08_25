from app.models import AIClinicalRequest
import logging

logger = logging.getLogger(__name__)

# Estimativa de custo (DeepSeek)
# Input: $0.14 / 1M tokens
# Output: $0.28 / 1M tokens

COST_INPUT_PER_1M = 0.14
COST_OUTPUT_PER_1M = 0.28

def estimate_cost(tokens_input: int, tokens_output: int) -> float:
    cost_input = (tokens_input / 1_000_000) * COST_INPUT_PER_1M
    cost_output = (tokens_output / 1_000_000) * COST_OUTPUT_PER_1M
    return round(cost_input + cost_output, 6)

def record_audit_log(session, request_data, metrics, status, error=None):
    """Grava na tabela de auditoria ai_clinical_requests"""
    # Converter para modelos SQL
    # Atenção: models_ai_compliance não tem tenant_id mapeado!
    # Mas aqui usamos o AIClinicalRequest local.
    
    # Se erro, tokens podem ser zero
    
    cost = estimate_cost(metrics.get("tokens_input", 0), metrics.get("tokens_output", 0))
    
    audit_entry = AIClinicalRequest(
        consultation_id=request_data.get("consultation_id"),
        provider=request_data.get("provider", "unknown"),
        model="deepseek-v3", # Exemplo
        tokens_input=metrics.get("tokens_input", 0),
        tokens_output=metrics.get("tokens_output", 0),
        processing_time_ms=metrics.get("duration", 0),
        cost_estimate=cost,
        status=status,
        error_message=str(error) if error else None,
        # tenant_id não está no modelo compliance original, logar em JSON ou adaptar
        # UserAgent hack para tenant?
        # Manter simples: não persistir tenant_id se a coluna não existir, mas logar no stdout seguro.
    )
    
    # Logar tenant_id no stdout seguro (já que pode nao ter coluna)
    logger.info(f"AUDIT: Tenant {request_data.get('tenant_id')} - cost=${cost:.6f} - status={status}")

    session.add(audit_entry)
    try:
        session.commit()
    except Exception as e:
        logger.error(f"Failed to commit audit log: {e}")
        session.rollback()
