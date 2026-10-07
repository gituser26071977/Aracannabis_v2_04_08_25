"""Serviço de aplicação da triagem psiquiátrica (reuso por rotas)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from araos.specialties.neurodevelopmental.scales import (
    ScaleNotFoundError,
    ScaleRegistry,
    ScaleResponseStore,
    ScaleRunner,
    ScaleValidationError,
)
from araos.specialties.psychiatry import (
    build_checklist,
    build_narrative,
    evaluate,
    explain,
    load_config,
    parse_config,
    polish_with_llm,
)

logger = logging.getLogger(__name__)

INSTRUMENT_CODE = "PSYCH_TRIAGE"


class TriageError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def apply_triage(
    db_session: Any,
    *,
    tenant_id: str,
    patient_id: str,
    raw_responses: Dict[str, Any],
    applied_by: Optional[str] = None,
    source: str = "ui",
    status: str = "final",
    version: str = "latest",
    metadata: Optional[Dict[str, Any]] = None,
    generate_narrative: bool = True,
    use_llm: bool = False,
) -> Dict[str, Any]:
    if not tenant_id:
        raise TriageError("tenant_required", "tenant_id é obrigatório")
    if not patient_id:
        raise TriageError("patient_required", "patient_id é obrigatório")
    if not isinstance(raw_responses, dict):
        raise TriageError("invalid_responses", "raw_responses deve ser objeto")

    try:
        from araos.specialties.psychiatry import register_instrument

        register_instrument()
        spec = ScaleRegistry.get(INSTRUMENT_CODE, version=version)
    except ScaleNotFoundError as exc:
        raise TriageError("instrument_not_found", str(exc)) from exc

    cfg = parse_config(load_config(spec.version))

    try:
        ScaleRunner(spec).run(raw_responses, metadata=metadata or {}, validate=True)
    except ScaleValidationError as exc:
        raise TriageError("validation_error", str(exc)) from exc
    except ValueError as exc:
        raise TriageError("scoring_error", str(exc)) from exc

    evaluation = evaluate(raw_responses, cfg)
    narrative = ""
    if generate_narrative:
        narrative = build_narrative(evaluation, cfg)
        if use_llm:
            narrative = polish_with_llm(narrative, checklist=build_checklist(evaluation, cfg))

    extras = {
        "psych_triage": {
            "model_version": cfg.version,
            "criteria_version": cfg.criteria_version,
            "updated_at": cfg.updated_at,
            "disclaimer": cfg.disclaimer,
            "risk": evaluation.risk,
            "patterns": evaluation.patterns,
            "contexts": evaluation.contexts,
            "narrative": narrative,
            "explainability": explain(raw_responses, cfg),
            "referenced_at": datetime.now(timezone.utc).isoformat(),
        }
    }
    merged_metadata = {**(metadata or {}), **extras}

    store = ScaleResponseStore(db_session)
    stored = store.save(
        tenant_id=tenant_id,
        patient_id=str(patient_id),
        scale_code=INSTRUMENT_CODE,
        raw_responses=raw_responses,
        applied_by=applied_by,
        source=source,
        status=status,
        metadata=merged_metadata,
        validate=False,
        scale_version=spec.version,
    )

    _publish_event(tenant_id, str(patient_id), stored.id, evaluation.indices, cfg)

    payload = stored.to_dict()
    payload["domain_scores"] = evaluation.indices
    payload["risk"] = evaluation.risk
    payload["patterns"] = evaluation.patterns
    payload["narrative"] = narrative
    payload["disclaimer"] = cfg.disclaimer
    return payload


def _publish_event(tenant_id: str, patient_id: str, response_id: str, indices: Dict[str, Any], cfg) -> None:
    try:
        from services.araos_event_emitter import default_emitter

        default_emitter().emit(
            event_type="PSYCH_TRIAGE_APPLIED",
            patient_id=patient_id,
            tenant_id=tenant_id,
            source_id=response_id,
            payload={
                "instrument_code": INSTRUMENT_CODE,
                "instrument_version": cfg.version,
                "response_id": response_id,
                "domain_scores": indices,
            },
            metadata={"model_version": cfg.version, "criteria_version": cfg.criteria_version},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao emitir PSYCH_TRIAGE_APPLIED: %s", exc)
