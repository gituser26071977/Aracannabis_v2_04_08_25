"""AraOS Psychiatry — Triagem e apoio à avaliação psiquiátrica.

Módulo dedicado que reutiliza a infraestrutura de escalas do AraOS
(`ScaleRegistry`, `ScaleRunner`, `ScaleResponseStore`) e o event store
clínico. Registra o instrumento `PSYCH_TRIAGE` no import.

O instrumento é multidimensional (escores independentes por domínio),
temporal, com módulo de risco suicida independente. Não estabelece
diagnóstico e não prescreve.
"""

from .application.narrative import build_checklist, build_narrative, polish_with_llm, sanitize
from .domain.explain import explain
from .domain.instrument import (
    build_interpretation,
    build_spec,
    load_config,
    parse_config,
    register_instrument,
)
from .domain.items import DomainDef, InstrumentConfig, PsychItem
from .domain.safety import assess_suicide
from .domain.scoring import Evaluation, derive_contexts, evaluate

register_instrument()

__all__ = [
    "InstrumentConfig",
    "PsychItem",
    "DomainDef",
    "Evaluation",
    "evaluate",
    "derive_contexts",
    "assess_suicide",
    "explain",
    "build_spec",
    "build_interpretation",
    "parse_config",
    "load_config",
    "register_instrument",
    "build_narrative",
    "build_checklist",
    "polish_with_llm",
    "sanitize",
]
