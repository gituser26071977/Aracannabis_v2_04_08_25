"""
araos.clinical.genome.infrastructure — Infrastructure layer.

Sprint 4.3 — ADR-0005.

Componentes:

- ``registry_loader`` — carregamento + validação de Registry.
- ``registry_repository`` — contrato ABC + InMemory implementation.
- ``serialization`` — serialização canônica JSON + SHA-256 state_hash.
- ``replay`` — Replay Engine wrapper (Phase 2).

Implementação SQL virá na Phase 4 (migration 2026_07_19).
"""

from .registry_loader import (
    RegistryLoadError,
    load_registry,
    load_registry_v1,
    validate_gene_id,
    validate_registry_compatibility,
)
from .registry_repository import (
    ClinicalGeneRegistryRepository,
    REDACTED,
)
from .serialization import (
    compute_state_hash,
    event_to_canonical_json,
    events_to_canonical_json,
    gene_from_canonical_json,
    gene_to_canonical_json,
)

__all__ = [
    "ClinicalGeneRegistryRepository",
    "REDACTED",
    "RegistryLoadError",
    "load_registry",
    "load_registry_v1",
    "validate_gene_id",
    "validate_registry_compatibility",
    "compute_state_hash",
    "event_to_canonical_json",
    "events_to_canonical_json",
    "gene_from_canonical_json",
    "gene_to_canonical_json",
]