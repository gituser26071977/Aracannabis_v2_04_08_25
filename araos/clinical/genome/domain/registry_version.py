"""
RegistryVersion — Versionamento semântico do Clinical Gene Registry.

Sprint 4.3 — ADR-0005.

O Clinical Gene Registry é versionado explicitamente (SemVer) para
garantir **rastreabilidade científica, reprodutibilidade e
compatibilidade entre estudos e versões da plataforma**.

Regras de versionamento:

- Mudanças incrementais (adição ou renomeação de Gene mantendo
  compatibilidade retroativa) → bump **minor** (1.0 → 1.1 → 1.2 ...).
- Mudanças incompatíveis (reorganização conceitual) → bump **major**
  (1.x → 2.0).
- Correções puramente documentacionais → bump **patch** (1.0.0 → 1.0.1).

Versão atual: **1.0** (fixada por ADR-0005).

Toda referência a um ``clinical_gene_id`` carrega implicitamente
a versão do Registry sob a qual foi criada. Genes introduzidos em
versões futuras **não substituem** os anteriores — coexistem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


# Constante canônica do Registry atual (Sprint 4.3).
CURRENT_REGISTRY_VERSION: str = "1.0"


@dataclass(frozen=True)
class RegistryVersion:
    """Versão imutável do Clinical Gene Registry.

    Representa um snapshot versionado: identifica univocamente o conjunto
    de Genes válidos em um determinado momento (``effective_from``).

    Invariantes enforced em ``__post_init__``:

    - Formato SemVer (``MAJOR.MINOR`` ou ``MAJOR.MINOR.PATCH``).
    - ``major`` >= 1.
    - ``minor`` >= 0.
    - ``patch`` is None ou >= 0.
    - ``effective_from`` é timezone-aware (UTC).
    """

    major: int
    minor: int
    patch: int | None = None
    effective_from: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.major < 1:
            raise ValueError(
                f"Registry major version deve ser >= 1, recebido {self.major}"
            )
        if self.minor < 0:
            raise ValueError(
                f"Registry minor version deve ser >= 0, recebido {self.minor}"
            )
        if self.patch is not None and self.patch < 0:
            raise ValueError(
                f"Registry patch version deve ser >= 0, recebido {self.patch}"
            )
        if self.effective_from.tzinfo is None:
            raise ValueError(
                "RegistryVersion.effective_from deve ser timezone-aware (UTC)"
            )

    @property
    def version_string(self) -> str:
        """Representação canônica em string (``"1.0"`` ou ``"1.0.3"``)."""
        if self.patch is None:
            return f"{self.major}.{self.minor}"
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def parse(cls, version_string: str, effective_from: datetime | None = None) -> "RegistryVersion":
        """Parse de uma string SemVer.

        Aceita ``"1.0"`` (minor) ou ``"1.0.3"`` (minor.patch).
        """
        parts = version_string.split(".")
        if len(parts) not in (2, 3):
            raise ValueError(
                f"Registry version inválida: '{version_string}'. "
                "Esperado formato 'MAJOR.MINOR' ou 'MAJOR.MINOR.PATCH'."
            )
        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2]) if len(parts) == 3 else None
        except ValueError as exc:
            raise ValueError(
                f"Registry version inválida: '{version_string}'. "
                "Componentes devem ser inteiros."
            ) from exc
        return cls(
            major=major,
            minor=minor,
            patch=patch,
            effective_from=effective_from or datetime.now(timezone.utc),
        )

    @classmethod
    def current(cls) -> "RegistryVersion":
        """Retorna a versão atual do Registry (Registry v1.0)."""
        return cls.parse(CURRENT_REGISTRY_VERSION)

    def is_compatible_with(self, other: "RegistryVersion") -> bool:
        """Dois RegistryVersions são compatíveis se compartilham ``major``.

        Genes introduzidos em versões diferentes podem coexistir; a
        chave de compatibilidade é o ``major`` version.
        """
        return self.major == other.major

    def __str__(self) -> str:
        return self.version_string