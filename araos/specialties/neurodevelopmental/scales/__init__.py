"""
AraOS Neurodevelopmental — Scales Plugin Subsystem.

API pública do subsistema de escalas neuropsicológicas.

Uso típico:

    from araos.specialties.neurodevelopmental.scales import (
        ScaleRegistry, ScaleRunner, ScaleResponseStore,
    )

    # 1. Listar escalas disponíveis
    for spec in ScaleRegistry.list():
        print(spec.code, spec.name)

    # 2. Aplicar uma escala
    spec = ScaleRegistry.get("GAD7")
    raw = {"q1": 2, "q2": 3, "q3": 1, "q4": 2, "q5": 0, "q6": 1, "q7": 3}
    result = ScaleRunner(spec).run(raw)
    print(result.scores, result.interpretation)

    # 3. Persistir resposta
    stored = ScaleResponseStore(db_session).save(
        tenant_id="...",
        patient_id="...",
        scale_code="GAD7",
        raw_responses=raw,
        applied_by="profissional_uuid",
    )

    # 4. Recuperar histórico do paciente
    history = ScaleResponseStore(db_session).list_for_patient(
        tenant_id="...",
        patient_id="...",
        scale_code="GAD7",
    )
"""

from .base import (
    ComputedScores,
    RawResponses,
    ScaleInterpretation,
    ScaleResult,
    ScaleSpec,
    ScaleSubscale,
)
from .registry import (
    ScaleAlreadyRegisteredError,
    ScaleNotFoundError,
    ScaleRegistry,
)
from .runner import ScaleRunner, ScaleValidationError
from .store import ScaleResponseStore, StoredScaleResponse

# Auto-registro das escalas builtin no import
from . import builtins  # noqa: F401

__all__ = [
    # Base
    "ComputedScores",
    "RawResponses",
    "ScaleInterpretation",
    "ScaleResult",
    "ScaleSpec",
    "ScaleSubscale",
    # Registry
    "ScaleRegistry",
    "ScaleAlreadyRegisteredError",
    "ScaleNotFoundError",
    # Runner
    "ScaleRunner",
    "ScaleValidationError",
    # Store
    "ScaleResponseStore",
    "StoredScaleResponse",
]