#!/usr/bin/env python3
"""
Script de Validação de Variáveis de Ambiente
Valida que todas as variáveis obrigatórias estão configuradas antes do deploy
"""
import os
import sys
from typing import Tuple

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

# Variáveis OBRIGATÓRIAS por categoria
REQUIRED_VARS = {
    "Ambiente": [
        ("FLASK_ENV", "production ou development"),
        ("FLASK_APP", "app_cors_livre.py"),
    ],
    "Segurança (CRÍTICO)": [
        ("JWT_SECRET_KEY", "secret de 32+ caracteres - NÃO usar 'super_secret_key'"),
        ("SECRET_KEY", "secret de 32+ caracteres - NÃO usar padrões"),
    ],
    "Database": [
        ("DATABASE_URL", "postgresql://user:pass@host:port/db ou sqlite:///path.db"),
    ],
}

# Variáveis OBRIGATÓRIAS para produção
REQUIRED_PRODUCTION_VARS = {
    "Webhook WhatsApp": [
        ("WEBHOOK_SECRET_KEY", "secret de 32+ caracteres"),
    ],
    "Email (SMTP)": [
        ("SMTP_SERVER", "servidor SMTP"),
        ("SMTP_PORT", "porta SMTP (465 ou 587)"),
        ("SMTP_USERNAME", "usuário SMTP"),
        ("SMTP_PASSWORD", "senha SMTP"),
        ("EMAIL_FROM", "email remetente"),
    ],
}

# Variáveis OPCIONAIS mas recomendadas
OPTIONAL_VARS = {
    "Telegram (D05k)": [
        ("TELEGRAM_DEFAULT_BOT_TOKEN", "bot fixo Dr.Anderson para admin notif"),
        ("TELEGRAM_ADMIN_CHAT_ID", "chat_id do admin que recebe notificações"),
    ],
    "LLMs": [
        ("OPENAI_API_KEY", "chave OpenAI (GPT-4, GPT-3.5)"),
        ("GROQ_API_KEY", "chave Groq (Llama, Mixtral)"),
        ("ANTHROPIC_API_KEY", "chave Anthropic (Claude)"),
        ("GOOGLE_API_KEY", "chave Google (Gemini)"),
        ("DEEPSEEK_API_KEY", "chave DeepSeek"),
    ],
}

# Valores INSEGUROS que NÃO devem estar em produção
INSECURE_VALUES = [
    "super_secret_key",
    "change_me",
    "your_key_here",
    "your_token_here",
    "your_password_here",
    "12345",
    "67890",
    "test",
    "exemplo",
]

def validate_var(var_name: str, expected: str) -> Tuple[bool, str]:
    """Valida uma variável de ambiente"""
    value = os.environ.get(var_name)
    
    if not value:
        return False, f"Variável {var_name} não configurada"
    
    # Verificar se contém valores inseguros
    value_lower = value.lower()
    for insecure in INSECURE_VALUES:
        if insecure in value_lower:
            return False, f"Variável {var_name} contém valor inseguro: '{insecure}'"
    
    # Validações específicas
    if "SECRET_KEY" in var_name or "JWT_SECRET" in var_name or "WEBHOOK_SECRET" in var_name:
        if len(value) < 32:
            return False, f"Variável {var_name} muito curta (mínimo 32 caracteres)"
    
    if var_name == "FLASK_ENV":
        if value not in ["production", "development"]:
            return False, f"FLASK_ENV deve ser 'production' ou 'development', não '{value}'"
    
    if var_name == "DEBUG":
        if value.lower() in ["true", "1"] and os.environ.get("FLASK_ENV") == "production":
            return False, "DEBUG=True em FLASK_ENV=production é INSEGURO!"
    
    return True, "OK"

def main():
    print_header("🔒 SIAP - Validação de Variáveis de Ambiente")
    
    errors = []
    warnings = []
    
    # 1. Validar variáveis obrigatórias
    print_header("1. Variáveis OBRIGATÓRIAS")
    for category, vars in REQUIRED_VARS.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.END}")
        for var_name, expected in vars:
            is_valid, message = validate_var(var_name, expected)
            if is_valid:
                print_success(f"{var_name}: {message}")
            else:
                print_error(f"{var_name}: {message}")
                errors.append(f"{var_name}: {message}")
    
    # 2. Validar variáveis de produção
    is_production = os.environ.get("FLASK_ENV") == "production"
    
    if is_production:
        print_header("2. Variáveis OBRIGATÓRIAS (PRODUÇÃO)")
        for category, vars in REQUIRED_PRODUCTION_VARS.items():
            print(f"\n{Colors.BOLD}{category}:{Colors.END}")
            for var_name, expected in vars:
                is_valid, message = validate_var(var_name, expected)
                if is_valid:
                    print_success(f"{var_name}: {message}")
                else:
                    print_error(f"{var_name}: {message}")
                    errors.append(f"{var_name}: {message}")
    else:
        print_header("2. Variáveis OBRIGATÓRIAS (PRODUÇÃO)")
        print_warning("Ambiente de desenvolvimento - validação de produção ignorada")
    
    # 3. Validar variáveis opcionais
    print_header("3. Variáveis OPCIONAIS")
    for category, vars in OPTIONAL_VARS.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.END}")
        has_any = False
        for var_name, expected in vars:
            value = os.environ.get(var_name)
            if value:
                is_valid, message = validate_var(var_name, expected)
                if is_valid:
                    print_success(f"{var_name}: Configurado")
                    has_any = True
                else:
                    print_warning(f"{var_name}: {message}")
                    warnings.append(f"{var_name}: {message}")
        
        if not has_any:
            print_warning(f"Nenhuma variável de {category} configurada (opcional)")
    
    # 4. Validações de segurança extras
    print_header("4. Validações de Segurança")
    
    # DEBUG em produção
    if is_production and os.environ.get("DEBUG", "").lower() in ["true", "1"]:
        print_error("DEBUG=True em produção é INSEGURO!")
        errors.append("DEBUG está ativo em produção")
    else:
        print_success("DEBUG configurado corretamente")
    
    # JWT_SECRET_KEY único
    jwt_secret = os.environ.get("JWT_SECRET_KEY", "")
    secret_key = os.environ.get("SECRET_KEY", "")
    if jwt_secret and secret_key and jwt_secret == secret_key:
        print_warning("JWT_SECRET_KEY e SECRET_KEY são iguais (recomendado usar diferentes)")
        warnings.append("JWT_SECRET_KEY == SECRET_KEY")
    else:
        print_success("JWT_SECRET_KEY e SECRET_KEY são diferentes")
    
    # 5. Resumo final
    print_header("📊 RESUMO")
    
    if errors:
        print_error(f"Encontrados {len(errors)} ERROS CRÍTICOS:")
        for error in errors:
            print(f"  - {error}")
        print()
    
    if warnings:
        print_warning(f"Encontrados {len(warnings)} AVISOS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    if not errors and not warnings:
        print_success("Todas as variáveis estão configuradas corretamente!")
        print()
    
    # 6. Código de saída
    if errors:
        print_error("❌ Validação FALHOU - Corrija os erros antes de fazer deploy")
        return 1
    elif warnings and is_production:
        print_warning("⚠️  Validação com avisos - Revise as configurações")
        return 0
    else:
        print_success("✅ Validação PASSOU - Ambiente configurado corretamente")
        return 0

if __name__ == "__main__":
    try:
        # Carregar .env se existir
        from dotenv import load_dotenv
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"✅ Carregado .env de: {env_file}\n")
        else:
            print(f"⚠️  Arquivo .env não encontrado em: {env_file}")
            print("⚠️  Lendo variáveis do ambiente do sistema\n")
    except ImportError:
        print("⚠️  python-dotenv não instalado - lendo apenas do ambiente\n")
    
    sys.exit(main())
