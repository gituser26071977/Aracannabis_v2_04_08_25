"""
ClinicalGeneId — Enumeração canônica dos Clinical Genes conhecidos.

Sprint 4.3 — ADR-0005 (Clinical Genome Engine, 1ª Iteração).

Esta enumeração representa o vocabulário **fechado e versionado** do
Clinical Gene Registry. Os valores são **as identidades** dos Genes
no modelo de domínio. Adicionar ou renomear um Gene exige incremento
de versão do Registry (v1.1, v1.2, 2.0 ...).

Registry atual: **v1.0** (fixado por esta ADR).

Princípio de nomenclatura (v1.0): Clinical Genes representam
**Funções Clínicas Fundamentais** — não qualidade, gravidade,
intensidade ou desfechos. Esses pertencem à Clinical Expression.

Exemplos:
- ``SLEEP`` (função) ≠ "qualidade do sono" (descrição da Expression).
- ``ANXIETY_REGULATION`` (função) ≠ "nível de ansiedade" (descrição
  da Expression).
"""

from __future__ import annotations

from enum import Enum


class ClinicalGeneId(str, Enum):
    """Identidade canônica de um Clinical Gene (Registry v1.0)."""

    SOCIAL_COMMUNICATION = "SOCIAL_COMMUNICATION"
    EXECUTIVE_FUNCTION = "EXECUTIVE_FUNCTION"
    SLEEP = "SLEEP"
    LANGUAGE = "LANGUAGE"
    EMOTIONAL_REGULATION = "EMOTIONAL_REGULATION"
    ANXIETY_REGULATION = "ANXIETY_REGULATION"
    MOBILITY = "MOBILITY"

    @classmethod
    def values(cls) -> list[str]:
        """Retorna todos os valores como ``list[str]``.

        Útil para validação de entrada (whitelist) e iteração sobre
        o Registry.
        """
        return [member.value for member in cls]

    @classmethod
    def contains(cls, value: str) -> bool:
        """Verifica se ``value`` é um ``ClinicalGeneId`` válido no Registry."""
        return value in cls.values()