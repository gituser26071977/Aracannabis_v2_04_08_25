"""
AraOS Platform — Unified SDK.

Único ponto de entrada para todos os consumidores da Platform Layer.
Nenhum módulo deve acessar implementações diretamente.

Uso:
    from araos.platform.sdk import (
        TenantContext,
        EventEnvelope,
        EventCatalog,
        AuditProvider,
        IdentityProvider,
        FeatureFlagService,
    )

Arquitetura:
    - SIAP (Flask) consome via este SDK
    - Voice (FastAPI) consome via este SDK
    - Smart Flow (FastAPI) consome via este SDK
    - Todos usam os MESMOS contratos e convenções
"""

# Contexto
from araos.platform.shared.context import TenantContext

# Eventos
from araos.platform.events.schemas import EventEnvelope, EventPayload, EventMetadata
from araos.platform.events.catalog import EventCatalog, EventDefinition
from araos.platform.events.json_schemas import SchemaRegistry, get_schema_registry

# Contratos (ABC)
from araos.platform.contracts.tenant import TenantProvider, TenantSettingsProvider
from araos.platform.contracts.identity import IdentityProvider, TokenProvider
from araos.platform.contracts.event_bus import EventPublisher, EventConsumer, EventBus
from araos.platform.contracts.audit import AuditProvider

# Feature Flags
from araos.platform.feature_flags.service import FeatureFlagService, FeatureFlagContext

# Identity Client
from araos.platform.identity.client import IdentityClient

# Erros
from araos.platform.shared.errors import (
    AraOSPlatformError,
    EventValidationError,
    EventNotInCatalogError,
    TenantNotFoundError,
    AuthenticationError,
    AuthorizationError,
)

# Constantes
from araos.platform.shared.constants import PLATFORM_NAME, PLATFORM_VERSION

__all__ = [
    # Contexto
    "TenantContext",
    
    # Eventos
    "EventEnvelope",
    "EventPayload",
    "EventMetadata",
    "EventCatalog",
    "EventDefinition",
    "SchemaRegistry",
    "get_schema_registry",
    
    # Contratos
    "TenantProvider",
    "TenantSettingsProvider",
    "IdentityProvider",
    "TokenProvider",
    "EventPublisher",
    "EventConsumer",
    "EventBus",
    "AuditProvider",
    
    # Serviços
    "FeatureFlagService",
    "FeatureFlagContext",
    "IdentityClient",
    
    # Erros
    "AraOSPlatformError",
    "EventValidationError",
    "EventNotInCatalogError",
    "TenantNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    
    # Constantes
    "PLATFORM_NAME",
    "PLATFORM_VERSION",
]
