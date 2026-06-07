"""
AraOS Platform — Contracts (ABC/Protocol).

Este pacote define as interfaces abstratas da Platform Layer.
TODAS as implementações concretas devem satisfazer estes contratos.

Nenhum módulo consumer deve importar implementações diretamente.
Deve importar apenas deste pacote.

Exemplo:
    from araos.platform.contracts import TenantProvider
    from araos.platform.contracts import IdentityProvider
    from araos.platform.contracts import EventPublisher, EventConsumer
    from araos.platform.contracts import AuditProvider
"""

from .tenant import TenantProvider, TenantSettingsProvider
from .identity import IdentityProvider, TokenProvider
from .event_bus import EventPublisher, EventConsumer, EventBus
from .audit import AuditProvider
from .feature_flags import FeatureFlagProvider, FeatureFlagContext, FeatureFlagState

__all__ = [
    "TenantProvider",
    "TenantSettingsProvider",
    "IdentityProvider",
    "TokenProvider",
    "EventPublisher",
    "EventConsumer",
    "EventBus",
    "AuditProvider",
    "FeatureFlagProvider",
    "FeatureFlagContext",
    "FeatureFlagState",
]
