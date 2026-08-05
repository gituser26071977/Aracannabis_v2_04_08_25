"""
ClinicalGeneRegistry — Coleção imutável de GeneDefinitions.

Sprint 4.3 — ADR-0005.

Representa um **snapshot versionado** do Clinical Gene Registry:
uma tupla imutável de ``GeneDefinition`` válida em uma
``RegistryVersion`` específica.

Invariantes enforced em ``__post_init__``:

- Não pode estar vazio.
- Todos os ``clinical_gene_id`` únicos (sem duplicatas).
- Todos os ``display_name`` únicos.
- Todas as definições vinculadas à **mesma** ``RegistryVersion``.
- Todas as definições devem ser ``GeneDefinition`` válidas.
- Compatibilidade com ``ClinicalGeneId`` enum: cada ``id`` da coleção
  deve existir no enum.

A coleção é **imutável** (``frozen=True``). Operações de filtro,
busca e iteração são read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from .clinical_gene_id import ClinicalGeneId
from .gene_definition import GeneDefinition
from .registry_version import RegistryVersion


@dataclass(frozen=True)
class ClinicalGeneRegistry:
    """Snapshot imutável do Clinical Gene Registry em uma versão."""

    version: RegistryVersion
    definitions: tuple[GeneDefinition, ...]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        # Não vazio.
        if not self.definitions:
            raise ValueError(
                "ClinicalGeneRegistry não pode estar vazio"
            )

        # Versão obrigatória.
        if not isinstance(self.version, RegistryVersion):
            raise ValueError(
                "ClinicalGeneRegistry.version deve ser RegistryVersion"
            )

        # Todas as definições devem ser GeneDefinition.
        for d in self.definitions:
            if not isinstance(d, GeneDefinition):
                raise ValueError(
                    f"definição inválida no Registry (esperado GeneDefinition, "
                    f"recebido {type(d).__name__})"
                )

        # Unicidade de ids.
        ids = [d.id for d in self.definitions]
        if len(ids) != len(set(ids)):
            duplicates = sorted(
                {i.value for i in ids if [d.id for d in self.definitions].count(i) > 1}
            )
            raise ValueError(
                f"ClinicalGeneRegistry contém IDs duplicados: {duplicates}"
            )

        # Unicidade de display_names.
        display_names = [d.display_name for d in self.definitions]
        if len(display_names) != len(set(display_names)):
            duplicates = sorted(
                {
                    n for n in display_names
                    if display_names.count(n) > 1
                }
            )
            raise ValueError(
                f"ClinicalGeneRegistry contém display_names duplicados: "
                f"{duplicates}"
            )

        # Unicidade de clinical_functions — pelo menos as primárias.
        primary_functions = [d.primary_clinical_function for d in self.definitions]
        if len(primary_functions) != len(set(primary_functions)):
            duplicates = sorted({
                f for f in primary_functions
                if primary_functions.count(f) > 1
            })
            raise ValueError(
                f"ClinicalGeneRegistry contém primary_clinical_function "
                f"duplicadas: {duplicates}"
            )

        # Compatibilidade com ClinicalGeneId enum.
        enum_ids = set(ClinicalGeneId.values())
        for d in self.definitions:
            # d.id pode ser ClinicalGeneId (caso normal) ou str (caso manual).
            id_value = (
                d.id.value if isinstance(d.id, ClinicalGeneId) else str(d.id)
            )
            if id_value not in enum_ids:
                raise ValueError(
                    f"Gene '{id_value}' não existe em ClinicalGeneId enum "
                    f"(Registry v{self.version.version_string})"
                )

        # Consistência de versão entre definições e snapshot.
        for d in self.definitions:
            if d.registry_version.version_string != self.version.version_string:
                raise ValueError(
                    f"GeneDefinition {d.id.value} tem versão "
                    f"{d.registry_version.version_string}, mas Registry está "
                    f"em {self.version.version_string}"
                )

        # created_at timezone-aware.
        if self.created_at.tzinfo is None:
            raise ValueError(
                "ClinicalGeneRegistry.created_at deve ser timezone-aware (UTC)"
            )

        # metadata imutável.
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(
                self, "metadata", MappingProxyType(dict(self.metadata))
            )

    # ─── Lookups ───────────────────────────────────────────────

    def get(self, gene_id: ClinicalGeneId | str) -> GeneDefinition | None:
        """Recupera a definição pelo ``clinical_gene_id``.

        Aceita ``ClinicalGeneId`` ou string. Retorna ``None`` se ausente.
        """
        target = gene_id.value if isinstance(gene_id, ClinicalGeneId) else gene_id
        for d in self.definitions:
            if d.id.value == target:
                return d
        return None

    def __contains__(self, gene_id: ClinicalGeneId | str) -> bool:
        return self.get(gene_id) is not None

    def __len__(self) -> int:
        return len(self.definitions)

    def __iter__(self) -> Iterator[GeneDefinition]:
        return iter(self.definitions)

    # ─── Serialização ──────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialização canônica do Registry (versão + lista de definições)."""
        return {
            "version": self.version.version_string,
            "effective_from": self.version.effective_from.isoformat(),
            "created_at": self.created_at.isoformat(),
            "definitions": [d.to_dict() for d in self.definitions],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ClinicalGeneRegistry":
        """Reconstrução determinística a partir de ``to_dict``."""
        if "version" not in data:
            raise ValueError(
                "ClinicalGeneRegistry.from_dict requer 'version'"
            )
        effective_from: datetime | None = None
        if "effective_from" in data and data["effective_from"]:
            effective_from = datetime.fromisoformat(data["effective_from"])
        version = RegistryVersion.parse(
            data["version"],
            effective_from=effective_from,
        )
        definitions = tuple(
            GeneDefinition.from_dict(d) for d in data.get("definitions", [])
        )
        kwargs: dict[str, Any] = {
            "version": version,
            "definitions": definitions,
        }
        if "created_at" in data and data["created_at"]:
            kwargs["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**kwargs)

    def __str__(self) -> str:
        return (
            f"ClinicalGeneRegistry(v{self.version.version_string}, "
            f"{len(self.definitions)} genes)"
        )