"""
ContextType — enumeração canônica dos tipos de ClinicalContext.

Sprint 4.2 — ADR-0003. Cada tipo representa uma categoria de contexto
clínico relevante para a evolução longitudinal do paciente.
"""

from __future__ import annotations

from enum import Enum


class ContextType(str, Enum):
    """Tipo de contexto clínico.

    Define a CATEGORIA do contexto. Cada categoria pode ter subtipos
    implícitos via `title`/`description` (ex: ClinicalEpisode pode ser
    crisis/hospitalization/behavioral).
    """
    CLINICAL_EPISODE = "clinical_episode"
    MEDICATION_CONTEXT = "medication_context"
    SCHOOL_CONTEXT = "school_context"
    FAMILY_CONTEXT = "family_context"
    ENVIRONMENTAL_CONTEXT = "environmental_context"
    DEVELOPMENTAL_MILESTONE = "developmental_milestone"
    BEHAVIORAL_PHASE = "behavioral_phase"
    SLEEP_PATTERN = "sleep_pattern"
    EDUCATIONAL_TRANSITION = "educational_transition"
    SOCIAL_CONTEXT = "social_context"

    @classmethod
    def values(cls) -> list[str]:
        return [t.value for t in cls]
