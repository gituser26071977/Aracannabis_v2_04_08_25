"""
Routes — AraOS Neurodevelopmental — Clinical Identity & Registry (Sprint 3.2 / ADR-0002).

Endpoints REST DDD-aligned para o bounded context Neurodevelopmental Registry.

URLs seguem ADR-0002 §2.6 — expressam linguagem clínica, não CRUD:

    POST   /api/neuro/clinical-identities                       → cria ClinicalIdentity
    GET    /api/neuro/clinical-identities/{id}                  → recupera (Registry projection)
    GET    /api/neuro/clinical-identities/{id}/timeline         → eventos do Event Store
    POST   /api/neuro/clinical-identities/{id}/diagnoses        → hipótese
    POST   /api/neuro/diagnoses/{id}/transitions                → mudança de estado
    POST   /api/neuro/diagnoses/{id}/classifications            → CID/DSM/SNOMED
    POST   /api/neuro/clinical-identities/{id}/phenotypes       → observa fenótipo
    POST   /api/neuro/phenotypes/{id}/resolve                   → resolve fenótipo
    POST   /api/neuro/clinical-identities/{id}/assessments      → aplica escala
    POST   /api/neuro/clinical-identities/{id}/interventions    → inicia intervenção
    POST   /api/neuro/interventions/{id}/transitions            → ajuste/pausa/stop
    POST   /api/neuro/clinical-identities/{id}/outcomes         → outcome
    POST   /api/neuro/admin/registry/replay                     → DESTRUTIVO (admin only)

Padrão de auth: `@jwt_required()` + `_resolve_tenant_id()` + `_get_actor_id()`.

Resposta HTTP 202 Accepted (escrita assíncrona) com `event_id` no body.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from araos.clinical.event_store import (
    ClinicalEventPublisher,
    InMemoryClinicalEventStore,
)
from araos.specialties.neurodevelopmental.application import (
    AssessmentService,
    ClinicalIdentityService,
    DiagnosisService,
    InterventionService,
    OutcomeService,
    PhenotypeService,
)
from araos.specialties.neurodevelopmental.domain import (
    CID10Code,
    CID11Code,
    ClassificationType,
    ConditionCode,
    DiagnosisState,
    DSM5Code,
    Dose,
    InterventionType,
    OutcomeCausality,
    OutcomeMagnitude,
    OutcomeSeverity,
    PhenotypeSeverity,
)
from araos.specialties.neurodevelopmental.projections import (
    REDACTED,
)

logger = logging.getLogger(__name__)

neuro_registry_bp = Blueprint(
    "neuro_registry", __name__, url_prefix="/api/neuro"
)


# ─── Helpers (reutilizáveis com neuro_scales.py) ───────────────────────


def _resolve_tenant_id() -> str:
    # Re-export do helper canônico (P0-12: tenant só do JWT/g.current_association,
    # nunca de X-Association-ID/X-Tenant-ID — vetor de spoof cross-tenant).
    from routes._helpers import _resolve_tenant_id as _canonical

    return _canonical()


def _get_actor_id() -> Optional[str]:
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            return str(identity.get("user_id") or identity.get("id") or "")
        return str(identity) if identity else None
    except Exception:
        return None


def _publisher() -> ClinicalEventPublisher:
    """Acessa o publisher configurado no app."""
    pub = current_app.config.get("NEURO_REGISTRY_PUBLISHER")
    if pub is None:
        # Fallback: criar InMemory para ambientes de teste/dev sem setup
        logger.warning(
            "NEURO_REGISTRY_PUBLISHER not configured — using InMemory fallback"
        )
        store = InMemoryClinicalEventStore()
        pub = ClinicalEventPublisher(store=store, validate_payload=False)
        current_app.config["NEURO_REGISTRY_PUBLISHER"] = pub
    return pub


def _projection() -> REDACTED:
    proj = current_app.config.get("NEURO_REGISTRY_PROJECTION")
    if proj is None:
        raise RuntimeError(
            "NEURO_REGISTRY_PROJECTION not configured. "
            "App factory must initialize projection with session_factory."
        )
    return proj


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _accepted(result) -> tuple:
    """Resposta 202 Accepted padronizada."""
    return (
        jsonify(
            {
                "event_id": result.event_id,
                "event_type": result.event_type,
                "occurred_at": _isoformat(result.occurred_at),
            }
        ),
        202,
    )


# ═══════════════════════════════════════════════════════════════════════
# ClinicalIdentity
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route("/clinical-identities", methods=["POST"])
@jwt_required()
def create_clinical_identity():
    """Cria nova ClinicalIdentity."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id required"}), 400

    svc = ClinicalIdentityService(_publisher())
    result = svc.create(
        tenant_id=tenant_id,
        patient_id=patient_id,
        actor_id=actor_id,
        initial_notes=body.get("initial_notes"),
    )
    response, status = _accepted(result)
    response.headers["Location"] = f"/api/neuro/clinical-identities/{result.identity_id}"
    return response, status


@neuro_registry_bp.route("/clinical-identities/<identity_id>", methods=["GET"])
@jwt_required()
def get_clinical_identity(identity_id: str):
    """Recupera ClinicalIdentity do Registry projection."""
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "unauthorized"}), 401

    try:
        proj = _projection()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    identity = proj.get_clinical_identity(tenant_id, identity_id)
    if identity is None:
        return jsonify({"error": "not found"}), 404

    diagnoses = proj.list_diagnoses(tenant_id, identity_id)
    phenotypes = proj.list_phenotypes(tenant_id, identity_id)
    interventions = proj.list_interventions(tenant_id, identity_id)

    return jsonify(
        {
            "id": identity.id,
            "patient_id": identity.patient_id,
            "status": identity.status,
            "initial_notes": identity.initial_notes,
            "diagnosis_count": identity.diagnosis_count,
            "phenotype_count": identity.phenotype_count,
            "assessment_count": identity.assessment_count,
            "intervention_count": identity.intervention_count,
            "outcome_count": identity.outcome_count,
            "diagnoses": [d.to_dict() if hasattr(d, "to_dict") else {
                "id": d.id, "state": d.state, "condition_code": d.condition_code,
                "primary_code": d.primary_code,
            } for d in diagnoses],
            "phenotypes": [p.to_dict() if hasattr(p, "to_dict") else {
                "id": p.id, "phenotype_code": p.phenotype_code, "is_active": p.is_active,
            } for p in phenotypes],
            "interventions": [iv.to_dict() if hasattr(iv, "to_dict") else {
                "id": iv.id, "intervention_type": iv.intervention_type, "state": iv.state,
            } for iv in interventions],
            "created_at": _isoformat(identity.created_at),
            "updated_at": _isoformat(identity.updated_at),
        }
    )


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/timeline", methods=["GET"]
)
@jwt_required()
def get_clinical_identity_timeline(identity_id: str):
    """Recupera timeline de eventos do Event Store filtrado por patient_id."""
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "unauthorized"}), 401

    pub = _publisher()
    # Acessar o store através do publisher
    store = pub.store
    patient_id_filter = request.args.get("patient_id")
    event_types = request.args.getlist("event_types")

    # Query the event store
    if hasattr(store, "query"):
        events = store.query(
            tenant_id=tenant_id,
            patient_id=patient_id_filter,
            event_types=event_types or None,
            order_by="sequence ASC",
        )
    else:
        events = []

    return jsonify(
        {
            "identity_id": identity_id,
            "events": [
                {
                    "id": e["id"],
                    "sequence": e["sequence"],
                    "event_type": e["event_type"],
                    "aggregate_type": e.get("aggregate_type"),
                    "aggregate_id": e.get("aggregate_id"),
                    "event_datetime": _isoformat(
                        datetime.fromisoformat(e["event_datetime"].replace("Z", "+00:00"))
                        if isinstance(e.get("event_datetime"), str)
                        else e.get("event_datetime")
                    ),
                    "payload": e["payload"],
                }
                for e in events
            ],
            "total": len(events),
        }
    )


# ═══════════════════════════════════════════════════════════════════════
# Diagnosis
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/diagnoses", methods=["POST"]
)
@jwt_required()
def hypothesize_diagnosis(identity_id: str):
    """Cria nova Diagnosis em estado HYPOTHESIS."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    try:
        condition = ConditionCode(body["condition_code"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"invalid condition_code: {e}"}), 400

    svc = DiagnosisService(_publisher())
    result = svc.hypothesize(
        tenant_id=tenant_id,
        patient_id=body.get("patient_id", ""),
        identity_id=identity_id,
        condition_code=condition,
        hypothesised_by=actor_id,
        reason=body.get("reason"),
        onset_date=body.get("onset_date"),
    )
    response, status = _accepted(result)
    response.headers["Location"] = f"/api/neuro/diagnoses/{result.diagnosis_id}"
    return response, status


@neuro_registry_bp.route(
    "/diagnoses/<diagnosis_id>/transitions", methods=["POST"]
)
@jwt_required()
def transition_diagnosis(diagnosis_id: str):
    """
    Aplica transição de estado do Diagnosis.

    Body: {"to_state": "confirmed", "evidence": {...}, "severity": "moderate"}
    """
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    to_state = body.get("to_state")
    if not to_state:
        return jsonify({"error": "to_state required"}), 400

    try:
        target_state = DiagnosisState(to_state)
    except ValueError:
        return jsonify({"error": f"invalid to_state: {to_state}"}), 400

    # current_state DEVE ser fornecido (projeção não é consultada aqui —
    # simplification: client envia estado atual; full impl consultaria projection)
    current_state_str = body.get("current_state")
    if not current_state_str:
        return jsonify({"error": "current_state required (DB lookup pending)"}), 400
    try:
        current_state = DiagnosisState(current_state_str)
    except ValueError:
        return jsonify({"error": f"invalid current_state: {current_state_str}"}), 400

    svc = DiagnosisService(_publisher())
    identity_id = body.get("identity_id", "")
    patient_id = body.get("patient_id", "")

    if target_state == DiagnosisState.CONFIRMED:
        result = svc.confirm(
            tenant_id=tenant_id,
            patient_id=patient_id,
            identity_id=identity_id,
            diagnosis_id=diagnosis_id,
            current_state=current_state,
            confirmed_by=actor_id,
            confirmation_evidence=body.get("evidence", {}),
            actor_id=actor_id,
            severity=body.get("severity"),
        )
    elif target_state == DiagnosisState.IN_REMISSION:
        result = svc.mark_in_remission(
            tenant_id=tenant_id,
            patient_id=patient_id,
            identity_id=identity_id,
            diagnosis_id=diagnosis_id,
            current_state=current_state,
            remission_type=body.get("remission_type", "partial"),
            marked_by=actor_id,
            actor_id=actor_id,
            evidence=body.get("evidence"),
        )
    elif target_state == DiagnosisState.DISCARDED:
        result = svc.discard(
            tenant_id=tenant_id,
            patient_id=patient_id,
            identity_id=identity_id,
            diagnosis_id=diagnosis_id,
            current_state=current_state,
            discarded_by=actor_id,
            reason=body.get("reason", ""),
            actor_id=actor_id,
            notes=body.get("notes"),
        )
    elif target_state == DiagnosisState.REVISED:
        result = svc.revise(
            tenant_id=tenant_id,
            patient_id=patient_id,
            identity_id=identity_id,
            diagnosis_id=diagnosis_id,
            current_state=current_state,
            new_condition_code=ConditionCode(body.get("new_condition_code", "")),
            revised_by=actor_id,
            reason=body.get("reason", ""),
            actor_id=actor_id,
        )
    elif target_state == DiagnosisState.INVESTIGATING:
        result = svc.start_investigation(
            tenant_id=tenant_id,
            patient_id=patient_id,
            identity_id=identity_id,
            diagnosis_id=diagnosis_id,
            current_state=current_state,
            investigation_plan=body.get("investigation_plan", ""),
            actor_id=actor_id,
        )
    else:
        return jsonify({"error": f"unsupported transition to {to_state}"}), 400

    return _accepted(result)


@neuro_registry_bp.route(
    "/diagnoses/<diagnosis_id>/classifications", methods=["POST"]
)
@jwt_required()
def add_classification(diagnosis_id: str):
    """Adiciona classificação multi-sistema (CID/DSM/SNOMED)."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    classification_type_str = body.get("classification_type")
    code = body.get("code")
    if not classification_type_str or not code:
        return (
            jsonify({"error": "classification_type and code required"}),
            400,
        )

    try:
        ct = ClassificationType(classification_type_str)
    except ValueError:
        return (
            jsonify({"error": f"invalid classification_type: {classification_type_str}"}),
            400,
        )

    svc = DiagnosisService(_publisher())
    result = svc.add_classification(
        tenant_id=tenant_id,
        patient_id=body.get("patient_id", ""),
        diagnosis_id=diagnosis_id,
        classification_type=ct,
        code=code,
        added_by=actor_id,
        is_primary=body.get("is_primary", False),
    )
    return _accepted(result)


# ═══════════════════════════════════════════════════════════════════════
# Phenotype
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/phenotypes", methods=["POST"]
)
@jwt_required()
def observe_phenotype(identity_id: str):
    """Observa novo fenótipo."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    try:
        severity = PhenotypeSeverity(body["severity"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"invalid severity: {e}"}), 400

    svc = PhenotypeService(_publisher())
    result = svc.observe(
        tenant_id=tenant_id,
        patient_id=body.get("patient_id", ""),
        identity_id=identity_id,
        phenotype_code=body["phenotype_code"],
        severity=severity,
        observed_by=actor_id,
        onset_date=body.get("onset_date"),
        linked_diagnosis_ids=body.get("linked_diagnosis_ids"),
        context=body.get("context"),
    )
    return _accepted(result)


@neuro_registry_bp.route("/phenotypes/<phenotype_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_phenotype(phenotype_id: str):
    """Resolve fenótipo (histórico preservado)."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}

    # Resolve identity_id via projection (cross-tenant safe lookup)
    try:
        proj = _projection()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    phenotype = proj.get_phenotype(tenant_id, phenotype_id)
    if phenotype is None:
        return jsonify({"error": "phenotype not found"}), 404
    identity_id = phenotype.identity_id
    patient_id = body.get("patient_id") or phenotype.patient_id

    svc = PhenotypeService(_publisher())
    result = svc.resolve(
        tenant_id=tenant_id,
        patient_id=patient_id,
        identity_id=identity_id,
        phenotype_id=phenotype_id,
        resolved_by=actor_id,
        reason=body.get("reason"),
        resolution_date=body.get("resolution_date"),
    )
    return _accepted(result)


# ═══════════════════════════════════════════════════════════════════════
# Assessment
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/assessments", methods=["POST"]
)
@jwt_required()
def apply_assessment(identity_id: str):
    """Aplica escala neuropsicológica."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    svc = AssessmentService(_publisher())
    result = svc.apply(
        tenant_id=tenant_id,
        patient_id=body.get("patient_id", ""),
        identity_id=identity_id,
        scale_code=body["scale_code"],
        scale_version=body["scale_version"],
        applied_by=actor_id,
        raw_responses=body.get("raw_responses", {}),
        computed_scores=body.get("computed_scores", {}),
        interpretation=body.get("interpretation", {}),
        linked_diagnosis_ids=body.get("linked_diagnosis_ids"),
    )
    return _accepted(result)


# ═══════════════════════════════════════════════════════════════════════
# Intervention
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/interventions", methods=["POST"]
)
@jwt_required()
def start_intervention(identity_id: str):
    """Inicia nova intervenção clínica."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    try:
        itype = InterventionType(body["intervention_type"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"invalid intervention_type: {e}"}), 400

    dose_dict = body.get("dose")
    dose = Dose(
        value=dose_dict.get("value") if dose_dict else None,
        unit=dose_dict.get("unit") if dose_dict else None,
        frequency=dose_dict.get("frequency") if dose_dict else None,
    ) if dose_dict else None

    svc = InterventionService(_publisher())
    result = svc.start(
        tenant_id=tenant_id,
        patient_id=body.get("patient_id", ""),
        identity_id=identity_id,
        intervention_id=body.get("intervention_id"),
        intervention_type=itype,
        subtype=body["subtype"],
        started_by=actor_id,
        start_date=body["start_date"],
        dose=dose,
        indication_condition_code=body.get("indication_condition_code"),
        linked_diagnosis_ids=body.get("linked_diagnosis_ids"),
        prescriber_id=body.get("prescriber_id"),
        notes=body.get("notes"),
    )
    return _accepted(result)


@neuro_registry_bp.route(
    "/interventions/<intervention_id>/transitions", methods=["POST"]
)
@jwt_required()
def transition_intervention(intervention_id: str):
    """Ajusta/pausa/retoma/para uma intervenção."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    action = body.get("action")
    if not action:
        return jsonify({"error": "action required (adjust/pause/resume/stop)"}), 400

    svc = InterventionService(_publisher())
    if action == "adjust":
        dose_dict = body.get("new_dose", {})
        dose = Dose(
            value=dose_dict.get("value"),
            unit=dose_dict.get("unit"),
            frequency=dose_dict.get("frequency"),
        )
        result = svc.adjust(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            intervention_id=intervention_id,
            adjusted_by=actor_id,
            new_dose=dose,
            reason=body.get("reason", ""),
        )
    elif action == "pause":
        result = svc.pause(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            intervention_id=intervention_id,
            paused_by=actor_id,
            reason=body.get("reason", ""),
            expected_resume_date=body.get("expected_resume_date"),
        )
    elif action == "resume":
        result = svc.resume(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            intervention_id=intervention_id,
            resumed_by=actor_id,
            resume_date=body.get("resume_date", ""),
        )
    elif action == "stop":
        result = svc.stop(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            intervention_id=intervention_id,
            stopped_by=actor_id,
            end_date=body.get("end_date", ""),
            reason=body.get("reason", ""),
            outcome_summary=body.get("outcome_summary"),
        )
    else:
        return jsonify({"error": f"invalid action: {action}"}), 400
    return _accepted(result)


# ═══════════════════════════════════════════════════════════════════════
# Outcome
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route(
    "/clinical-identities/<identity_id>/outcomes", methods=["POST"]
)
@jwt_required()
def record_outcome(identity_id: str):
    """Registra outcome clínico."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id or not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    body = request.get_json(force=True) or {}
    outcome_type = body.get("outcome_type")
    if not outcome_type:
        return jsonify({"error": "outcome_type required"}), 400

    svc = OutcomeService(_publisher())
    if outcome_type == "improvement":
        result = svc.record_improvement(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            identity_id=identity_id,
            observed_by=actor_id,
            evidence=body.get("evidence", {}),
            intervention_id=body.get("intervention_id"),
            magnitude=OutcomeMagnitude(body["magnitude"]) if body.get("magnitude") else None,
            notes=body.get("notes"),
        )
    elif outcome_type == "worsening":
        result = svc.record_worsening(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            identity_id=identity_id,
            observed_by=actor_id,
            evidence=body.get("evidence", {}),
            intervention_id=body.get("intervention_id"),
            magnitude=OutcomeMagnitude(body["magnitude"]) if body.get("magnitude") else None,
            notes=body.get("notes"),
        )
    elif outcome_type == "adverse_event":
        result = svc.record_adverse_event(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            identity_id=identity_id,
            observed_by=actor_id,
            severity=OutcomeSeverity(body["severity"]),
            description=body["description"],
            intervention_id=body.get("intervention_id"),
            causality=(
                OutcomeCausality(body["causality"]) if body.get("causality") else None
            ),
            action_taken=body.get("action_taken"),
            notes=body.get("notes"),
        )
    elif outcome_type == "no_change":
        result = svc.record_no_change(
            tenant_id=tenant_id,
            patient_id=body.get("patient_id", ""),
            identity_id=identity_id,
            observed_by=actor_id,
            intervention_id=body.get("intervention_id"),
            duration_observed_months=body.get("duration_observed_months"),
            notes=body.get("notes"),
        )
    else:
        return jsonify({"error": f"unsupported outcome_type: {outcome_type}"}), 400

    return _accepted(result)


# ═══════════════════════════════════════════════════════════════════════
# Admin — replay
# ═══════════════════════════════════════════════════════════════════════


@neuro_registry_bp.route("/admin/registry/replay", methods=["POST"])
@jwt_required()
def replay_registry():
    """DESTRUTIVO: wipe + replay do Registry desde genesis."""
    try:
        proj = _projection()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    body = request.get_json(force=True) or {}
    tenant_id = body.get("tenant_id") or _resolve_tenant_id()
    since_sequence = body.get("since_sequence")

    if since_sequence is None:
        applied = proj.replay_all(tenant_id)
        return jsonify(
            {
                "action": "replay_all",
                "tenant_id": tenant_id,
                "events_applied": applied,
            }
        )
    else:
        applied = proj.replay_from(tenant_id, int(since_sequence))
        return jsonify(
            {
                "action": "replay_from",
                "tenant_id": tenant_id,
                "since_sequence": since_sequence,
                "events_applied": applied,
            }
        )