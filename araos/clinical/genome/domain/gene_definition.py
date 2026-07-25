"""
GeneDefinition — Definição formal de um Clinical Gene.

Sprint 4.3 — ADR-0005.

Value Object imutável (``frozen=True``) que representa a definição
canônica de um Clinical Gene em uma versão específica do Registry.

Cada Gene é definido por:

- ``id`` — identidade canônica (ClinicalGeneId, vinda do Registry).
- ``display_name`` — nome legível para humanos.
- ``description`` — descrição clínica do que o Gene representa.
- ``clinical_functions`` — funções semânticas associadas (substitui
  o termo legado ``capability``). Tupla imutável.
- ``registry_version`` — versão do Registry à qual esta definição
  está vinculada.
- ``created_at`` — timestamp UTC da criação da definição.
- ``metadata`` — extensões opcionais (labels livres, hints).

Invariantes enforced:

- ``clinical_functions`` não-vazia (pelo menos uma função semântica).
- ``display_name`` e ``description`` não-vazios.
- ``registry_version`` é obrigatória.
- Tuplas/listas no ``metadata`` devem ser imutáveis (``Mapping``,
  ``Sequence``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from .clinical_gene_id import ClinicalGeneId
from .registry_version import RegistryVersion


@dataclass(frozen=True)
class GeneDefinition:
    """Definição imutável de um Clinical Gene."""

    id: ClinicalGeneId
    display_name: str
    description: str
    clinical_functions: tuple[str, ...]
    registry_version: RegistryVersion
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        # display_name não-vazio.
        if not self.display_name or not self.display_name.strip():
            raise ValueError(
                f"GeneDefinition.display_name não pode ser vazio "
                f"(gene_id={self.id.value})"
            )

        # description não-vazia.
        if not self.description or not self.description.strip():
            raise ValueError(
                f"GeneDefinition.description não pode ser vazio "
                f"(gene_id={self.id.value})"
            )

        # clinical_functions obrigatória.
        if not self.clinical_functions:
            raise ValueError(
                f"GeneDefinition.clinical_functions é obrigatória "
                f"(gene_id={self.id.value})"
            )
        for fn in self.clinical_functions:
            if not isinstance(fn, str) or not fn.strip():
                raise ValueError(
                    f"clinical_functions deve conter apenas strings não-vazias "
                    f"(gene_id={self.id.value})"
                )

        # registry_version obrigatória.
        if not isinstance(self.registry_version, RegistryVersion):
            raise ValueError(
                f"GeneDefinition.registry_version deve ser RegistryVersion "
                f"(gene_id={self.id.value})"
            )

        # created_at timezone-aware.
        if self.created_at.tzinfo is None:
            raise ValueError(
                f"GeneDefinition.created_at deve ser timezone-aware (UTC) "
                f"(gene_id={self.id.value})"
            )

        # metadata imutável.
        if not isinstance(self.metadata, MappingProxyType):
            # Aceitar Mapping mas converter para MappingProxyType (frozen).
            object.__setattr__(
                self, "metadata", MappingProxyType(dict(self.metadata))
            )

    @property
    def primary_clinical_function(self) -> str:
        """Retorna a função semântica primária (primeira da tupla)."""
        return self.clinical_functions[0]

    def to_dict(self) -> dict[str, Any]:
        """Serialização canônica (sem ``metadata`` privado).

        Inclui apenas campos públicos estáveis. Útil para JSON,
        auditoria e reconstrução determinística.
        """
        return {
            "id": self.id.value,
            "display_name": self.display_name,
            "description": self.description,
            "clinical_functions": list(self.clinical_functions),
            "registry_version": self.registry_version.version_string,
            "registry_version_effective_from": self.registry_version.effective_from.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GeneDefinition":
        """Reconstrução determinística a partir de ``to_dict``.

        ``registry_version`` é obrigatório; campos desconhecidos são
        preservados em ``metadata``.
        """
        if "registry_version" not in data:
            raise ValueError(
                "GeneDefinition.from_dict requer 'registry_version'"
            )
        effective_from: datetime | None = None
        if (
            "registry_version_effective_from" in data
            and data["registry_version_effective_from"]
        ):
            effective_from = datetime.fromisoformat(
                data["registry_version_effective_from"]
            )
        known_keys = {
            "id", "display_name", "description",
            "clinical_functions", "registry_version",
            "registry_version_effective_from", "created_at",
        }
        extra_metadata = {
            k: v for k, v in data.items() if k not in known_keys
        }
        kwargs: dict[str, Any] = {
            "id": ClinicalGeneId(data["id"]),
            "display_name": data["display_name"],
            "description": data["description"],
            "clinical_functions": tuple(data["clinical_functions"]),
            "registry_version": RegistryVersion.parse(
                data["registry_version"],
                effective_from=effective_from,
            ),
            "metadata": MappingProxyType(extra_metadata),
        }
        if "created_at" in data and data["created_at"]:
            kwargs["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**kwargs)

    def __str__(self) -> str:
        return (
            f"GeneDefinition({self.id.value} v{self.registry_version})"
        )