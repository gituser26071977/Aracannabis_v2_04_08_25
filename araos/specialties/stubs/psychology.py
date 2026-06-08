"""
AraOS Specialty — Psicologia (Stub).

Especialidade: Psicologia
Categoria: Multiprofessional
Status: Planned

Week 10 — Specialty Framework Foundation (Part 9)

STUB — Sem regras clínicas específicas.
Apenas validação da arquitetura.
"""

from typing import List

from araos.specialties.core.definitions import (
    SpecialtyDefinition, SpecialtyCategory, SpecialtyStatus, SpecialtyCapability,
)
from araos.specialties.core.profile import SpecialtyProfile


PSYCHOLOGY_DEFINITION = SpecialtyDefinition(
    code="psychology",
    name="Psicologia",
    description="Acompanhamento psicológico e avaliação comportamental.",
    category=SpecialtyCategory.MULTIPROFESSIONAL,
    status=SpecialtyStatus.PLANNED,
    version="0.1.0",
    capabilities={
        SpecialtyCapability.CLINICAL_PROFILE,
        SpecialtyCapability.SPECIALTY_TIMELINE,
        SpecialtyCapability.SCALES,
        SpecialtyCapability.QUESTIONNAIRES,
        SpecialtyCapability.WORKFLOWS,
        SpecialtyCapability.DASHBOARD,
        SpecialtyCapability.KNOWLEDGE_BASE,
        SpecialtyCapability.AGENT_SUPPORT,
        SpecialtyCapability.EVOLUTION_TRACKING,
    },
    supported_entities=[
        "diagnosis", "risk_factor", "procedure",
    ],
)


class PsychologyProfile(SpecialtyProfile):
    """Profile especializado para Psicologia."""

    def __init__(self, patient_id: str, tenant_id: str):
        super().__init__(patient_id, tenant_id, specialty_code="psychology")

    def validate(self) -> List[str]:
        return []

    def get_definition(self) -> SpecialtyDefinition:
        return PSYCHOLOGY_DEFINITION
