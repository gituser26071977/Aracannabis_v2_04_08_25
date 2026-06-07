"""
AraOS Platform — Events Module.

Módulo central para event-driven architecture.
Todos os eventos da plataforma passam por aqui.

Uso rápido:
    from araos.platform.events import EventEnvelope, EventCatalog
    
    catalog = EventCatalog()
    event = EventEnvelope(
        event_type="PATIENT_CREATED",
        tenant_id="org_123",
        aggregate_type="patient",
        aggregate_id="pat_456",
        payload=EventPayload(data={"name": "João"}),
    )
    event.validate()  # Valida contra o catálogo
"""

from .schemas import EventEnvelope, EventPayload, EventMetadata
from .catalog import EventCatalog, EventDefinition
from .json_schemas import SchemaRegistry, get_schema_registry

__all__ = [
    "EventEnvelope",
    "EventPayload",
    "EventMetadata",
    "EventCatalog",
    "EventDefinition",
    "SchemaRegistry",
    "get_schema_registry",
]
