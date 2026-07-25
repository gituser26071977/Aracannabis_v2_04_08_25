"""
Registry Repository — Persistência do Clinical Gene Registry.

Sprint 4.3 — ADR-0005.

Esta Sprint implementa apenas o contrato (ABC) e a versão
``InMemory`` (default para testes e operação síncrona). A
implementação SQL (``REDACTED``)
será entregue na Sprint 4.3 Phase 4, junto com a migration
``2026_07_19_clinical_genome_s43.py``.

A interface é desenhada para que:

- O carregamento seja **idempotente** (chamadas repetidas retornam
  o mesmo Registry).
- O versionamento seja **explícito**: cada Registry carregado
  carrega sua ``RegistryVersion``.
- A versão atual (``CURRENT_REGISTRY_VERSION``) seja **cacheada**
  após o primeiro carregamento.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

from ..domain.clinical_gene_id import ClinicalGeneId
from ..domain.gene_registry import ClinicalGeneRegistry
from ..domain.registry_version import RegistryVersion


class ClinicalGeneRegistryRepository(ABC):
    """Contrato de persistência do Clinical Gene Registry."""

    @abstractmethod
    def get_version(self, version: str) -> ClinicalGeneRegistry | None:
        """Recupera Registry por versão (``"1.0"``). ``None`` se ausente."""

    @abstractmethod
    def get_current(self) -> ClinicalGeneRegistry:
        """Recupera a versão atual do Registry."""

    @abstractmethod
    def list_versions(self) -> list[str]:
        """Lista todas as versões disponíveis."""

    @abstractmethod
    def save(self, registry: ClinicalGeneRegistry) -> None:
        """Persiste um Registry. Idempotente (mesma versão → sobrescreve)."""


class REDACTED(ClinicalGeneRegistryRepository):
    """Repositório in-memory (testes, operação síncrona, Phase 1).

    Por padrão, pré-carrega o Registry v1.0. Suporta múltiplas
    versões em memória simultaneamente.
    """

    def __init__(self, preload: bool = True) -> None:
        self._by_version: Dict[str, ClinicalGeneRegistry] = {}
        if preload:
            from .registry_loader import load_registry_v1
            self.save(load_registry_v1())

    def get_version(self, version: str) -> ClinicalGeneRegistry | None:
        return self._by_version.get(version)

    def get_current(self) -> ClinicalGeneRegistry:
        """Retorna a versão mais alta do Registry em memória.

        Critério de ordenação: ``major`` × 1000 + ``minor`` (compatível
        com SemVer até ``99.999``). ``patch`` desempata.
        """
        if not self._by_version:
            raise RuntimeError(
                "REDACTED vazio. "
                "Faça preload ou save() antes de get_current()."
            )
        versions = [RegistryVersion.parse(v) for v in self._by_version]
        versions.sort(
            key=lambda v: (v.major, v.minor, v.patch if v.patch is not None else 0),
            reverse=True,
        )
        top = versions[0]
        return self._by_version[top.version_string]  # type: ignore[index]

    def list_versions(self) -> list[str]:
        return sorted(self._by_version.keys())

    def save(self, registry: ClinicalGeneRegistry) -> None:
        version_key = registry.version.version_string
        self._by_version[version_key] = registry

    # ─── Helpers de domínio ─────────────────────────────────────

    def is_known(self, gene_id: ClinicalGeneId | str) -> bool:
        """Verifica se ``gene_id`` é conhecido em alguma versão carregada."""
        target = gene_id.value if isinstance(gene_id, ClinicalGeneId) else gene_id
        return any(
            definition.id.value == target
            for reg in self._by_version.values()
            for definition in reg
        )

    def __contains__(self, gene_id: ClinicalGeneId | str) -> bool:
        return self.is_known(gene_id)

    def __len__(self) -> int:
        return len(self._by_version)