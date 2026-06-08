"""
AraOS Follow-up Engine API — Week 11D Productization Layer.
"""
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from uuid import UUID

from models import db
from araos.platform.api.response import success_response, error_response
from araos.followup.db_models import (
    FollowupProgramModel,
    FollowupPhaseModel,
    FollowupCheckpointModel,
    FollowupQuestionnaireModel,
    FollowupQuestionModel,
    FollowupResponseModel,
    FollowupAlertModel,
    FollowupEscalationModel,
)

followup_bp = Blueprint("followup", __name__)


def _get_tenant_id():
    return getattr(g, "current_association", None) and g.current_association.id


def _require_tenant():
    tid = _get_tenant_id()
    if not tid:
        return error_response("MISSING_TENANT", "X-Association-ID header required", 403)
    return tid


# ═══════════════════════════════════════════════════════════════
# PROGRAMS
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/programs", methods=["GET"])
@jwt_required()
def list_programs():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient_id = request.args.get("patient_id", type=int)
    q = db.select(FollowupProgramModel).where(FollowupProgramModel.tenant_id == tenant_id)
    if patient_id:
        q = q.where(FollowupProgramModel.patient_id == patient_id)
    items = db.session.execute(q.order_by(FollowupProgramModel.created_at.desc())).scalars().all()
    return success_response(data=[_program_to_dict(i) for i in items])


@followup_bp.route("/programs", methods=["POST"])
@jwt_required()
def create_program():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return error_response("MISSING_PATIENT_ID", "patient_id é obrigatório", 400)
    program = FollowupProgramModel(
        tenant_id=tenant_id,
        patient_id=patient_id,
        name=body.get("name", ""),
        specialty_code=body.get("specialty_code", "cannabis"),
        status=body.get("status", "active"),
        current_phase=body.get("current_phase"),
        metadata_json=body.get("metadata", {}),
    )
    db.session.add(program)
    db.session.commit()
    return success_response(data=_program_to_dict(program), status=201)


@followup_bp.route("/programs/<program_id>", methods=["GET"])
@jwt_required()
def get_program(program_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    program = db.session.execute(
        db.select(FollowupProgramModel).where(
            FollowupProgramModel.id == UUID(program_id),
            FollowupProgramModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not program:
        return error_response("PROGRAM_NOT_FOUND", "Programa não encontrado", 404)
    return success_response(data=_program_to_dict(program, deep=True))


@followup_bp.route("/programs/<program_id>", methods=["PUT"])
@jwt_required()
def update_program(program_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    program = db.session.execute(
        db.select(FollowupProgramModel).where(
            FollowupProgramModel.id == UUID(program_id),
            FollowupProgramModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not program:
        return error_response("PROGRAM_NOT_FOUND", "Programa não encontrado", 404)
    body = request.get_json(force=True) or {}
    for field in ["name", "status", "current_phase", "metadata_json"]:
        if field in body:
            setattr(program, field, body[field])
    if body.get("completed_at"):
        program.completed_at = datetime.fromisoformat(body["completed_at"])
    db.session.commit()
    return success_response(data=_program_to_dict(program))


def _program_to_dict(program, deep=False):
    d = {
        "id": str(program.id),
        "patient_id": program.patient_id,
        "name": program.name,
        "specialty_code": program.specialty_code,
        "status": program.status,
        "current_phase": program.current_phase,
        "started_at": program.started_at.isoformat() if program.started_at else None,
        "completed_at": program.completed_at.isoformat() if program.completed_at else None,
        "created_at": program.created_at.isoformat() if program.created_at else None,
    }
    if deep:
        d["phases"] = [_phase_to_dict(p) for p in program.phases]
        d["checkpoints"] = [_checkpoint_to_dict(c) for c in program.checkpoints]
        d["questionnaires"] = [_questionnaire_to_dict(q) for q in program.questionnaires]
        d["alerts"] = [_alert_to_dict(a) for a in program.alerts]
    return d


# ═══════════════════════════════════════════════════════════════
# PHASES
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/phases", methods=["GET"])
@jwt_required()
def list_phases():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    program_id = request.args.get("program_id")
    q = db.select(FollowupPhaseModel).where(FollowupPhaseModel.tenant_id == tenant_id)
    if program_id:
        q = q.where(FollowupPhaseModel.program_id == UUID(program_id))
    items = db.session.execute(q.order_by(FollowupPhaseModel.order_index)).scalars().all()
    return success_response(data=[_phase_to_dict(i) for i in items])


@followup_bp.route("/phases", methods=["POST"])
@jwt_required()
def create_phase():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    phase = FollowupPhaseModel(
        program_id=UUID(body.get("program_id")),
        tenant_id=tenant_id,
        name=body.get("name", ""),
        description=body.get("description"),
        order_index=body.get("order_index", 0),
        target_duration_days=body.get("target_duration_days"),
    )
    db.session.add(phase)
    db.session.commit()
    return success_response(data=_phase_to_dict(phase), status=201)


def _phase_to_dict(phase):
    return {
        "id": str(phase.id),
        "program_id": str(phase.program_id),
        "name": phase.name,
        "description": phase.description,
        "order_index": phase.order_index,
        "status": phase.status,
        "started_at": phase.started_at.isoformat() if phase.started_at else None,
        "completed_at": phase.completed_at.isoformat() if phase.completed_at else None,
    }


# ═══════════════════════════════════════════════════════════════
# CHECKPOINTS
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/checkpoints", methods=["GET"])
@jwt_required()
def list_checkpoints():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    program_id = request.args.get("program_id")
    status = request.args.get("status")
    q = db.select(FollowupCheckpointModel).where(FollowupCheckpointModel.tenant_id == tenant_id)
    if program_id:
        q = q.where(FollowupCheckpointModel.program_id == UUID(program_id))
    if status:
        q = q.where(FollowupCheckpointModel.status == status)
    items = db.session.execute(q.order_by(FollowupCheckpointModel.due_date)).scalars().all()
    return success_response(data=[_checkpoint_to_dict(i) for i in items])


@followup_bp.route("/checkpoints", methods=["POST"])
@jwt_required()
def create_checkpoint():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    cp = FollowupCheckpointModel(
        program_id=UUID(body.get("program_id")),
        phase_id=body.get("phase_id") and UUID(body["phase_id"]),
        tenant_id=tenant_id,
        name=body.get("name", ""),
        description=body.get("description"),
        due_date=datetime.fromisoformat(body["due_date"]) if body.get("due_date") else None,
    )
    db.session.add(cp)
    db.session.commit()
    return success_response(data=_checkpoint_to_dict(cp), status=201)


@followup_bp.route("/checkpoints/<checkpoint_id>", methods=["PUT"])
@jwt_required()
def update_checkpoint(checkpoint_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    cp = db.session.execute(
        db.select(FollowupCheckpointModel).where(
            FollowupCheckpointModel.id == UUID(checkpoint_id),
            FollowupCheckpointModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not cp:
        return error_response("CHECKPOINT_NOT_FOUND", "Checkpoint não encontrado", 404)
    body = request.get_json(force=True) or {}
    for field in ["name", "description", "status", "notification_sent"]:
        if field in body:
            setattr(cp, field, body[field])
    if body.get("completed_at"):
        cp.completed_at = datetime.fromisoformat(body["completed_at"])
    db.session.commit()
    return success_response(data=_checkpoint_to_dict(cp))


def _checkpoint_to_dict(cp):
    return {
        "id": str(cp.id),
        "program_id": str(cp.program_id),
        "phase_id": str(cp.phase_id) if cp.phase_id else None,
        "name": cp.name,
        "description": cp.description,
        "due_date": cp.due_date.isoformat() if cp.due_date else None,
        "completed_at": cp.completed_at.isoformat() if cp.completed_at else None,
        "status": cp.status,
        "notification_sent": cp.notification_sent,
    }


# ═══════════════════════════════════════════════════════════════
# QUESTIONNAIRES & QUESTIONS
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/questionnaires", methods=["GET"])
@jwt_required()
def list_questionnaires():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    program_id = request.args.get("program_id")
    q = db.select(FollowupQuestionnaireModel).where(FollowupQuestionnaireModel.tenant_id == tenant_id)
    if program_id:
        q = q.where(FollowupQuestionnaireModel.program_id == UUID(program_id))
    items = db.session.execute(q.order_by(FollowupQuestionnaireModel.created_at.desc())).scalars().all()
    return success_response(data=[_questionnaire_to_dict(i, deep=True) for i in items])


@followup_bp.route("/questionnaires", methods=["POST"])
@jwt_required()
def create_questionnaire():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    qn = FollowupQuestionnaireModel(
        program_id=UUID(body.get("program_id")),
        tenant_id=tenant_id,
        name=body.get("name", ""),
        category=body.get("category"),
        description=body.get("description"),
        frequency_days=body.get("frequency_days", 7),
    )
    db.session.add(qn)
    db.session.commit()
    return success_response(data=_questionnaire_to_dict(qn), status=201)


def _questionnaire_to_dict(qn, deep=False):
    d = {
        "id": str(qn.id),
        "program_id": str(qn.program_id),
        "name": qn.name,
        "category": qn.category,
        "description": qn.description,
        "frequency_days": qn.frequency_days,
        "status": qn.status,
        "created_at": qn.created_at.isoformat() if qn.created_at else None,
    }
    if deep:
        d["questions"] = [_question_to_dict(q) for q in qn.questions]
    return d


@followup_bp.route("/questions", methods=["POST"])
@jwt_required()
def create_question():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    q = FollowupQuestionModel(
        questionnaire_id=UUID(body.get("questionnaire_id")),
        tenant_id=tenant_id,
        text=body.get("text", ""),
        question_type=body.get("question_type", "scale"),
        min_value=body.get("min_value", 0.0),
        max_value=body.get("max_value", 10.0),
        options=body.get("options", []),
        order_index=body.get("order_index", 0),
    )
    db.session.add(q)
    db.session.commit()
    return success_response(data=_question_to_dict(q), status=201)


def _question_to_dict(q):
    return {
        "id": str(q.id),
        "questionnaire_id": str(q.questionnaire_id),
        "text": q.text,
        "question_type": q.question_type,
        "min_value": q.min_value,
        "max_value": q.max_value,
        "options": q.options,
        "order_index": q.order_index,
    }


# ═══════════════════════════════════════════════════════════════
# RESPONSES
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/responses", methods=["GET"])
@jwt_required()
def list_responses():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient_id = request.args.get("patient_id", type=int)
    questionnaire_id = request.args.get("questionnaire_id")
    q = db.select(FollowupResponseModel).where(FollowupResponseModel.tenant_id == tenant_id)
    if patient_id:
        q = q.where(FollowupResponseModel.patient_id == patient_id)
    if questionnaire_id:
        q = q.where(FollowupResponseModel.questionnaire_id == UUID(questionnaire_id))
    items = db.session.execute(q.order_by(FollowupResponseModel.responded_at.desc())).scalars().all()
    return success_response(data=[_response_to_dict(i) for i in items])


@followup_bp.route("/responses", methods=["POST"])
@jwt_required()
def create_response():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return error_response("MISSING_PATIENT_ID", "patient_id é obrigatório", 400)
    resp = FollowupResponseModel(
        questionnaire_id=UUID(body.get("questionnaire_id")),
        question_id=UUID(body.get("question_id")),
        patient_id=patient_id,
        tenant_id=tenant_id,
        value=body.get("value"),
        numeric_value=body.get("numeric_value"),
        responded_by=body.get("responded_by", "patient"),
        metadata_json=body.get("metadata", {}),
    )
    db.session.add(resp)
    db.session.commit()
    return success_response(data=_response_to_dict(resp), status=201)


def _response_to_dict(r):
    return {
        "id": str(r.id),
        "questionnaire_id": str(r.questionnaire_id),
        "question_id": str(r.question_id),
        "patient_id": r.patient_id,
        "value": r.value,
        "numeric_value": r.numeric_value,
        "responded_at": r.responded_at.isoformat() if r.responded_at else None,
        "responded_by": r.responded_by,
    }


# ═══════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/alerts", methods=["GET"])
@jwt_required()
def list_alerts():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient_id = request.args.get("patient_id", type=int)
    status_filter = request.args.get("status")
    q = db.select(FollowupAlertModel).where(FollowupAlertModel.tenant_id == tenant_id)
    if patient_id:
        q = q.where(FollowupAlertModel.patient_id == patient_id)
    if status_filter:
        q = q.where(FollowupAlertModel.status == status_filter)
    items = db.session.execute(q.order_by(FollowupAlertModel.triggered_at.desc())).scalars().all()
    return success_response(data=[_alert_to_dict(i) for i in items])


@followup_bp.route("/alerts/<alert_id>/resolve", methods=["POST"])
@jwt_required()
def resolve_alert(alert_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    alert = db.session.execute(
        db.select(FollowupAlertModel).where(
            FollowupAlertModel.id == UUID(alert_id),
            FollowupAlertModel.tenant_id == tenant_id,
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
        "program_id": str(alert.program_id),
        "patient_id": alert.patient_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "status": alert.status,
        "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "escalation_level": alert.escalation_level,
    }


# ═══════════════════════════════════════════════════════════════
# ESCALATIONS
# ═══════════════════════════════════════════════════════════════

@followup_bp.route("/escalations", methods=["GET"])
@jwt_required()
def list_escalations():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    alert_id = request.args.get("alert_id")
    q = db.select(FollowupEscalationModel).where(FollowupEscalationModel.tenant_id == tenant_id)
    if alert_id:
        q = q.where(FollowupEscalationModel.alert_id == UUID(alert_id))
    items = db.session.execute(q.order_by(FollowupEscalationModel.escalated_at.desc())).scalars().all()
    return success_response(data=[_escalation_to_dict(i) for i in items])


@followup_bp.route("/escalations", methods=["POST"])
@jwt_required()
def create_escalation():
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    body = request.get_json(force=True) or {}
    esc = FollowupEscalationModel(
        alert_id=UUID(body.get("alert_id")),
        patient_id=body.get("patient_id"),
        tenant_id=tenant_id,
        from_level=body.get("from_level", 0),
        to_level=body.get("to_level", 1),
        reason=body.get("reason"),
        escalated_by=int(get_jwt_identity()),
    )
    db.session.add(esc)
    db.session.commit()
    return success_response(data=_escalation_to_dict(esc), status=201)


def _escalation_to_dict(esc):
    return {
        "id": str(esc.id),
        "alert_id": str(esc.alert_id),
        "from_level": esc.from_level,
        "to_level": esc.to_level,
        "reason": esc.reason,
        "escalated_at": esc.escalated_at.isoformat() if esc.escalated_at else None,
    }
