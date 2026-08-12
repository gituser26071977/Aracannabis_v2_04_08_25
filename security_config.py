"""
Configurações de segurança para o sistema AraOS.
Este módulo contém configurações e funções relacionadas à segurança da aplicação.
"""

import os
import re
import logging
from functools import wraps
from flask import request, jsonify, current_app
import secrets
import string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


logger = logging.getLogger(__name__)


# FASE 5A — key function híbrida: usa JWT identity (profissional_id) quando
# autenticado; caso contrário, usa IP. Isso evita o problema do load test
# (mesmo IP = mesmo bucket) e garante isolamento entre profissionais em produção.
def get_hybrid_key():
    """
    Retorna a chave do rate limit:
      - profissional_id (string do JWT) se autenticado
      - IP do cliente caso contrário

    O Flask-Limiter exige string. Profissional.id é int; convertemos para str
    e prefixamos com "prof:" para evitar colisão com IPs.
    """
    try:
        # flask_jwt_extended pode estar indisponível (testes mínimos); usar import lazy
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        # verify_jwt_in_request() retorna False se não há token; não levanta
        if verify_jwt_in_request(optional=True):
            ident = get_jwt_identity()
            if ident is not None:
                return f"prof:{ident}"
    except Exception:
        # Sem JWT / sem request context / sem Flask-JWT-Extended
        pass
    # Fallback: IP
    return f"ip:{get_remote_address()}"


def require_secret(name, min_length=32, allow_default=False, default=None):
    """
    Lê uma variável de ambiente obrigatória como segredo.

    Em produção (FLASK_ENV=production) aborta o startup se a variável
    estiver ausente, vazia ou for um placeholder conhecido.
    Em desenvolvimento aceita placeholder/default se allow_default=True.

    Args:
        name: nome da variável de ambiente
        min_length: tamanho mínimo exigido
        allow_default: se True, permite valor vazio/placeholder em dev
        default: valor default se variável ausente (apenas com allow_default)

    Returns:
        str: valor do segredo

    Raises:
        RuntimeError: se inválido em produção
    """
    placeholders = {"", "changeme", "change_me", "change-me",
                    "your-secret-key-here", "secret", "default"}
    value = os.getenv(name, "")

    if allow_default and not value:
        return default or "REDACTED"

    is_placeholder = (
        not value
        or value.lower() in placeholders
        or value.startswith("CHANGE_ME")
        or len(value) < min_length
    )

    if is_placeholder:
        from config import is_production  # import local evita circular config↔security_config

        is_prod = is_production()
        if is_prod or not allow_default:
            raise RuntimeError(
                f"[SECURITY] {name} ausente/fraco. Defina um valor "
                f"com pelo menos {min_length} caracteres. "
                f"Em produção o startup é abortado."
            )
        return default or "REDACTED"

    return value

# Configurações de senha
PASSWORD_MIN_LENGTH = 10
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"

# Configurações de token
TOKEN_EXPIRATION_MINUTES = 60  # 1 hora
REFRESH_TOKEN_EXPIRATION_DAYS = 7  # 7 dias

# Configurações de rate limiting — FASE 5A
# Limites por janela de tempo. moving-window strategy = sem "rajadas" no início da janela.
DEFAULT_RATE_LIMIT = "5000 per hour, 200 per minute"
LOGIN_RATE_LIMIT = "10 per minute"             # brute-force protection (POST /auth/login)
SENSITIVE_ENDPOINTS_RATE_LIMIT = "100 per minute"  # POSTs críticos (cadastros, troca de senha, etc)
API_SEARCH_RATE_LIMIT = "200 per minute"       # reservado para FASE 5B (não aplicado agora)

# Lista de origens permitidas para CORS
ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:3002',
    'http://localhost:3003',
    'http://localhost:3004',
    'http://localhost:3005',
    'http://localhost:3006',
    'http://localhost:3007',
    'http://localhost:3008',
    'http://localhost:3009',
    'http://localhost:3010',
    'http://localhost:5000',
    'http://localhost:5002',
    'http://localhost:5003',
    'http://localhost:5010',
    'http://backend:5002',
    'https://visualsmartflow.com.br',
    'https://www.visualsmartflow.com.br',
    'https://araos.visualsmartflow.com.br',
    # Tenant Vittalis (prontuário + API)
    'https://siap.vittalis.site',
    'https://api.vittalis.site',
    'https://vittalis.site',
    'http://192.168.0.104:3000',
    'http://192.168.0.104:3000',
    'http://192.168.0.104:5002',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5002'
]

# Cabeçalhos de segurança HTTP
connect_src_origins = " ".join(ALLOWED_ORIGINS)
# CSP otimizado para SPA React — permite recursos da mesma origem e conexões CORS configuradas
SECURITY_HEADERS = {
    # CSP e headers com nonce são setados em add_security_headers(response)
    # para incluir nonce por-request.
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "Permissions-Policy": "geolocation=(), microphone=(self), camera=(self), payment=()",
}

# Inicializar rate limiter
limiter = None


def _resolve_storage_uri():
    """
    FASE 5A — Decide onde o Flask-Limiter persiste os contadores.

    Ordem de preferência:
      1. RATELIMIT_STORAGE_URL (env var padrão Flask-Limiter)
      2. REDIS_URL + RATE_LIMIT_REDIS_DB (db dedicado, default /1 = não conflita com cache /0)
      3. memory:// (fallback local)

    Returns:
        str: storage URI válido para Flask-Limiter.
    """
    explicit = os.getenv("RATELIMIT_STORAGE_URL", "").strip()
    if explicit:
        return explicit

    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        # Permite configurar db dedicado (não conflita com cache /0 usado por outros serviços).
        db = os.getenv("RATE_LIMIT_REDIS_DB", "1").strip() or "1"
        # Se REDIS_URL já terminar com /N, substitui. Senão, anexa.
        if redis_url.rsplit("/", 1)[-1].isdigit():
            base = redis_url.rsplit("/", 1)[0]
        else:
            base = redis_url
        final_url = f"{base}/{db}"
        logger.info("[rate-limit] usando Redis storage em %s", final_url)
        return final_url

    logger.warning(
        "[rate-limit] REDIS_URL não definido — usando memory://. "
        "Em produção multi-worker isso causa rate limit inconsistente entre workers."
    )
    return "memory://"


def init_limiter(app):
    """
    Inicializa o rate limiter para a aplicação Flask.

    FASE 5A — Mudanças:
      - Storage: Redis (compartilhado entre workers) com fallback memory://
      - Key function: híbrida (profissional_id se autenticado, IP se anônimo)
      - Strategy: moving-window (sem picos de início de janela)
      - default_limits: 200/min + 5000/hora (vs antigo 60/min + 1000/dia)
    """
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_hybrid_key,
        default_limits=[DEFAULT_RATE_LIMIT],
        storage_uri=_resolve_storage_uri(),
        strategy="moving-window",
        headers_enabled=True,   # adiciona X-RateLimit-* nas respostas
    )
    return limiter

def validate_password_strength(password):
    """
    Valida a força da senha de acordo com as políticas definidas.
    
    Args:
        password (str): A senha a ser validada
        
    Returns:
        tuple: (bool, str) - (válido, mensagem de erro)
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"A senha deve ter pelo menos {PASSWORD_MIN_LENGTH} caracteres"
    
    if PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        return False, "A senha deve conter pelo menos uma letra maiúscula"
    
    if PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        return False, "A senha deve conter pelo menos uma letra minúscula"
    
    if PASSWORD_REQUIRE_NUMBERS and not re.search(r'[0-9]', password):
        return False, "A senha deve conter pelo menos um número"
    
    if PASSWORD_REQUIRE_SPECIAL and not any(c in PASSWORD_SPECIAL_CHARS for c in password):
        return False, f"A senha deve conter pelo menos um caractere especial ({PASSWORD_SPECIAL_CHARS})"
    
    return True, "Senha válida"

def generate_secure_token(length=32):
    """
    Gera um token seguro aleatório.
    
    Args:
        length (int): Comprimento do token
        
    Returns:
        str: Token seguro
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def add_security_headers(response):
    """
    Adiciona cabeçalhos de segurança HTTP à resposta.

    P0-05 (Missão 18): CSP sem 'unsafe-inline' / 'unsafe-eval' em script-src.
    Gera nonce por-request e o embute no header Content-Security-Policy.
    """
    # Gera nonce determinístico por request (cacheado em flask.g)
    nonce = getattr(g, "csp_nonce", None) if "g" in dir() else None
    if nonce is None:
        import secrets as _secrets
        nonce = _secrets.token_urlsafe(16)

    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: blob: https:; "
        f"font-src 'self' data: https:; "
        f"connect-src 'self' {connect_src_origins}; "
        f"frame-src 'self'; "
        f"media-src 'self' blob: data:; "
        f"object-src 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'; "
        f"frame-ancestors 'none'; "
        f"upgrade-insecure-requests"
    )

    response.headers["Content-Security-Policy"] = csp
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

def csrf_protect(f):
    """
    Decorator para proteção CSRF (P0-06 — Missão 18).

    Garantias:
      1. Token é obrigatório no header X-CSRF-Token (ou form field csrf_token).
      2. Token nunca pode ser comparado contra None:
         - se app.config["CSRF_TOKEN"] não estiver setado, ABORTA no startup
           (ver app_cors_livre.py: create_app chama _ensure_csrf_token()).
      3. Comparação via hmac.compare_digest (constant-time, anti timing-attack).
    """
    import hmac

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return f(*args, **kwargs)

        expected = current_app.config.get("CSRF_TOKEN")
        if not expected:
            # Fail closed: se a config está quebrada, recusa TUDO.
            current_app.logger.error(
                "csrf_protect: CSRF_TOKEN não configurado — abortando request"
            )
            return jsonify({"error": "CSRF misconfiguration"}), 503

        token = request.headers.get("X-CSRF-Token") or (
            request.form.get("csrf_token") if request.form else None
        )
        if not token:
            return jsonify({"error": "CSRF token ausente"}), 403

        if not hmac.compare_digest(str(token), str(expected)):
            return jsonify({"error": "CSRF token inválido"}), 403

        return f(*args, **kwargs)
    return decorated_function


def _ensure_csrf_token(app):
    """
    Garante que app.config["CSRF_TOKEN"] está setado em produção.
    Em produção ABORTA se não houver valor seguro.
    """
    import os
    token = app.config.get("CSRF_TOKEN")
    if token and len(str(token)) >= 32:
        return token

    is_prod = os.environ.get("ENVIRONMENT", "development").lower() in ("production", "prod")
    if is_prod:
        raise RuntimeError(
            "[SECURITY] CSRF_TOKEN ausente ou fraco. Defina um valor de "
            "pelo menos 32 caracteres antes de iniciar em produção."
        )
    # dev: gera placeholder aleatório
    import secrets as _secrets
    new_token = _secrets.token_hex(32)
    app.config["CSRF_TOKEN"] = new_token
    return new_token

def check_content_type(content_type):
    """
    Decorator para verificar o Content-Type da requisição.
    
    Args:
        content_type (str): Content-Type esperado
        
    Returns:
        function: Decorator
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method not in ['GET', 'HEAD', 'OPTIONS']:
                if not request.headers.get('Content-Type', '').startswith(content_type):
                    return jsonify({'error': f'Content-Type deve ser {content_type}'}), 415
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# P0-04 (Missão 18): campos de senha NUNCA devem ser sanitizados.
# Sanitização que remove < > ' " ; quebra senhas com esses caracteres.
_PASSWORD_KEYS = frozenset({
    "senha",
    "password",
    "confirm_password",
    "new_password",
    "old_password",
    "senha_atual",
    "nova_senha",
    "current_password",
})


def sanitize_input(data):
    """
    Sanitiza dados de entrada para prevenir injeção em campos NÃO-credenciais.

    IMPORTANTE (P0-04): campos de senha NUNCA são sanitizados. Senhas com
    caracteres como < > ' " ; são válidas (o sanitize_input é projetado
    para remover XSS/SQLi de campos HTML, não de credenciais).

    Args:
        data: str, dict, list ou escalar a ser sanitizado

    Returns:
        Dados sanitizados (senhas pass-through intactas)
    """
    if isinstance(data, str):
        return re.sub(r'[<>\'";]', '', data)
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in _PASSWORD_KEYS:
                # Senha é preservada integralmente (pass-through)
                out[k] = v
            else:
                out[k] = sanitize_input(v)
        return out
    if isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

def is_valid_email(email):
    """
    Verifica se um email é válido.
    
    Args:
        email (str): Email a ser validado
        
    Returns:
        bool: True se o email for válido, False caso contrário
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_cpf(cpf):
    """
    Verifica se um CPF é válido.
    
    Args:
        cpf (str): CPF a ser validado
        
    Returns:
        bool: True se o CPF for válido, False caso contrário
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verificar se todos os dígitos são iguais
    if cpf == cpf[0] * 11:
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    return int(cpf[10]) == digito2

def mask_sensitive_data(data, field, mask_char='*', visible_start=2, visible_end=2):
    """
    Mascara dados sensíveis para exibição.
    
    Args:
        data (str): Dados a serem mascarados
        field (str): Tipo de campo (cpf, email, etc)
        mask_char (str): Caractere usado para mascarar
        visible_start (int): Número de caracteres visíveis no início
        visible_end (int): Número de caracteres visíveis no fim
        
    Returns:
        str: Dados mascarados
    """
    if not data:
        return data
    
    data = str(data)
    
    if field == 'email':
        parts = data.split('@')
        if len(parts) != 2:
            return data
        
        username = parts[0]
        domain = parts[1]
        
        if len(username) <= visible_start + visible_end:
            masked_username = username
        else:
            masked_username = username[:visible_start] + mask_char * (len(username) - visible_start - visible_end) + username[-visible_end:]
        
        return f"{masked_username}@{domain}"
    
    elif field in ['cpf', 'telefone']:
        if len(data) <= visible_start + visible_end:
            return data
        
        return data[:visible_start] + mask_char * (len(data) - visible_start - visible_end) + data[-visible_end:]
    
    else:
        # Mascaramento genérico
        if len(data) <= visible_start + visible_end:
            return data
        
        return data[:visible_start] + mask_char * (len(data) - visible_start - visible_end) + data[-visible_end:]
