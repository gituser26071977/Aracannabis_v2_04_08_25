"""
AraOS Platform — Shared Constants.

Constantes globais usadas em múltiplos módulos.
"""

# Plataforma
PLATFORM_NAME = "AraOS"
PLATFORM_VERSION = "1.0.0"
PLATFORM_ENVIRONMENTS = {"development", "staging", "production", "test"}

# Tenant
DEFAULT_TENANT_SETTINGS = {
    "max_users": 10,
    "max_consultations_per_day": 100,
    "storage_quota_mb": 1024,
    "voice_enabled": False,
    "smart_flow_enabled": False,
    "concierge_enabled": False,
    "biometric_auth": False,
    "api_rate_limit": 1000,  # requests/hour
}

# Event Bus
EVENT_BUS_DEFAULT_TIMEOUT = 30  # seconds
EVENT_BUS_BATCH_SIZE = 100
EVENT_BUS_MAX_WAIT_SECONDS = 5

# Audit
AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years (LGPD requirement)
AUDIT_LOG_BATCH_SIZE = 500

# Timeouts
DEFAULT_HTTP_TIMEOUT = 30
DEFAULT_DB_TIMEOUT = 30

# File size limits
MAX_DOCUMENT_SIZE_MB = 50
MAX_AUDIO_SIZE_MB = 100
MAX_VIDEO_SIZE_MB = 500

# Feature flags defaults
DEFAULT_FEATURE_FLAGS = {
    "voice_copilot": False,
    "smart_flow": False,
    "biometric_checkin": False,
    "ai_concierge": False,
    "advanced_analytics": False,
    "multi_clinic": False,
    "api_access": False,
    "white_label": False,
    "custom_integrations": False,
}
