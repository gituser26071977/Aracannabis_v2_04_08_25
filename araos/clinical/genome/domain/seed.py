"""
Seed — Referência canônica do Clinical Gene Registry v1.0.

Sprint 4.3 — ADR-0005.

Este módulo é a **fonte da verdade** do Registry v1.0. Define os
sete Clinical Genes iniciais com suas descrições formais e
Clinical Functions associadas.

Qualquer alteração nesta listagem exige incremento da versão do
Registry (1.0 → 1.1, 1.2, 2.0 ...) e atualização do ADR-0005.

Princípio de nomenclatura (v1.0):
    Clinical Genes representam **Funções Clínicas Fundamentais**.
    Eles **não** representam qualidade, gravidade, intensidade
    ou desfechos. Esses pertencem à Clinical Expression.

Exemplos:
    - ``SLEEP`` (função) ≠ "qualidade do sono" (descrição da Expression).
    - ``ANXIETY_REGULATION`` (função) ≠ "nível de ansiedade"
      (descrição da Expression).
"""

from __future__ import annotations

from datetime import datetime, timezone

from .clinical_gene_id import ClinicalGeneId
from .gene_definition import GeneDefinition
from .registry_version import RegistryVersion


# Data fixa do Registry v1.0 — congelada por ADR-0005.
# Não usar ``datetime.now()`` para garantir reprodutibilidade.
REGISTRY_V1_EFFECTIVE_FROM: datetime = datetime(
    2026, 7, 17, 0, 0, 0, tzinfo=timezone.utc,
)


def _v1_registry_version() -> RegistryVersion:
    return RegistryVersion(
        major=1, minor=0, patch=None,
        effective_from=REGISTRY_V1_EFFECTIVE_FROM,
    )


def build_registry_v1_definitions() -> tuple[GeneDefinition, ...]:
    """Constrói as 7 GeneDefinitions canônicas do Registry v1.0.

    Retorna uma tupla imutável. A ordem segue a declaração do
    ADR-0005 (não-alfabética, semântica).
    """
    version = _v1_registry_version()

    return (
        GeneDefinition(
            id=ClinicalGeneId.SOCIAL_COMMUNICATION,
            display_name="Social Communication",
            description=(
                "Capacidade de comunicação social — interação recíproca, "
                "uso de comunicação não-verbal e adaptação a contextos "
                "sociais."
            ),
            clinical_functions=("communication", "language", "social"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.EXECUTIVE_FUNCTION,
            display_name="Executive Function",
            description=(
                "Funções executivas — atenção, planejamento, flexibilidade "
                "cognitiva e controle inibitório."
            ),
            clinical_functions=("attention", "planning", "flexibility"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description=(
                "Sono — função clínica fundamental caracterizada por "
                "arquitetura circadiana, duração, fragmentação e "
                "qualidade subjetiva (esta última pertence à Expression)."
            ),
            clinical_functions=("sleep", "circadian", "rest"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.LANGUAGE,
            display_name="Language",
            description=(
                "Linguagem expressiva e receptiva — vocabulário, "
                "morfossintaxe, pragmática e compreensão."
            ),
            clinical_functions=("language", "communication"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.EMOTIONAL_REGULATION,
            display_name="Emotional Regulation",
            description=(
                "Regulação emocional — modulação, expressão e reconhecimento "
                "de estados afetivos."
            ),
            clinical_functions=("emotion", "affect", "self-regulation"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.ANXIETY_REGULATION,
            display_name="Anxiety Regulation",
            description=(
                "Regulação da ansiedade — modulação de preocupação, medo e "
                "resposta de alarme (esta última pertence à Expression)."
            ),
            clinical_functions=("anxiety", "worry", "fear"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
        GeneDefinition(
            id=ClinicalGeneId.MOBILITY,
            display_name="Mobility",
            description=(
                "Mobilidade funcional — coordenação motora, marcha e "
                "capacidade de deslocamento."
            ),
            clinical_functions=("motor", "coordination", "gait"),
            registry_version=version,
            created_at=REGISTRY_V1_EFFECTIVE_FROM,
        ),
    )