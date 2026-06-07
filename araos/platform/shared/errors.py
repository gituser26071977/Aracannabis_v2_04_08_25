"""
AraOS Platform — Shared Errors.

Exceções padronizadas usadas em TODOS os módulos da plataforma.
Isso permite tratamento uniforme de erros entre SIAP, Voice, e Smart Flow.
"""

from typing import Optional, Dict, Any


class AraOSPlatformError(Exception):
    """Base para todas as exceções da plataforma."""
    
    def __init__(
        self,
        message: str,
        code: str = None,
        details: Dict[str, Any] = None,
        http_status: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__.upper().replace("ERROR", "")
        self.details = details or {}
        self.http_status = http_status
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": True,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ─── Event Errors ────────────────────────────────────────────────────

class EventValidationError(AraOSPlatformError):
    """Evento não passou na validação."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, code="EVENT_VALIDATION", details=details, http_status=400)


class EventNotInCatalogError(AraOSPlatformError):
    """Evento não está registrado no catálogo."""
    def __init__(self, event_type: str):
        super().__init__(
            f"Event type '{event_type}' not registered in catalog",
            code="EVENT_NOT_IN_CATALOG",
            details={"event_type": event_type},
            http_status=400,
        )


class EventPublishError(AraOSPlatformError):
    """Falha ao publicar evento."""
    def __init__(self, message: str, event_type: str = None):
        super().__init__(
            message,
            code="EVENT_PUBLISH_FAILED",
            details={"event_type": event_type},
            http_status=502,
        )


class EventConsumeError(AraOSPlatformError):
    """Falha ao consumir evento."""
    def __init__(self, message: str, event_id: str = None):
        super().__init__(
            message,
            code="EVENT_CONSUME_FAILED",
            details={"event_id": event_id},
            http_status=500,
        )


class EventRetryExhaustedError(AraOSPlatformError):
    """Todas as tentativas de reprocessamento esgotadas."""
    def __init__(self, event_id: str, max_retries: int):
        super().__init__(
            f"Event {event_id} exhausted all {max_retries} retries",
            code="EVENT_RETRY_EXHAUSTED",
            details={"event_id": event_id, "max_retries": max_retries},
            http_status=500,
        )


# ─── Tenant Errors ───────────────────────────────────────────────────

class TenantNotFoundError(AraOSPlatformError):
    """Tenant não encontrado."""
    def __init__(self, tenant_id: str):
        super().__init__(
            f"Tenant '{tenant_id}' not found",
            code="TENANT_NOT_FOUND",
            details={"tenant_id": tenant_id},
            http_status=404,
        )


class TenantResolutionError(AraOSPlatformError):
    """Falha ao resolver tenant a partir de request."""
    def __init__(self, message: str):
        super().__init__(
            message,
            code="TENANT_RESOLUTION_FAILED",
            http_status=400,
        )


class TenantFeatureNotEnabledError(AraOSPlatformError):
    """Feature não habilitada para o tenant."""
    def __init__(self, tenant_id: str, feature: str):
        super().__init__(
            f"Feature '{feature}' not enabled for tenant '{tenant_id}'",
            code="FEATURE_NOT_ENABLED",
            details={"tenant_id": tenant_id, "feature": feature},
            http_status=403,
        )


# ─── Identity Errors ─────────────────────────────────────────────────

class AuthenticationError(AraOSPlatformError):
    """Falha de autenticação."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTHENTICATION_FAILED", http_status=401)


class AuthorizationError(AraOSPlatformError):
    """Falta de permissão."""
    def __init__(self, permission: str, user_id: str = None):
        super().__init__(
            f"Permission '{permission}' denied",
            code="AUTHORIZATION_DENIED",
            details={"permission": permission, "user_id": user_id},
            http_status=403,
        )


class TokenExpiredError(AraOSPlatformError):
    """Token expirado."""
    def __init__(self):
        super().__init__(
            "Token expired",
            code="TOKEN_EXPIRED",
            http_status=401,
        )


class TokenInvalidError(AraOSPlatformError):
    """Token inválido."""
    def __init__(self, reason: str = None):
        super().__init__(
            f"Invalid token: {reason}" if reason else "Invalid token",
            code="TOKEN_INVALID",
            http_status=401,
        )


# ─── Audit Errors ────────────────────────────────────────────────────

class AuditLogError(AraOSPlatformError):
    """Falha ao registrar ou consultar audit log."""
    def __init__(self, message: str):
        super().__init__(message, code="AUDIT_LOG_FAILED", http_status=500)


class AuditQueryError(AraOSPlatformError):
    """Falha na consulta de audit logs."""
    def __init__(self, message: str):
        super().__init__(message, code="AUDIT_QUERY_FAILED", http_status=500)


# ─── Feature Flag Errors ─────────────────────────────────────────────

class FeatureFlagError(AraOSPlatformError):
    """Erro no serviço de feature flags."""
    def __init__(self, message: str):
        super().__init__(message, code="FEATURE_FLAG_ERROR", http_status=500)


# ─── General Platform Errors ─────────────────────────────────────────

class ConfigurationError(AraOSPlatformError):
    """Configuração inválida ou ausente."""
    def __init__(self, message: str, config_key: str = None):
        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key},
            http_status=500,
        )


class NotImplementedError(AraOSPlatformError):
    """Funcionalidade ainda não implementada."""
    def __init__(self, feature: str):
        super().__init__(
            f"Feature '{feature}' not yet implemented",
            code="NOT_IMPLEMENTED",
            details={"feature": feature},
            http_status=501,
        )


class ValidationError(AraOSPlatformError):
    """Erro de validação genérico."""
    def __init__(self, message: str, field: str = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field},
            http_status=400,
        )


class DependencyError(AraOSPlatformError):
    """Erro em dependência externa (DB, Redis, API, etc)."""
    def __init__(self, message: str, dependency: str = None):
        super().__init__(
            message,
            code="DEPENDENCY_ERROR",
            details={"dependency": dependency},
            http_status=503,
        )
