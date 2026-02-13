from datetime import datetime, timedelta
import logging

# Simple In-Memory Rate Limiter
# Em produção, usar Redis.

logger = logging.getLogger(__name__)

# tenant_id -> list of timestamps
REQUEST_HISTORY = {} 
LIMIT_PER_MINUTE = 30 # Default

def check_rate_limit(tenant_id: int):
    now = datetime.utcnow()
    # Limpar histórico antigo
    window_start = now - timedelta(minutes=1)
    
    if tenant_id not in REQUEST_HISTORY:
        REQUEST_HISTORY[tenant_id] = []
    
    # Manter apenas requisições recentes (dentro da janela de 1 min)
    REQUEST_HISTORY[tenant_id] = [t for t in REQUEST_HISTORY[tenant_id] if t > window_start]
    
    current_count = len(REQUEST_HISTORY[tenant_id])
    
    if current_count >= LIMIT_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for tenant {tenant_id}: {current_count}/{LIMIT_PER_MINUTE}")
        return False
    
    # Registrar nova requisição
    REQUEST_HISTORY[tenant_id].append(now)
    return True

# Cleanup job (opcional) poderia rodar periodicamente para limpar tenants inativos
