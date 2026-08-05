"""
araos.clinical.genome — Clinical Genome Engine.

Sprint 4.3 — ADR-0005.

Primeira materialização computacional da Teoria do Clinical Genome.

Phase 1 — Clinical Gene Registry v1.0:

- ``domain`` — entidades de domínio puras (ClinicalGeneId,
  RegistryVersion, GeneDefinition, ClinicalGeneRegistry, seed v1.0).
- ``infrastructure`` — loader, validação, repository (InMemory).

Phase 2+ (próximas): ClinicalGene Aggregate Root, GeneService,
GeneProjection, REST API.
"""

from . import domain, infrastructure

__all__ = ["domain", "infrastructure"]