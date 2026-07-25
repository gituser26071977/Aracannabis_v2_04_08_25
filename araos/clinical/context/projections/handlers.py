"""
Clinical Context — Projection Handlers.

Mapeia cada event_type relacionado a ClinicalContext em efeito sobre:
    - clinical_contexts                  (write-side aggregate)
    - clinical_context_relationships     (graph edge)

Eventos consumidos (10):
    CLINICAL_CONTEXT_SUGGESTED              → marca idempotência do Rule Engine
    CLINICAL_CONTEXT_CREATED                → insere ClinicalContextModel
    CLINICAL_CONTEXT_ACTIVATED              → atualiza status
    CLINICAL_CONTEXT_UPDATED                → merge metadados
    CLINICAL_CONTEXT_CLOSED                 → atualiza status + end_date
    CLINICAL_CONTEXT_REOPENED               → status = ACTIVE, incrementa version
    CLINICAL_CONTEXT_LINKED                 → upsert edge
    CLINICAL_CONTEXT_UNLINKED               → remove edge
    CLINICAL_CONTEXT_REJECTED               → status = REJECTED
    CLINICAL_CONTEXT_TYPE_CONFIRMED         → corrige context_type

Idempotência: caller (ClinicalContextProjection.apply) checa `processed_events`
antes de chamar. Aqui, cada handler é determinístico.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from araos.clinical.context.sql import (
    ClinicalContextModel,
    ContextRelationshipModel,
)
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_status import ContextStatus
from araos.clinical.context.domain.context_type import ContextType


logger = logging.getLogger(__name__)


def _ensure_aware(dt):
    if dt is None:
        return None
    if isinstance(dt, str):
        s = dt.replace("Z", "+00:00") if dt.endswith("Z") else dt
        try:
            dt2 = datetime.fromisoformat(s)
        except ValueError:
            return None
        dt = dt2
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _get_status(value):
    if isinstance(value, ContextStatus):
        return value
    try:
        return ContextStatus(value)
    except ValueError:
        return None


# ─── Idempotency marker ────────────────────────────────────────────


def handle_clinical_context_suggested(
    session: Session, event: Dict[str, Any]
) -> None:
    """Marca (tenant, patient, rule, event_id) como processado.

    Idempotência via UniqueConstraint — IntegrityError → skip silencioso.
    """
    from araos.clinical.context.sql import ProcessedRuleEvaluationModel
    import uuid

    payload = event.get("payload") or {}
    rule_id = payload.get("rule_id")
    if not rule_id:
        return
    tenant_id = event.get("tenant_id")
    patient_id = event.get("patient_id") or payload.get("patient_id")
    ev_id = event.get("id") or event.get("event_id")
    suggestion_id = payload.get("suggestion_id") or ev_id or uuid.uuid4().hex

    if not (tenant_id and patient_id and ev_id):
        return

    row = ProcessedRuleEvaluationModel(
        id=uuid.uuid4().hex,
        tenant_id=tenant_id,
        patient_id=patient_id,
        rule_id=rule_id,
        event_id=ev_id,
        suggestion_id=suggestion_id,
        context_id=payload.get("context_id"),
        processed_at=_ensure_aware(event.get("created_at")) or datetime.now(timezone.utc),
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        # Já processado — skip.
        logger.debug(
            "rule_evaluation_already_processed",
            extra={
                "tenant_id": tenant_id, "patient_id": patient_id,
                "rule_id": rule_id, "event_id": ev_id,
            },
        )


# ─── Context lifecycle handlers ────────────────────────────────────


def _coerce_status_value(v, default=None):
    if v is None:
        return default
    try:
        return ContextStatus(v).value
    except (ValueError, KeyError):
        return default


def _coerce_type_value(v, default=None):
    if v is None:
        return default
    try:
        return ContextType(v).value
    except (ValueError, KeyError):
        return default


def _coerce_origin_value(v, default=None):
    if v is None:
        return default
    try:
        return ContextOrigin(v).value
    except (ValueError, KeyError):
        return default


def handle_clinical_context_created(
    session: Session, event: Dict[str, Any]
) -> None:
    """Insere novo ClinicalContext (chamado após transition_to via service)."""
    payload = event.get("payload") or {}
    context_id = payload.get("context_id")
    if not context_id:
        return

    # Se já existe (idempotência), atualiza.
    existing = session.get(ClinicalContextModel, context_id)
    if existing is not None:
        return

    row = ClinicalContextModel(
        context_id=context_id,
        tenant_id=event.get("tenant_id"),
        patient_id=event.get("patient_id") or payload.get("patient_id"),
        context_type=_coerce_type_value(payload.get("context_type"), ContextType.OTHER.value)
        if False
        else _coerce_type_value(
            payload.get("context_type"), ContextType.CLINICAL_EPISODE.value
        ),
        status=_coerce_status_value(
            payload.get("status"), ContextStatus.PLANNED.value
        ),
        origin=_coerce_origin_value(
            payload.get("origin"), ContextOrigin.MANUAL.value
        ),
        title=payload.get("title") or "Sem título",
        description=payload.get("description") or "",
        reason=payload.get("reason") or "",
        observations_json=list(payload.get("observations") or []),
        start_date=_ensure_aware(payload.get("start_date")) or datetime.now(timezone.utc),
        end_date=_ensure_aware(payload.get("end_date")),
        confidence_score=float(payload.get("confidence_score") or 1.0),
        source_event_ids_json=list(payload.get("source_event_ids") or []),
        linked_event_ids_json=list(payload.get("linked_event_ids") or []),
        linked_diagnosis_ids_json=list(payload.get("linked_diagnosis_ids") or []),
        linked_phenotype_ids_json=list(payload.get("linked_phenotype_ids") or []),
        linked_intervention_ids_json=list(payload.get("linked_intervention_ids") or []),
        linked_outcome_ids_json=list(payload.get("linked_outcome_ids") or []),
        linked_assessment_ids_json=list(payload.get("linked_assessment_ids") or []),
        professionals_json=list(payload.get("professionals") or []),
        confirmed_by=payload.get("confirmed_by"),
        confirmed_at=_ensure_aware(payload.get("confirmed_at")),
        rejected_by=payload.get("rejected_by"),
        rejected_at=_ensure_aware(payload.get("rejected_at")),
        suggestion_id=payload.get("suggestion_id"),
        explanation_id=payload.get("explanation_id"),
        created_at=_ensure_aware(event.get("created_at")) or datetime.now(timezone.utc),
        updated_at=None,
        aggregate_version=int(payload.get("aggregate_version") or 1),
        created_by=payload.get("created_by") or event.get("created_by"),
    )
    session.add(row)
    session.flush()


def REDACTED(
    session: Session, event: Dict[str, Any]
) -> None:
    """Handler genérico para Activated/Closed/Reopened/Rejected."""
    payload = event.get("payload") or {}
    context_id = payload.get("context_id")
    if not context_id:
        return
    row = session.get(ClinicalContextModel, context_id)
    if row is None:
        return

    target_status = payload.get("new_status") or payload.get("status")
    if not target_status:
        return
    new_status = _coerce_status_value(target_status)
    if not new_status:
        return

    row.status = new_status
    row.updated_at = _ensure_aware(event.get("created_at")) or datetime.now(timezone.utc)
    row.aggregate_version = int(payload.get("aggregate_version") or row.aggregate_version + 1)

    actor_id = payload.get("actor_id")
    if new_status == ContextStatus.ACTIVE.value and actor_id:
        row.confirmed_by = actor_id
        row.confirmed_at = row.updated_at
    elif new_status == ContextStatus.REJECTED.value and actor_id:
        row.rejected_by = actor_id
        row.rejected_at = row.updated_at

    if new_status in (
        ContextStatus.COMPLETED.value,
        ContextStatus.CANCELLED.value,
        ContextStatus.ARCHIVED.value,
    ):
        end_dt = _ensure_aware(payload.get("end_date")) or row.updated_at
        row.end_date = end_dt

    session.flush()


# Aliased handlers por evento (mesma lógica base acima):

def handle_clinical_context_activated(
    session: Session, event: Dict[str, Any]
) -> None:
    REDACTED(session, event)


def handle_clinical_context_closed(
    session: Session, event: Dict[str, Any]
) -> None:
    REDACTED(session, event)


def handle_clinical_context_reopened(
    session: Session, event: Dict[str, Any]
) -> None:
    REDACTED(session, event)


def handle_clinical_context_rejected(
    session: Session, event: Dict[str, Any]
) -> None:
    REDACTED(session, event)


def handle_clinical_context_updated(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event.get("payload") or {}
    context_id = payload.get("context_id")
    if not context_id:
        return
    row = session.get(ClinicalContextModel, context_id)
    if row is None:
        return

    changed = payload.get("changed_fields") or []
    field_map = {
        "title": "title",
        "description": "description",
        "observations": "observations_json",
        "professionals": "professionals_json",
        "linked_event_ids": "linked_event_ids_json",
        "linked_diagnosis_ids": "linked_diagnosis_ids_json",
        "linked_phenotype_ids": "linked_phenotype_ids_json",
        "linked_intervention_ids": "linked_intervention_ids_json",
        "linked_outcome_ids": "linked_outcome_ids_json",
        "linked_assessment_ids": "linked_assessment_ids_json",
    }
    for change_key, row_field in field_map.items():
        if change_key in payload and change_key in changed:
            setattr(row, row_field, list(payload[change_key]) if row_field.endswith("_json") else payload[change_key])

    row.updated_at = _ensure_aware(event.get("created_at")) or datetime.now(timezone.utc)
    row.aggregate_version = int(payload.get("aggregate_version") or row.aggregate_version + 1)
    actor_id = payload.get("actor_id")
    if actor_id:
        row.updated_by = actor_id
    session.flush()


# ─── Relationship handlers ──────────────────────────────────────────


def handle_clinical_context_linked(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event.get("payload") or {}
    rel_id = payload.get("relationship_id")
    if not rel_id:
        return
    existing = session.get(ContextRelationshipModel, rel_id)
    if existing is not None:
        return
    row = ContextRelationshipModel(
        relationship_id=rel_id,
        tenant_id=event.get("tenant_id"),
        source_context_id=payload.get("source_context_id"),
        target_context_id=payload.get("target_context_id"),
        relationship_type=payload.get("relationship_type") or "related_to",
        confidence=float(payload.get("confidence") or 1.0),
        evidence_event_ids_json=list(payload.get("evidence_event_ids") or []),
        created_at=_ensure_aware(event.get("created_at")) or datetime.now(timezone.utc),
        created_by=payload.get("created_by") or event.get("created_by"),
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()


def handle_clinical_context_unlinked(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event.get("payload") or {}
    rel_id = payload.get("relationship_id")
    if not rel_id:
        return
    row = session.get(ContextRelationshipModel, rel_id)
    if row is None:
        return
    # Tenant isolation check via payload auxiliary field
    payload_tenant = payload.get("tenant_id") or event.get("tenant_id")
    if payload_tenant and row.tenant_id != payload_tenant:
        return
    session.delete(row)
    session.flush()


# ─── Type confirmed ────────────────────────────────────────────────


def REDACTED(
    session: Session, event: Dict[str, Any]
) -> None:
    payload = event.get("payload") or {}
    context_id = payload.get("context_id")
    if not context_id:
        return
    row = session.get(ClinicalContextModel, context_id)
    if row is None:
        return
    new_type = _coerce_type_value(payload.get("confirmed_type"))
    if new_type:
        row.context_type = new_type
    row.updated_at = _ensure_aware(event.get("created_at")) or datetime.now(timezone.utc)
    session.flush()


# ─── Dispatch ───────────────────────────────────────────────────────

HANDLERS_BY_EVENT_TYPE = {
    "CLINICAL_CONTEXT_SUGGESTED": handle_clinical_context_suggested,
    "CLINICAL_CONTEXT_CREATED": handle_clinical_context_created,
    "CLINICAL_CONTEXT_ACTIVATED": handle_clinical_context_activated,
    "CLINICAL_CONTEXT_UPDATED": handle_clinical_context_updated,
    "CLINICAL_CONTEXT_CLOSED": handle_clinical_context_closed,
    "CLINICAL_CONTEXT_REOPENED": handle_clinical_context_reopened,
    "CLINICAL_CONTEXT_LINKED": handle_clinical_context_linked,
    "CLINICAL_CONTEXT_UNLINKED": handle_clinical_context_unlinked,
    "CLINICAL_CONTEXT_REJECTED": handle_clinical_context_rejected,
    "CLINICAL_CONTEXT_TYPE_CONFIRMED": REDACTED,
}
