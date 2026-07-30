"""
AraOS Clinical Event Engine — Pacote principal.

Cross-specialty Event Sourcing para o AraOS (ADR-0001).

API pública:
    - ClinicalEventStore: contrato de persistência
    - InMemoryClinicalEventStore: implementação in-memory (testes)
    - SqlAlchemyClinicalEventStore: implementação PostgreSQL
    - ClinicalEventPublisher: ponto único de publicação
    - ClinicalEventModel: SQLAlchemy model
    - CLINICAL_EVENT_CATALOG: catálogo versionado
    - compute_event_hash, verify_chain, find_break: hash chain utilities
"""

from .catalog import (
    CLINICAL_EVENT_CATALOG,
    ClinicalEventDefinition,
    EventProducer,
    EventStatus,
    count_event_types,
    get_event_definition,
    is_known_event_type,
    list_event_types,
)
from .hash_chain import (
    GENESIS_HASH,
    canonical_form,
    compute_event_hash,
    find_break,
    verify_chain,
)
from .models import ClinicalEventModel, ClinicalEventSequence
from .publisher import (
    ClinicalEventPublisher,
    EventValidationError,
    UnknownEventTypeError,
)
from .store import (
    ClinicalEventStore,
    InMemoryClinicalEventStore,
    SqlAlchemyClinicalEventStore,
)
from .validators import is_valid_payload, validate_event_payload


__all__ = [
    # Modelo
    "ClinicalEventModel",
    "ClinicalEventSequence",
    # Catálogo
    "CLINICAL_EVENT_CATALOG",
    "ClinicalEventDefinition",
    "EventProducer",
    "EventStatus",
    "get_event_definition",
    "is_known_event_type",
    "list_event_types",
    "count_event_types",
    # Hash chain
    "GENESIS_HASH",
    "canonical_form",
    "compute_event_hash",
    "find_break",
    "verify_chain",
    # Store
    "ClinicalEventStore",
    "InMemoryClinicalEventStore",
    "SqlAlchemyClinicalEventStore",
    # Publisher
    "ClinicalEventPublisher",
    "EventValidationError",
    "UnknownEventTypeError",
    # Validators
    "validate_event_payload",
    "is_valid_payload",
]
