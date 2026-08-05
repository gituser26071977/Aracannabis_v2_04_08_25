"""
AraOS Neurodevelopmental — Branded IDs.

Tipos nominais (NewType) para type safety sem overhead em runtime.
Cada entidade do domínio possui seu próprio tipo de ID — confusões
em tempo de compilação são detectadas.

Convenções:
    - Todos os IDs são UUID4 em string (compatível com `araos.platform.tenant.models`).
    - `new_id()` gera novo UUID4.
    - IDs são imutáveis (str).
"""

from __future__ import annotations

import uuid
from typing import NewType

# ─── Branded IDs ────────────────────────────────────────────────────────────
# NewType cria tipo distinto em type checker (zero overhead em runtime).
# Erros do tipo "passar InterventionId onde se esperava DiagnosisId" são
# capturados por mypy/pyright sem custo de execução.

PatientId = NewType("PatientId", str)
"""ID administrativo do paciente (referência externa ao Clinical Identity)."""

ClinicalIdentityId = NewType("ClinicalIdentityId", str)
"""Aggregate Root — identidade clínica longitudinal permanente."""

DiagnosisId = NewType("DiagnosisId", str)
"""Entity — diagnóstico dentro da ClinicalIdentity."""

PhenotypeId = NewType("PhenotypeId", str)
"""Entity — fenótipo/manifestação observável."""

AssessmentId = NewType("AssessmentId", str)
"""Entity — aplicação de escala neuropsicológica."""

InterventionId = NewType("InterventionId", str)
"""Aggregate Root — qualquer intervenção clínica (medicação, cannabis, ABA...)."""

OutcomeId = NewType("OutcomeId", str)
"""Entity — resultado clínico derivado de eventos."""


def new_id() -> str:
    """
    Gera novo UUID4 como string.

    Usado como factory default para todas as entidades.
    Retorna str puro (não branded) — caller deve fazer cast se necessário.
    """
    return str(uuid.uuid4())