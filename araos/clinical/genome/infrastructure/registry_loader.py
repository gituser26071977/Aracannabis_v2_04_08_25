"""
Registry Loader — Carregamento e validação do Clinical Gene Registry.

Sprint 4.3 — ADR-0005.

O Loader é a porta de entrada única para construir um
``ClinicalGeneRegistry`` em memória. Centraliza:

- Carregamento do **Seed canônico** (Registry v1.0).
- Construção a partir de uma lista customizada (testes, versões
  futuras).
- Validação estrutural de integridade.

Invariantes enforced (delegadas ao ``ClinicalGeneRegistry``):

- IDs únicos.
- display_names únicos.
- primary_clinical_function únicas.
- Compatibilidade com ``ClinicalGeneId`` enum.
- Consistência de ``registry_version``.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from ..domain.clinical_gene_id import ClinicalGeneId
from ..domain.gene_definition import GeneDefinition
from ..domain.gene_registry import ClinicalGeneRegistry
from ..domain.registry_version import RegistryVersion
from ..domain.seed import build_registry_v1_definitions


class RegistryLoadError(ValueError):
    """Erro de carregamento/validação do Registry."""


def load_registry_v1() -> ClinicalGeneRegistry:
    """Carrega o Registry canônico v1.0 (Seed oficial ADR-0005).

    Retorna um ``ClinicalGeneRegistry`` imutável com os 7 Genes
    iniciais.
    """
    return ClinicalGeneRegistry(
        version=RegistryVersion.current(),
        definitions=build_registry_v1_definitions(),
    )


def load_registry(
    version: RegistryVersion,
    definitions: Iterable[GeneDefinition],
) -> ClinicalGeneRegistry:
    """Carrega um Registry a partir de definições arbitrárias.

    Usado para:
    - Testes (versões alternativas, mocking).
    - Futuras versões do Registry (1.1, 2.0 …).

    Invariantes enforced por ``ClinicalGeneRegistry.__post_init__``.
    """
    defs_list: Sequence[GeneDefinition] = tuple(definitions)
    if not defs_list:
        raise RegistryLoadError(
            "Registry não pode ser carregado sem definições"
        )
    return ClinicalGeneRegistry(
        version=version,
        definitions=defs_list,
    )


def validate_gene_id(gene_id: str) -> ClinicalGeneId:
    """Valida se ``gene_id`` é um ``ClinicalGeneId`` válido.

    Levanta ``RegistryLoadError`` se inválido.
    """
    if not ClinicalGeneId.contains(gene_id):
        raise RegistryLoadError(
            f"clinical_gene_id '{gene_id}' não existe no Registry "
            f"v{RegistryVersion.current().version_string}. "
            f"Válidos: {ClinicalGeneId.values()}"
        )
    return ClinicalGeneId(gene_id)


def validate_registry_compatibility(
    registry: ClinicalGeneRegistry,
    gene_id: ClinicalGeneId | str,
) -> None:
    """Valida que ``gene_id`` é compatível com o ``registry``.

    Usado quando se consome um Gene carregado em uma versão do Registry
    mas o código opera em outra versão (ex: serialização legacy).

    Regras:
    - ``gene_id`` deve existir no enum atual **e** no registry.
    """
    gene_id_value = (
        gene_id.value if isinstance(gene_id, ClinicalGeneId) else str(gene_id)
    )
    if gene_id_value not in ClinicalGeneId.values():
        raise RegistryLoadError(
            f"Gene '{gene_id_value}' não existe no enum ClinicalGeneId atual"
        )
    if gene_id_value not in registry:
        raise RegistryLoadError(
            f"Gene '{gene_id_value}' não existe no Registry "
            f"v{registry.version.version_string}"
        )