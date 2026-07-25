"""
AraOS Neurodevelopmental — Projection Handlers (event → projection reducers).

Cada função aqui recebe um evento (dict) e uma sessão SQLAlchemy,
aplicando o efeito à projection correspondente.

Padrão:
    def handle_<event_type>(session, event) -> None:
        ...

Dispatch em HANDLERS por event_type.

Idempotência:
    Não é responsabilidade dos handlers — caller (registry.apply) checa
    `processed_events` antes de chamar.

Convenção de nomenclatura:
    payload_<field> para campos do payload do evento.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict

from sqlalchemy.orm import Session

from .db_models import (
    NeuroRegistryAssessmentModel,
    NeuroRegistryClinicalIdentityModel,
    NeuroRegistryDiagnosisModel,
    NeuroRegistryInterventionModel,
    NeuroRegistryOutcomeModel,
    NeuroRegistryPhenotypeModel,
)

logger = logging.getLogger(__name__)


def _parse_iso(value: str | None) -> datetime | None:
    """Parse ISO 8601 string → datetime UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None



def event_id(event):
    """Normaliza id do evento (store usa 'id', alguns contextos 'event_id')."""
    return event.get('id') or event.get('event_id', '')


def _ensure_aware(dt: datetime | None) -> datetime | None:
    """Garante datetime timezone-aware (UTC default)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ═══════════════════════════════════════════════════════════════════════
# ClinicalIdentity handlers
# ═══════════════════════════════════════════════════════════════════════

def handle_clinical_identity_created(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    identity = NeuroRegistryClinicalIdentityModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=payload["patient_id"],
        status="active",
        initial_notes=payload.get("initial_notes"),
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )
    session.add(identity)
    logger.debug("Applied CLINICAL_IDENTITY_CREATED for %s", identity.id)


def handle_clinical_identity_archived(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    identity = session.get(NeuroRegistryClinicalIdentityModel, event["aggregate_id"])
    if identity is None:
        logger.warning(
            "CLINICAL_IDENTITY_ARCHIVED for unknown identity %s — skipping",
            event["aggregate_id"],
        )
        return
    identity.status = "archived"
    identity.archived_at = _ensure_aware(
        _parse_iso(event.get("event_datetime"))
    )
    identity.archive_reason = payload.get("reason")
    identity.source_event_ids = identity.source_event_ids + [event_id(event)]
    identity.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Diagnosis handlers
# ═══════════════════════════════════════════════════════════════════════

def _resolve_patient_id_from_event(event: Dict[str, Any]) -> str:
    """Extrai patient_id do evento (campo da coluna, não payload)."""
    return event.get("patient_id", "")


def handle_diagnosis_hypothesised(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    classification_dict = payload.get("classification") or {}
    entries = classification_dict.get("entries") or []
    primary = next((e for e in entries if e.get("is_primary")), entries[0] if entries else None)

    diag = NeuroRegistryDiagnosisModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=_resolve_patient_id_from_event(event),
        identity_id=event["payload"].get("identity_id", ""),
        condition_code=payload["condition_code"],
        state="hypothesis",
        classification=classification_dict,
        primary_code=primary.get("code") if primary else None,
        primary_type=primary.get("type") if primary else None,
        hypothesised_at=_ensure_aware(
            _parse_iso(event.get("event_datetime"))
        ),
        onset_date=payload.get("onset_date"),
        rationale=payload.get("reason"),
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )
    session.add(diag)
    # Increment identity counter
    _increment_identity_counter(session, event, "diagnosis_count", +1)
    logger.debug("Applied DIAGNOSIS_HYPOTHESIZED for %s", diag.id)


def handle_diagnosis_investigating(
    session: Session, event: Dict[str, Any]
) -> None:
    _transition_diagnosis(session, event, new_state="investigating")


def handle_diagnosis_confirmed(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_CONFIRMED for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    diag.state = "confirmed"
    diag.confirmation_evidence = payload.get("confirmation_evidence") or {}
    diag.severity = payload.get("severity")
    diag.confirmed_at = _ensure_aware(_parse_iso(event.get("event_datetime")))
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


def handle_diagnosis_revised(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_REVISED for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    diag.previous_condition_code = diag.condition_code
    diag.condition_code = payload["new_condition_code"]
    diag.state = "revised"
    diag.rationale = payload.get("reason")
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]
    # Update classification if provided
    new_classification = payload.get("new_classification")
    if new_classification:
        diag.classification = new_classification


def handle_diagnosis_in_remission(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_IN_REMISSION for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    diag.state = "in_remission"
    diag.remission_type = payload.get("remission_type")
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


def handle_diagnosis_discarded(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_DISCARDED for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    diag.state = "discarded"
    diag.rationale = payload.get("reason")
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


def REDACTED(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_CLASSIFICATION_ADDED for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    # Append new classification entry
    classification = dict(diag.classification or {})
    entries = list(classification.get("entries") or [])
    new_entry = {
        "type": payload["classification_type"],
        "code": payload["code"],
        "is_primary": payload.get("is_primary", False),
        "added_in_event_id": event_id(event),
    }
    if new_entry["is_primary"]:
        # Demote existing primary
        entries = [{**e, "is_primary": False} for e in entries]
    entries.append(new_entry)
    classification["entries"] = entries
    diag.classification = classification
    # Update primary cache
    primary = next((e for e in entries if e.get("is_primary")), entries[0] if entries else None)
    diag.primary_code = primary.get("code") if primary else None
    diag.primary_type = primary.get("type") if primary else None
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


def REDACTED(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "DIAGNOSIS_CLASSIFICATION_REMOVED for unknown diagnosis %s — skipping",
            event["aggregate_id"],
        )
        return
    classification = dict(diag.classification or {})
    entries = [
        e for e in classification.get("entries") or []
        if not (
            e.get("type") == payload["classification_type"]
            and e.get("code") == payload["code"]
        )
    ]
    classification["entries"] = entries
    diag.classification = classification
    primary = next((e for e in entries if e.get("is_primary")), entries[0] if entries else None)
    diag.primary_code = primary.get("code") if primary else None
    diag.primary_type = primary.get("type") if primary else None
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Phenotype handlers
# ═══════════════════════════════════════════════════════════════════════

def handle_phenotype_observed(session: Session, event: Dict[str, Any]) -> None:
    payload = event["payload"]
    pheno = NeuroRegistryPhenotypeModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=_resolve_patient_id_from_event(event),
        identity_id=event["payload"].get("identity_id", ""),
        phenotype_code=payload["phenotype_code"],
        severity=payload["severity"],
        onset_date=payload.get("onset_date"),
        linked_diagnosis_ids=payload.get("linked_diagnosis_ids") or [],
        context=payload.get("context"),
        observed_by=payload["observed_by"],
        observed_at=_ensure_aware(_parse_iso(event.get("event_datetime"))),
        is_active=True,
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )
    session.add(pheno)
    _increment_identity_counter(session, event, "phenotype_count", +1)
    logger.debug("Applied PHENOTYPE_OBSERVED for %s", pheno.id)


def handle_phenotype_resolved(session: Session, event: Dict[str, Any]) -> None:
    payload = event["payload"]
    pheno = session.get(NeuroRegistryPhenotypeModel, event["aggregate_id"])
    if pheno is None:
        logger.warning(
            "PHENOTYPE_RESOLVED for unknown phenotype %s — skipping",
            event["aggregate_id"],
        )
        return
    pheno.is_active = False
    pheno.resolved_at = _ensure_aware(_parse_iso(event.get("event_datetime")))
    pheno.resolved_by = payload["resolved_by"]
    pheno.resolution_reason = payload.get("reason")
    pheno.source_event_ids = pheno.source_event_ids + [event_id(event)]
    pheno.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Assessment handlers
# ═══════════════════════════════════════════════════════════════════════

def handle_assessment_applied(session: Session, event: Dict[str, Any]) -> None:
    payload = event["payload"]
    assess = NeuroRegistryAssessmentModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=_resolve_patient_id_from_event(event),
        identity_id=event["payload"].get("identity_id", ""),
        scale_code=payload["scale_code"],
        scale_version=payload["scale_version"],
        applied_by=payload["applied_by"],
        applied_at=_ensure_aware(_parse_iso(event.get("event_datetime"))),
        raw_responses=payload.get("raw_responses") or {},
        computed_scores=payload.get("computed_scores") or {},
        interpretation=payload.get("interpretation") or {},
        linked_diagnosis_ids=payload.get("linked_diagnosis_ids") or [],
        status="final",
        version=1,
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )
    session.add(assess)
    _increment_identity_counter(session, event, "assessment_count", +1)
    logger.debug("Applied ASSESSMENT_APPLIED for %s", assess.id)


def handle_assessment_updated(session: Session, event: Dict[str, Any]) -> None:
    payload = event["payload"]
    assess = session.get(NeuroRegistryAssessmentModel, event["aggregate_id"])
    if assess is None:
        logger.warning(
            "ASSESSMENT_UPDATED for unknown assessment %s — skipping",
            event["aggregate_id"],
        )
        return
    assess.previous_version_id = assess.id
    assess.raw_responses = payload.get("raw_responses") or assess.raw_responses
    assess.computed_scores = payload.get("computed_scores") or assess.computed_scores
    if payload.get("interpretation") is not None:
        assess.interpretation = payload["interpretation"]
    assess.status = "amended"
    assess.version = (assess.version or 1) + 1
    assess.applied_by = payload["updated_by"]
    assess.source_event_ids = assess.source_event_ids + [event_id(event)]
    assess.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Intervention handlers
# ═══════════════════════════════════════════════════════════════════════

def handle_intervention_started(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    dose = payload.get("dose")
    interv = NeuroRegistryInterventionModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=_resolve_patient_id_from_event(event),
        identity_id=event["payload"].get("identity_id", ""),
        intervention_type=payload["intervention_type"],
        subtype=payload["subtype"],
        state="started",
        dose=dose,
        indication_condition_code=payload.get("indication_condition_code"),
        linked_diagnosis_ids=payload.get("linked_diagnosis_ids") or [],
        prescriber_id=payload.get("prescriber_id"),
        notes=payload.get("notes"),
        started_by=payload["started_by"],
        start_date=payload["start_date"],
        is_active=True,
        is_paused=False,
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )
    session.add(interv)
    _increment_identity_counter(session, event, "intervention_count", +1)
    logger.debug("Applied INTERVENTION_STARTED for %s", interv.id)


def handle_intervention_adjusted(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    interv = session.get(NeuroRegistryInterventionModel, event["aggregate_id"])
    if interv is None:
        logger.warning(
            "INTERVENTION_ADJUSTED for unknown intervention %s — skipping",
            event["aggregate_id"],
        )
        return
    interv.previous_dose = interv.dose
    interv.dose = payload.get("new_dose")
    interv.state = "adjusted"
    interv.source_event_ids = interv.source_event_ids + [event_id(event)]
    interv.last_sequence = event["sequence"]


def handle_intervention_paused(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    interv = session.get(NeuroRegistryInterventionModel, event["aggregate_id"])
    if interv is None:
        logger.warning(
            "INTERVENTION_PAUSED for unknown intervention %s — skipping",
            event["aggregate_id"],
        )
        return
    interv.state = "paused"
    interv.is_paused = True
    interv.pause_reason = payload.get("reason")
    interv.expected_resume_date = payload.get("expected_resume_date")
    interv.source_event_ids = interv.source_event_ids + [event_id(event)]
    interv.last_sequence = event["sequence"]


def handle_intervention_resumed(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    interv = session.get(NeuroRegistryInterventionModel, event["aggregate_id"])
    if interv is None:
        logger.warning(
            "INTERVENTION_RESUMED for unknown intervention %s — skipping",
            event["aggregate_id"],
        )
        return
    if payload.get("new_dose") is not None:
        interv.previous_dose = interv.dose
        interv.dose = payload["new_dose"]
    interv.state = "resumed"
    interv.is_paused = False
    interv.pause_reason = None
    interv.source_event_ids = interv.source_event_ids + [event_id(event)]
    interv.last_sequence = event["sequence"]


def handle_intervention_stopped(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event["payload"]
    interv = session.get(NeuroRegistryInterventionModel, event["aggregate_id"])
    if interv is None:
        logger.warning(
            "INTERVENTION_STOPPED for unknown intervention %s — skipping",
            event["aggregate_id"],
        )
        return
    interv.state = "stopped"
    interv.is_active = False
    interv.end_date = payload.get("end_date")
    interv.stop_reason = payload.get("reason")
    interv.stop_outcome_summary = payload.get("outcome_summary")
    interv.source_event_ids = interv.source_event_ids + [event_id(event)]
    interv.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Outcome handlers
# ═══════════════════════════════════════════════════════════════════════

def _handle_outcome_base(event: Dict[str, Any]) -> NeuroRegistryOutcomeModel:
    payload = event["payload"]
    return NeuroRegistryOutcomeModel(
        id=event["aggregate_id"],
        tenant_id=event["tenant_id"],
        patient_id=_resolve_patient_id_from_event(event),
        identity_id=event["payload"].get("identity_id", ""),
        outcome_type=event["event_type"].replace("OUTCOME_", "").lower(),
        observed_by=payload["observed_by"],
        observed_at=_ensure_aware(_parse_iso(event.get("event_datetime"))),
        evidence=payload.get("evidence") or {},
        intervention_id=payload.get("intervention_id"),
        magnitude=payload.get("magnitude"),
        severity=payload.get("severity"),
        causality=payload.get("causality"),
        action_taken=payload.get("action_taken"),
        description=payload.get("description"),
        duration_months=payload.get("duration_months"),
        responding_domains=payload.get("responding_domains") or [],
        non_responding_domains=payload.get("non_responding_domains") or [],
        duration_observed_months=payload.get("duration_observed_months"),
        notes=payload.get("notes"),
        source_event_ids=[event_id(event)],
        last_sequence=event["sequence"],
    )


def handle_outcome_improvement(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


def handle_outcome_worsening(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


def handle_outcome_partial_response(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


def handle_outcome_remission(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


def handle_outcome_adverse_event(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


def handle_outcome_no_change(
    session: Session, event: Dict[str, Any]
) -> None:
    outcome = _handle_outcome_base(event)
    session.add(outcome)
    _increment_identity_counter(session, event, "outcome_count", +1)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _increment_identity_counter(
    session: Session, event: Dict[str, Any], field: str, delta: int
) -> None:
    """Incrementa contador no ClinicalIdentity associado."""
    identity_id = event["payload"].get("identity_id", "")
    if not identity_id:
        return
    identity = session.get(NeuroRegistryClinicalIdentityModel, identity_id)
    if identity is None:
        return
    current = getattr(identity, field, 0) or 0
    setattr(identity, field, current + delta)


def _transition_diagnosis(
    session: Session, event: Dict[str, Any], new_state: str
) -> None:
    """Helper genérico para transições de estado do Diagnosis."""
    diag = session.get(NeuroRegistryDiagnosisModel, event["aggregate_id"])
    if diag is None:
        logger.warning(
            "%s for unknown diagnosis %s — skipping",
            event["event_type"], event["aggregate_id"],
        )
        return
    diag.state = new_state
    diag.source_event_ids = diag.source_event_ids + [event_id(event)]
    diag.last_sequence = event["sequence"]


# ═══════════════════════════════════════════════════════════════════════
# Dispatch table
# ═══════════════════════════════════════════════════════════════════════

HANDLERS: Dict[str, Callable[[Session, Dict[str, Any]], None]] = {
    # ClinicalIdentity
    "CLINICAL_IDENTITY_CREATED": handle_clinical_identity_created,
    "CLINICAL_IDENTITY_ARCHIVED": handle_clinical_identity_archived,
    # Diagnosis
    "DIAGNOSIS_HYPOTHESIZED": handle_diagnosis_hypothesised,
    "DIAGNOSIS_INVESTIGATING": handle_diagnosis_investigating,
    "DIAGNOSIS_CONFIRMED": handle_diagnosis_confirmed,
    "DIAGNOSIS_REVISED": handle_diagnosis_revised,
    "DIAGNOSIS_IN_REMISSION": handle_diagnosis_in_remission,
    "DIAGNOSIS_DISCARDED": handle_diagnosis_discarded,
    "DIAGNOSIS_CLASSIFICATION_ADDED": REDACTED,
    "DIAGNOSIS_CLASSIFICATION_REMOVED": REDACTED,
    # Phenotype
    "PHENOTYPE_OBSERVED": handle_phenotype_observed,
    "PHENOTYPE_RESOLVED": handle_phenotype_resolved,
    # Assessment
    "ASSESSMENT_APPLIED": handle_assessment_applied,
    "ASSESSMENT_UPDATED": handle_assessment_updated,
    # Intervention
    "INTERVENTION_STARTED": handle_intervention_started,
    "INTERVENTION_ADJUSTED": handle_intervention_adjusted,
    "INTERVENTION_PAUSED": handle_intervention_paused,
    "INTERVENTION_RESUMED": handle_intervention_resumed,
    "INTERVENTION_STOPPED": handle_intervention_stopped,
    # Outcome
    "OUTCOME_IMPROVEMENT": handle_outcome_improvement,
    "OUTCOME_WORSENING": handle_outcome_worsening,
    "OUTCOME_PARTIAL_RESPONSE": handle_outcome_partial_response,
    "OUTCOME_REMISSION": handle_outcome_remission,
    "OUTCOME_ADVERSE_EVENT": handle_outcome_adverse_event,
    "OUTCOME_NO_CHANGE": handle_outcome_no_change,
}


def get_handler(event_type: str) -> Callable[[Session, Dict[str, Any]], None] | None:
    """Retorna handler registrado para event_type ou None."""
    return HANDLERS.get(event_type)