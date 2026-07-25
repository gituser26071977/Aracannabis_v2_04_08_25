"""
AraOS Neurodevelopmental Module — Public API.

Módulo de assistência clínica, pesquisa científica, gestão, ensino e
indicadores em neurodesenvolvimento. Substitui e amplia o antigo
"módulo TEA", suportando TEA, TDAH, AH/SD, Dupla Excepcionalidade,
TOD, Transtornos de Linguagem, Deficiência Intelectual, Transtornos
Específicos de Aprendizagem e Outras Neurodivergências.

Sprint 1 — escopo:
    - Plugin subsystem de escalas neuropsicológicas
    - Escalas builtin: GAD-7, PHQ-9
    - Persistência polimórfica de respostas

Sprints futuros:
    - Sprint 2: 6 escalas adicionais (M-CHAT, CARS, ATEC, Vineland,
                SNAP-IV, SRS-2)
    - Sprint 3: ABC, PSQI, AQ, Conners + perfil multi-CID
    - Sprint 4: Medicações + Cannabis medicinal integrado
    - Sprint 5: 7 dashboards + 8 relatórios + 8 exportadores
    - Sprint 6: IA clínica + Observatório Sergipano
    - Sprint 7: Hardening + LGPD + produção
"""

from .scales import (
    ScaleAlreadyRegisteredError,
    ScaleInterpretation,
    ScaleNotFoundError,
    ScaleRegistry,
    ScaleResponseStore,
    ScaleResult,
    ScaleRunner,
    ScaleSpec,
    ScaleSubscale,
    ScaleValidationError,
    StoredScaleResponse,
)

__version__ = "1.0.0"
__status__ = "sprint-1"

__all__ = [
    # Plugin subsystem
    "ScaleSpec",
    "ScaleSubscale",
    "ScaleInterpretation",
    "ScaleResult",
    "ScaleRegistry",
    "ScaleAlreadyRegisteredError",
    "ScaleNotFoundError",
    "ScaleRunner",
    "ScaleValidationError",
    "ScaleResponseStore",
    "StoredScaleResponse",
]