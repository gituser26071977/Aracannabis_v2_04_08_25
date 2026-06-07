"""
AraOS Platform — Shared Module.

Utilitários, tipos, contextos e constantes compartilhados.
"""

from .context import TenantContext
from .types import TenantID, UserID, EventID, SessionID, JSONDict, JSONList
from .errors import (
    AraOSPlatformError,
    EventValidationError,
    EventNotInCatalogError,
    EventPublishError,
    TenantNotFoundError,
    AuthenticationError,
    AuthorizationError,
)
from .constants import (
    PLATFORM_NAME,
    PLATFORM_VERSION,
    DEFAULT_TENANT_SETTINGS,
    DEFAULT_FEATURE_FLAGS,
)

__all__ = [
    "TenantContext",
    "TenantID",
    "UserID",
    "EventID",
    "SessionID",
    "JSONDict",
    "JSONList",
    "AraOSPlatformError",
    "EventValidationError",
    "EventNotInCatalogError",
    "EventPublishError",
    "TenantNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "PLATFORM_NAME",
    "PLATFORM_VERSION",
    "DEFAULT_TENANT_SETTINGS",
    "DEFAULT_FEATURE_FLAGS",
]
