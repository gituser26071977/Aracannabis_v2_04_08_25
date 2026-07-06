"""
Configuração central do AraOS.

P0-03 (Fase 1 — Segurança): segredos obrigatórios são validados no startup
via ``security_config.validate_required_secrets()``. Defaults inseguros foram
removidos. A aplicação ABORTA se ``JWT_SECRET_KEY`` ou ``SECRET_KEY`` estiverem
ausentes/fracas em produção.
"""

import os
import logging

from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env (somente desenvolvimento)
load_dotenv()

logger = logging.getLogger(__name__)


def _is_production() -> bool:
    """P0-10 (Missão 18): fonte ÚNICA de verdade para detecção de produção.

    Aceita apenas ENVIRONMENT=production|prod (case-insensitive).
    FLASK_ENV=production também é aceito como alias para retrocompatibilidade,
    mas a variável canônica é ENVIRONMENT.
    """
    env = os.environ.get("ENVIRONMENT", "").strip().lower()
    if env in ("production", "prod"):
        return True
    # Backward-compat alias
    flask_env = os.environ.get("FLASK_ENV", "").strip().lower()
    return flask_env == "production"


def is_production() -> bool:
    """API pública usada por toda a aplicação. Use sempre esta função."""
    return _is_production()


# Carregar validador de segredos. Importação tardia para evitar ciclo.
try:
    from security_config import validate_required_secrets  # noqa: E402

    try:
        _validated = validate_required_secrets()
        logger.info("Config: %d segredos validados com sucesso.", len(_validated))
    except RuntimeError as exc:
        # Em produção, o app NÃO pode iniciar sem segredos.
        if _is_production():
            raise
        logger.warning("Config: %s (modo desenvolvimento)", exc)
except ImportError:
    # security_config ausente (improvável) — prossegue sem validação
    logger.warning("Config: security_config não importado; validação de segredos desativada.")


class Config:
    # --- Banco de dados (Postgres porta 5434) ---
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5434/aracannabis",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Engine options (P0-13 Production Readiness) ---
    # pool_size=20, max_overflow=40 → até 60 conexões concorrentes
    # pool_pre_ping=True → testa conexão antes de usar
    #   (evita "server closed connection" após idle timeout)
    # pool_recycle=1800 → recicla conexões a cada 30min (mitiga memory leak em pg)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),
        "pool_pre_ping": os.getenv("DB_POOL_PRE_PING", "true").lower()
        in ("true", "1", "yes"),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
    }

    # --- JWT (P0-03: default inseguro removido) ---
    if _is_production():
        # Em produção exige segredo real; aborta no startup se ausente.
        from security_config import require_secret  # type: ignore

        JWT_SECRET_KEY = require_secret("JWT_SECRET_KEY", min_length=32)
        SECRET_KEY = require_secret("SECRET_KEY", min_length=32)
    else:
        # Em desenvolvimento aceita placeholder mas avisa.
        from security_config import require_secret  # type: ignore

        JWT_SECRET_KEY = require_secret("JWT_SECRET_KEY", min_length=32, allow_default=True)
        SECRET_KEY = require_secret("SECRET_KEY", min_length=32, allow_default=True)

    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas em segundos

    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # --- CORS ---
    CORS_HEADERS = "Content-Type"

    # --- Redis (Flask-Limiter storage + cache) ---
    # Default None para o health check usar fallback localhost
    # (em prod o .env.production define REDIS_URL=redis://siap-redis:6379/0)
    REDIS_URL = os.getenv("REDIS_URL", "").strip() or None

    # --- Site URL (links em emails) ---
    ARAOS_SITE_URL = os.getenv("ARAOS_SITE_URL", "https://araos.aracannabis.com.br").strip()

    # --- Upload de arquivos (P0-07) ---
    UPLOAD_FOLDER_EXAMES = os.path.join(os.getcwd(), "uploads", "exames")
    # 16MB — limite coerente entre rotas; app_cors_livre.py deve respeitar
    # este valor (P0-07 trata a divergência 500MB/50MB).
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx"}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    # Em produção todas as chaves são validadas em Config.__init__.


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # SQLite não suporta pool_size/max_overflow
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": False,
    }


# Dicionário de configurações
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
