"""
Configurações de segurança para o sistema Aracannabis.
Este módulo contém configurações e funções relacionadas à segurança da aplicação.
"""

import re
from functools import wraps
from flask import request, jsonify, current_app
import secrets
import string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

# Configurações de rate limiting
DEFAULT_RATE_LIMIT = "1000 per day, 60 per minute"
LOGIN_RATE_LIMIT = "10 per minute"
SENSITIVE_ENDPOINTS_RATE_LIMIT = "100 per minute"
API_SEARCH_RATE_LIMIT = "200 per minute"

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
    'https://aracannabis.com.br',
    'https://www.aracannabis.com.br',
    'https://app.aracannabis.com.br',
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
    'Content-Security-Policy': (
        f"default-src 'self'; "
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: blob: https:; "
        f"font-src 'self' data: https:; "
        f"connect-src 'self' {connect_src_origins}; "
        f"frame-src 'self'; "
        f"media-src 'self' blob: data:;"
    ),
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0',
}

# Inicializar rate limiter
limiter = None

def init_limiter(app):
    """Inicializa o rate limiter para a aplicação Flask"""
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[DEFAULT_RATE_LIMIT],
        storage_uri="memory://",
        strategy="fixed-window"
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
    
    Args:
        response: Objeto de resposta Flask
        
    Returns:
        response: Objeto de resposta com cabeçalhos adicionados
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

def csrf_protect(f):
    """
    Decorator para proteção CSRF.
    Verifica se o token CSRF no cabeçalho corresponde ao token na sessão.
    
    Args:
        f: Função a ser decorada
        
    Returns:
        function: Função decorada com proteção CSRF
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ignorar verificação para métodos GET, HEAD, OPTIONS
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return f(*args, **kwargs)
        
        # Verificar token CSRF para outros métodos
        token = request.headers.get('X-CSRF-Token')
        if not token or token != current_app.config.get('CSRF_TOKEN'):
            return jsonify({'error': 'CSRF token inválido ou ausente'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

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

def sanitize_input(data):
    """
    Sanitiza dados de entrada para prevenir injeção.
    
    Args:
        data: Dados a serem sanitizados
        
    Returns:
        Dados sanitizados
    """
    if isinstance(data, str):
        # Remover caracteres potencialmente perigosos
        return re.sub(r'[<>\'";]', '', data)
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    else:
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
