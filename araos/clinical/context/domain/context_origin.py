"""
ContextOrigin — enumeração da origem do ClinicalContext.

Define COMO o contexto foi criado:
    - manual: criado por profissional de saúde
    - rule_engine: sugerido por regra automática (Sprint 4.2)
    - artificial_intelligence: sugerido por modelo (Sprint 5+ stub)
    - import: importado de sistema externo
    - research: definido por estudo clínico
"""

from __future__ import annotations

from enum import Enum


class ContextOrigin(str, Enum):
    """Origem do contexto."""
    MANUAL = "manual"
    RULE_ENGINE = "rule_engine"
    ARTIFICIAL_INTELLIGENCE = "artificial_intelligence"
    IMPORT = "import"
    RESEARCH = "research"

    @property
    def is_automated(self) -> bool:
        """Origens automatizadas — exigem confirmação humana."""
        return self in (ContextOrigin.RULE_ENGINE, ContextOrigin.ARTIFICIAL_INTELLIGENCE)

    @classmethod
    def values(cls) -> list[str]:
        return [o.value for o in cls]
