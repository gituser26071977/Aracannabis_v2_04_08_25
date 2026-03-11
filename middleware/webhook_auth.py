"""
Middleware de Autenticação para Webhooks
Protege endpoints de webhook contra acesso não autorizado
"""
from flask import request, jsonify
from functools import wraps
import os
import logging

logger = logging.getLogger(__name__)

def webhook_auth_required(f):
    """
    Decorator para proteger webhooks com autenticação via secret key
    
    Valida:
    1. X-Webhook-Secret header
    2. IP whitelist (opcional)
    
    Uso:
        @webhook_auth_required
        def my_webhook():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Validar X-Webhook-Secret header
        webhook_secret = os.environ.get('WEBHOOK_SECRET_KEY')
        
        if not webhook_secret:
            logger.warning("WEBHOOK_SECRET_KEY não configurado! Webhook desprotegido!")
            # Em ambiente de desenvolvimento, permitir sem secret (com warning)
            if os.environ.get('FLASK_ENV') == 'development':
                logger.warning("Ambiente de desenvolvimento - permitindo webhook sem autenticação")
            else:
                return jsonify({
                    'error': 'Webhook não configurado corretamente',
                    'message': 'WEBHOOK_SECRET_KEY não definido no servidor'
                }), 500
        
        # Obter secret do header
        provided_secret = request.headers.get('X-Webhook-Secret')
        
        if not provided_secret:
            logger.warning(f"Tentativa de acesso ao webhook sem X-Webhook-Secret do IP: {request.remote_addr}")
            return jsonify({
                'error': 'Autenticação necessária',
                'message': 'Header X-Webhook-Secret não fornecido'
            }), 401
        
        # Validar secret
        if provided_secret != webhook_secret:
            logger.error(f"Tentativa de acesso ao webhook com secret inválido do IP: {request.remote_addr}")
            return jsonify({
                'error': 'Autenticação falhou',
                'message': 'X-Webhook-Secret inválido'
            }), 403
        
        # 2. Validar IP whitelist (opcional)
        ip_whitelist_str = os.environ.get('WEBHOOK_IP_WHITELIST', '')
        if ip_whitelist_str:
            allowed_ips = [ip.strip() for ip in ip_whitelist_str.split(',')]
            client_ip = request.remote_addr
            
            # Suportar X-Forwarded-For para proxies reversos (Nginx, etc)
            if request.headers.get('X-Forwarded-For'):
                client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            
            if client_ip not in allowed_ips:
                logger.error(f"Tentativa de acesso ao webhook de IP não permitido: {client_ip}")
                return jsonify({
                    'error': 'Acesso negado',
                    'message': 'IP não autorizado'
                }), 403
            
            logger.info(f"Webhook acessado por IP autorizado: {client_ip}")
        
        # Autenticação bem-sucedida
        logger.info(f"Webhook autenticado com sucesso do IP: {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function


def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    """
    Verifica assinatura HMAC de webhook (para APIs que usam esse padrão)
    
    Args:
        payload: Payload JSON do webhook
        signature: Assinatura fornecida no header (ex: X-Hub-Signature-256)
        secret: Secret compartilhado
    
    Returns:
        True se assinatura é válida, False caso contrário
    """
    import hmac
    import hashlib
    import json
    
    # Calcular HMAC do payload
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    # Comparação segura contra timing attacks
    return hmac.compare_digest(f"sha256={expected_signature}", signature)


# Rate limiting para webhooks (prevenir spam)
from collections import defaultdict
from datetime import datetime, timedelta

webhook_rate_limit = defaultdict(list)
WEBHOOK_MAX_REQUESTS = int(os.environ.get('WEBHOOK_MAX_REQUESTS_PER_MINUTE', '10'))

def webhook_rate_limiter(identifier: str) -> tuple[bool, str]:
    """
    Rate limiting simples para webhooks
    
    Args:
        identifier: Identificador único (telefone, email, etc)
    
    Returns:
        (is_allowed, message)
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=1)
    
    # Limpar requisições antigas
    webhook_rate_limit[identifier] = [
        ts for ts in webhook_rate_limit[identifier] if ts > cutoff
    ]
    
    # Verificar limite
    if len(webhook_rate_limit[identifier]) >= WEBHOOK_MAX_REQUESTS:
        return False, f"Rate limit excedido: máximo {WEBHOOK_MAX_REQUESTS} requisições por minuto"
    
    # Adicionar nova requisição
    webhook_rate_limit[identifier].append(now)
    return True, "OK"
