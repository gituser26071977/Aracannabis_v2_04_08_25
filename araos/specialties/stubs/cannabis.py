"""
AraOS Specialty — Cannabis Medicinal (Stub).

Especialidade: Cannabis Medicinal
Categoria: Integrative
Status: Planned

Week 10 — Specialty Framework Foundation (Part 9)

STUB — Sem regras clínicas específicas.
Apenas validação da arquitetura.
"""

from typing import List, Dict, Any

from araos.specialties.core.definitions import (
    SpecialtyDefinition, SpecialtyCategory, SpecialtyStatus, SpecialtyCapability,
)
from araos.specialties.core.profile import SpecialtyProfile, SpecialtyField


CANNABIS_DEFINITION = SpecialtyDefinition(
    code="cannabis",
    name="Cannabis Medicinal",
    description="Acompanhamento de pacientes em tratamento com cannabis medicinal.",
    category=SpecialtyCategory.INTEGRATIVE,
    status=SpecialtyStatus.PLANNED,
    version="0.1.0",
    capabilities={
        SpecialtyCapability.CLINICAL_PROFILE,
        SpecialtyCapability.SPECIALTY_TIMELINE,
        SpecialtyCapability.PROTOCOLS,
        SpecialtyCapability.WORKFLOWS,
        SpecialtyCapability.DASHBOARD,
        SpecialtyCapability.KNOWLEDGE_BASE,
        SpecialtyCapability.AGENT_SUPPORT,
        SpecialtyCapability.DOSE_TRACKING,
        SpecialtyCapability.EVOLUTION_TRACKING,
    },
    supported_entities=[
        "diagnosis", "medication", "allergy", "risk_factor",
    ],
)


class CannabisProfile(SpecialtyProfile):
    """Profile especializado para Cannabis Medicinal."""

    def __init__(self, patient_id: str, tenant_id: str):
        super().__init__(patient_id, tenant_id, specialty_code="cannabis")

    def validate(self) -> List[str]:
        """Valida o profile."""
        errors = []
        # Stub: validações serão implementadas no módulo específico
        return errors

    def get_definition(self) -> SpecialtyDefinition:
        """Retorna a definição da especialidade."""
        return CANNABIS_DEFINITION
