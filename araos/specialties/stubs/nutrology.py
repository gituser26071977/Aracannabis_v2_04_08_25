"""
AraOS Specialty — Nutrologia (Stub).

Especialidade: Nutrologia
Categoria: Medical
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


NUTROLOGY_DEFINITION = SpecialtyDefinition(
    code="nutrology",
    name="Nutrologia",
    description="Acompanhamento nutricional e metabólico.",
    category=SpecialtyCategory.MEDICAL,
    status=SpecialtyStatus.PLANNED,
    version="0.1.0",
    capabilities={
        SpecialtyCapability.CLINICAL_PROFILE,
        SpecialtyCapability.SPECIALTY_TIMELINE,
        SpecialtyCapability.PROTOCOLS,
        SpecialtyCapability.SCALES,
        SpecialtyCapability.WORKFLOWS,
        SpecialtyCapability.DASHBOARD,
        SpecialtyCapability.KNOWLEDGE_BASE,
        SpecialtyCapability.AGENT_SUPPORT,
        SpecialtyCapability.EVOLUTION_TRACKING,
    },
    supported_entities=[
        "diagnosis", "medication", "allergy", "risk_factor", "procedure",
    ],
)


class NutrologyProfile(SpecialtyProfile):
    """Profile especializado para Nutrologia."""

    def __init__(self, patient_id: str, tenant_id: str):
        super().__init__(patient_id, tenant_id, specialty_code="nutrology")

    def validate(self) -> List[str]:
        return []

    def get_definition(self) -> SpecialtyDefinition:
        return NUTROLOGY_DEFINITION
