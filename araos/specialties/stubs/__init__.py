"""
AraOS Specialty Stubs.

Stubs mínimos para validação da arquitetura.

Week 10 — Specialty Framework Foundation (Part 9)
"""

from .cannabis import (
    CANNABIS_DEFINITION,
    CannabisProfile,
)
from .nutrology import (
    NUTROLOGY_DEFINITION,
    NutrologyProfile,
)
from .psychiatry import (
    PSYCHIATRY_DEFINITION,
    PsychiatryProfile,
)
from .psychology import (
    PSYCHOLOGY_DEFINITION,
    PsychologyProfile,
)
from .cardiology import (
    CARDIOLOGY_DEFINITION,
    CardiologyProfile,
)
from .nephrology import (
    NEPHROLOGY_DEFINITION,
    NephrologyProfile,
)
from .pulmonology import (
    PULMONOLOGY_DEFINITION,
    PulmonologyProfile,
)
from .infectology import (
    INFECTOLOGY_DEFINITION,
    InfectologyProfile,
)

__all__ = [
    "CANNABIS_DEFINITION",
    "CannabisProfile",
    "NUTROLOGY_DEFINITION",
    "NutrologyProfile",
    "PSYCHIATRY_DEFINITION",
    "PsychiatryProfile",
    "PSYCHOLOGY_DEFINITION",
    "PsychologyProfile",
    "CARDIOLOGY_DEFINITION",
    "CardiologyProfile",
    "NEPHROLOGY_DEFINITION",
    "NephrologyProfile",
    "PULMONOLOGY_DEFINITION",
    "PulmonologyProfile",
    "INFECTOLOGY_DEFINITION",
    "InfectologyProfile",
]

# Lista de todas as definições para registro fácil
ALL_SPECIALTY_DEFINITIONS = [
    CANNABIS_DEFINITION,
    NUTROLOGY_DEFINITION,
    PSYCHIATRY_DEFINITION,
    PSYCHOLOGY_DEFINITION,
    CARDIOLOGY_DEFINITION,
    NEPHROLOGY_DEFINITION,
    PULMONOLOGY_DEFINITION,
    INFECTOLOGY_DEFINITION,
]
