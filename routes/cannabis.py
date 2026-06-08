"""
ARAOS Cannabis Module API — Week 11D Productization Layer.

RESTful endpoints exposing persistent cannabis clinical data.
"""
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from uuid import UUID

from models import db, Paciente
from araos.platform.api.response import success_response, error_response
from araos.specialties.cannabis.db_models import (
    CannabisProfileModel,
    CannabisTherapeuticGoalModel,
    CannabisProductModel,
    CannabisMedicationModel,
    CannabisDoseEntryModel,
    CannabisOutcomeScoreModel,
    CannabisAlertModel,
)

cannabis_bp = Blueprint("cannabis", __name__)


def _get_tenant_id():
    return getattr(g, "current_association", None) and g.current_association.id


def _require_tenant():
    tid = _get_tenant_id()
    if not tid:
        return error_response("MISSING_TENANT", "X-Association-ID header required", 403)
    return tid


# ═══════════════════════════════════════════════════════════════
# PROFILES
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/profiles", methods=["GET"])
@jwt_required()
def list_profiles():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    q = db.select(CannabisProfileModel).where(CannabisProfileModel.tenant_id == tenant_id)
    total = db.session.execute(db.select(db.func.count()).select_from(q.subquery())).scalar()
    items = db.session.execute(q.order_by(CannabisProfileModel.created_at.desc()).offset((page - 1) * per_page).limit(per_page)).scalars().all()
    return success_response(
        data=[_profile_to_dict(i) for i in items],
        meta={"pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": (total // per_page) + (1 if total % per_page else 0)}},
    )


@cannabis_bp.route("/profiles/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_profile(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil cannabis não encontrado", 404)
    return success_response(data=_profile_to_dict(profile, deep=True))


@cannabis_bp.route("/profiles", methods=["POST"])
@jwt_required()
def create_profile():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return error_response("MISSING_PATIENT_ID", "patient_id é obrigatório", 400)

    existing = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if existing:
        return error_response("PROFILE_EXISTS", "Perfil já existe para este paciente", 409)

    profile = CannabisProfileModel(
        patient_id=patient_id,
        tenant_id=tenant_id,
        primary_condition=body.get("primary_condition"),
        secondary_conditions=body.get("secondary_conditions", []),
        eligibility_status=body.get("eligibility_status", "eligible"),
        eligibility_reason=body.get("eligibility_reason"),
        treatment_status=body.get("treatment_status", "active"),
        notes=body.get("notes"),
        started_at=datetime.utcnow() if body.get("started_at") else None,
    )
    db.session.add(profile)
    db.session.commit()
    return success_response(data=_profile_to_dict(profile), status=201)


@cannabis_bp.route("/profiles/<int:patient_id>", methods=["PUT"])
@jwt_required()
def update_profile(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil não encontrado", 404)
    body = request.get_json(force=True) or {}
    for field in ["primary_condition", "secondary_conditions", "eligibility_status",
                  "eligibility_reason", "treatment_status", "notes", "discontinued_reason"]:
        if field in body:
            setattr(profile, field, body[field])
    if body.get("discontinued_at"):
        profile.discontinued_at = datetime.fromisoformat(body["discontinued_at"])
    db.session.commit()
    return success_response(data=_profile_to_dict(profile))


def _profile_to_dict(profile, deep=False):
    d = {
        "id": str(profile.id),
        "patient_id": profile.patient_id,
        "tenant_id": profile.tenant_id,
        "specialty_code": profile.specialty_code,
        "eligibility_status": profile.eligibility_status,
        "eligibility_reason": profile.eligibility_reason,
        "primary_condition": profile.primary_condition,
        "secondary_conditions": profile.secondary_conditions,
        "treatment_status": profile.treatment_status,
        "started_at": profile.started_at.isoformat() if profile.started_at else None,
        "discontinued_at": profile.discontinued_at.isoformat() if profile.discontinued_at else None,
        "notes": profile.notes,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }
    if deep:
        d["goals"] = [_goal_to_dict(g) for g in profile.goals]
        d["medications"] = [_medication_to_dict(m) for m in profile.medications]
        d["dose_entries"] = [_dose_to_dict(de) for de in profile.dose_entries]
        d["outcome_scores"] = [_outcome_to_dict(o) for o in profile.outcome_scores]
        d["alerts"] = [_alert_to_dict(a) for a in profile.alerts]
    return d


# ═══════════════════════════════════════════════════════════════
# THERAPEUTIC GOALS
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/profiles/<int:patient_id>/goals", methods=["POST"])
@jwt_required()
def create_goal(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil não encontrado", 404)
    body = request.get_json(force=True) or {}
    goal = CannabisTherapeuticGoalModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        description=body.get("description", ""),
        target_symptom=body.get("target_symptom", ""),
        target_metric=body.get("target_metric"),
        baseline_score=body.get("baseline_score", 0.0),
        target_score=body.get("target_score", 0.0),
        current_score=body.get("current_score", 0.0),
    )
    db.session.add(goal)
    db.session.commit()
    return success_response(data=_goal_to_dict(goal), status=201)


def _goal_to_dict(goal):
    return {
        "id": str(goal.id),
        "profile_id": str(goal.profile_id),
        "description": goal.description,
        "target_symptom": goal.target_symptom,
        "target_metric": goal.target_metric,
        "baseline_score": goal.baseline_score,
        "target_score": goal.target_score,
        "current_score": goal.current_score,
        "achieved": goal.achieved,
        "achieved_at": goal.achieved_at.isoformat() if goal.achieved_at else None,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# PRODUCTS
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/products", methods=["GET"])
@jwt_required()
def list_products():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    items = db.session.execute(
        db.select(CannabisProductModel).where(
            CannabisProductModel.tenant_id == tenant_id,
            CannabisProductModel.active == True,
        ).order_by(CannabisProductModel.name)
    ).scalars().all()
    return success_response(data=[_product_to_dict(i) for i in items])


@cannabis_bp.route("/products", methods=["POST"])
@jwt_required()
def create_product():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    product = CannabisProductModel(
        tenant_id=tenant_id,
        name=body.get("name", ""),
        manufacturer=body.get("manufacturer"),
        formulation=body.get("formulation"),
        spectrum=body.get("spectrum"),
        cbd_mg=body.get("cbd_mg", 0.0),
        thc_mg=body.get("thc_mg", 0.0),
        cbg_mg=body.get("cbg_mg", 0.0),
        cbn_mg=body.get("cbn_mg", 0.0),
        volume_ml=body.get("volume_ml"),
        route=body.get("route"),
        batch_number=body.get("batch_number"),
    )
    db.session.add(product)
    db.session.commit()
    return success_response(data=_product_to_dict(product), status=201)


@cannabis_bp.route("/products/<product_id>", methods=["PUT"])
@jwt_required()
def update_product(product_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    product = db.session.execute(
        db.select(CannabisProductModel).where(
            CannabisProductModel.id == UUID(product_id),
            CannabisProductModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not product:
        return error_response("PRODUCT_NOT_FOUND", "Produto não encontrado", 404)
    body = request.get_json(force=True) or {}
    for field in ["name", "manufacturer", "formulation", "spectrum", "cbd_mg", "thc_mg",
                  "cbg_mg", "cbn_mg", "volume_ml", "route", "batch_number", "active"]:
        if field in body:
            setattr(product, field, body[field])
    db.session.commit()
    return success_response(data=_product_to_dict(product))


def _product_to_dict(product):
    return {
        "id": str(product.id),
        "name": product.name,
        "manufacturer": product.manufacturer,
        "formulation": product.formulation,
        "spectrum": product.spectrum,
        "cbd_mg": product.cbd_mg,
        "thc_mg": product.thc_mg,
        "cbg_mg": product.cbg_mg,
        "cbn_mg": product.cbn_mg,
        "volume_ml": product.volume_ml,
        "route": product.route,
        "batch_number": product.batch_number,
        "active": product.active,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# MEDICATIONS (Prescriptions)
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/profiles/<int:patient_id>/medications", methods=["POST"])
@jwt_required()
def create_medication(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil não encontrado", 404)
    body = request.get_json(force=True) or {}
    med = CannabisMedicationModel(
        profile_id=profile.id,
        patient_id=patient_id,
        tenant_id=tenant_id,
        product_id=body.get("product_id") and UUID(body["product_id"]),
        prescribed_dose_mg=body.get("prescribed_dose_mg"),
        frequency=body.get("frequency"),
        instructions=body.get("instructions"),
        prescribed_by=int(get_jwt_identity()),
        started_at=datetime.utcnow(),
    )
    db.session.add(med)
    db.session.commit()
    return success_response(data=_medication_to_dict(med), status=201)


def _medication_to_dict(med):
    return {
        "id": str(med.id),
        "patient_id": med.patient_id,
        "product_id": str(med.product_id) if med.product_id else None,
        "product": _product_to_dict(med.product) if med.product else None,
        "prescribed_dose_mg": med.prescribed_dose_mg,
        "frequency": med.frequency,
        "status": med.status,
        "instructions": med.instructions,
        "prescribed_at": med.prescribed_at.isoformat() if med.prescribed_at else None,
        "started_at": med.started_at.isoformat() if med.started_at else None,
        "stopped_at": med.stopped_at.isoformat() if med.stopped_at else None,
        "stopped_reason": med.stopped_reason,
    }


# ═══════════════════════════════════════════════════════════════
# DOSE ENTRIES
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/doses/<int:patient_id>", methods=["GET"])
@jwt_required()
def list_doses(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    items = db.session.execute(
        db.select(CannabisDoseEntryModel).where(
            CannabisDoseEntryModel.patient_id == patient_id,
            CannabisDoseEntryModel.tenant_id == tenant_id,
        ).order_by(CannabisDoseEntryModel.entry_date.desc())
    ).scalars().all()
    return success_response(data=[_dose_to_dict(i) for i in items])


@cannabis_bp.route("/doses", methods=["POST"])
@jwt_required()
def create_dose():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return error_response("MISSING_PATIENT_ID", "patient_id é obrigatório", 400)
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil cannabis não encontrado para este paciente", 404)
    dose = CannabisDoseEntryModel(
        profile_id=profile.id,
        patient_id=patient_id,
        tenant_id=tenant_id,
        medication_id=body.get("medication_id") and UUID(body["medication_id"]),
        dose_mg=body.get("dose_mg"),
        thc_mg=body.get("thc_mg"),
        cbd_mg=body.get("cbd_mg"),
        entry_type=body.get("entry_type", "administered"),
        reason=body.get("reason"),
        physician_id=int(get_jwt_identity()),
        entry_date=datetime.utcnow(),
    )
    db.session.add(dose)
    db.session.commit()
    return success_response(data=_dose_to_dict(dose), status=201)


def _dose_to_dict(dose):
    return {
        "id": str(dose.id),
        "patient_id": dose.patient_id,
        "medication_id": str(dose.medication_id) if dose.medication_id else None,
        "dose_mg": dose.dose_mg,
        "thc_mg": dose.thc_mg,
        "cbd_mg": dose.cbd_mg,
        "entry_type": dose.entry_type,
        "reason": dose.reason,
        "entry_date": dose.entry_date.isoformat() if dose.entry_date else None,
        "created_at": dose.created_at.isoformat() if dose.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# OUTCOME SCORES
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/outcomes/<int:patient_id>", methods=["GET"])
@jwt_required()
def list_outcomes(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    metric = request.args.get("metric")
    q = db.select(CannabisOutcomeScoreModel).where(
        CannabisOutcomeScoreModel.patient_id == patient_id,
        CannabisOutcomeScoreModel.tenant_id == tenant_id,
    )
    if metric:
        q = q.where(CannabisOutcomeScoreModel.metric_name == metric)
    items = db.session.execute(q.order_by(CannabisOutcomeScoreModel.recorded_at.desc())).scalars().all()
    return success_response(data=[_outcome_to_dict(i) for i in items])


@cannabis_bp.route("/outcomes", methods=["POST"])
@jwt_required()
def create_outcome():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return error_response("MISSING_PATIENT_ID", "patient_id é obrigatório", 400)
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not profile:
        return error_response("PROFILE_NOT_FOUND", "Perfil cannabis não encontrado para este paciente", 404)
    outcome = CannabisOutcomeScoreModel(
        profile_id=profile.id,
        patient_id=patient_id,
        tenant_id=tenant_id,
        metric_name=body.get("metric_name", ""),
        score=body.get("score", 0.0),
        max_score=body.get("max_score", 10.0),
        unit=body.get("unit"),
        context=body.get("context"),
        recorded_at=datetime.utcnow(),
    )
    db.session.add(outcome)
    db.session.commit()
    return success_response(data=_outcome_to_dict(outcome), status=201)


def _outcome_to_dict(outcome):
    return {
        "id": str(outcome.id),
        "patient_id": outcome.patient_id,
        "metric_name": outcome.metric_name,
        "score": outcome.score,
        "max_score": outcome.max_score,
        "unit": outcome.unit,
        "context": outcome.context,
        "recorded_at": outcome.recorded_at.isoformat() if outcome.recorded_at else None,
        "created_at": outcome.created_at.isoformat() if outcome.created_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════

@cannabis_bp.route("/alerts", methods=["GET"])
@jwt_required()
def list_alerts():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient_id = request.args.get("patient_id", type=int)
    status_filter = request.args.get("status")
    severity = request.args.get("severity")
    q = db.select(CannabisAlertModel).where(CannabisAlertModel.tenant_id == tenant_id)
    if patient_id:
        q = q.where(CannabisAlertModel.patient_id == patient_id)
    if status_filter:
        q = q.where(CannabisAlertModel.status == status_filter)
    if severity:
        q = q.where(CannabisAlertModel.severity == severity)
    items = db.session.execute(q.order_by(CannabisAlertModel.triggered_at.desc())).scalars().all()
    return success_response(data=[_alert_to_dict(i) for i in items])


@cannabis_bp.route("/alerts/<alert_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_alert(alert_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    alert = db.session.execute(
        db.select(CannabisAlertModel).where(
            CannabisAlertModel.id == UUID(alert_id),
            CannabisAlertModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not alert:
        return error_response("ALERT_NOT_FOUND", "Alerta não encontrado", 404)
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = int(get_jwt_identity())
    db.session.commit()
    return success_response(data=_alert_to_dict(alert))


def _alert_to_dict(alert):
    return {
        "id": str(alert.id),
        "patient_id": alert.patient_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "status": alert.status,
        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "escalation_level": alert.escalation_level,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }
