"""
araos.clinical.genome.domain — Domain layer do Clinical Genome Engine.

Sprint 4.3 — ADR-0005.

Componentes:

- ``ClinicalGeneId`` — enumeração canônica de Genes (Registry v1.0).
- ``RegistryVersion`` — versionamento SemVer do Registry.
- ``GeneDefinition`` — VO imutável de definição de um Gene.
- ``ClinicalGeneRegistry`` — coleção imutável de GeneDefinitions
  válida em uma versão específica.
- ``seed.build_registry_v1_definitions`` — referência canônica do
  Registry v1.0.

Nenhuma dependência de I/O. Domain puro (DDD).
"""

from .clinical_gene_id import ClinicalGeneId
from .gene_definition import GeneDefinition
from .gene_registry import ClinicalGeneRegistry
from .registry_version import (
    CURRENT_REGISTRY_VERSION,
    RegistryVersion,
)
from .seed import (
    REGISTRY_V1_EFFECTIVE_FROM,
    build_registry_v1_definitions,
)

__all__ = [
    "ClinicalGeneId",
    "GeneDefinition",
    "ClinicalGeneRegistry",
    "RegistryVersion",
    "CURRENT_REGISTRY_VERSION",
    "REGISTRY_V1_EFFECTIVE_FROM",
    "build_registry_v1_definitions",
]