"""
AraOS Digital Twin API — Week 11D Productization Layer.

Exposes the Digital Twin as a public internal API.
All data is read from persistent tables and aggregated on-the-fly.
"""
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func

from models import db, Paciente, Sintoma, Dosagem, Evolucao, Consulta, Exame
from araos.platform.api.response import success_response, error_response
from araos.specialties.cannabis.db_models import (
    CannabisProfileModel,
    CannabisDoseEntryModel,
    CannabisOutcomeScoreModel,
    CannabisAlertModel,
    CannabisMedicationModel,
)

twin_bp = Blueprint("twin", __name__)


def _get_tenant_id():
    return getattr(g, "current_association", None) and g.current_association.id


def _require_tenant():
    tid = _get_tenant_id()
    if not tid:
        return error_response("MISSING_TENANT", "X-Association-ID header required", 403)
    return tid


def _get_patient_or_404(patient_id, tenant_id):
    patient = db.session.execute(
        db.select(Paciente).where(
            Paciente.id == patient_id,
            Paciente.associacao_id == tenant_id,
        )
    ).scalar_one_or_none()
    if not patient:
        return None, error_response("PATIENT_NOT_FOUND", "Paciente não encontrado", 404)
    return patient, None


# ═══════════════════════════════════════════════════════════════
# FULL TWIN VIEW
# ═══════════════════════════════════════════════════════════════

@twin_bp.route("/<int:patient_id>", methods=["GET"])
@jwt_required()
def get_twin(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient, err = _get_patient_or_404(patient_id, tenant_id)
    if err:
        return err

    return success_response(data={
        "patient": _patient_summary(patient),
        "demographics": _patient_demographics(patient),
        "clinical_summary": _clinical_summary(patient_id, tenant_id),
        "cannabis": _cannabis_summary(patient_id, tenant_id),
        "timeline": _timeline_summary(patient_id, tenant_id),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    })


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

@twin_bp.route("/<int:patient_id>/summary", methods=["GET"])
@jwt_required()
def get_summary(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient, err = _get_patient_or_404(patient_id, tenant_id)
    if err:
        return err

    return success_response(data=_clinical_summary(patient_id, tenant_id))


# ═══════════════════════════════════════════════════════════════
# TIMELINE
# ═══════════════════════════════════════════════════════════════

@twin_bp.route("/<int:patient_id>/timeline", methods=["GET"])
@jwt_required()
def get_timeline(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient, err = _get_patient_or_404(patient_id, tenant_id)
    if err:
        return err

    events = []

    # Consultas
    for c in db.session.execute(
        db.select(Consulta).where(Consulta.paciente_id == patient_id).order_by(Consulta.data_hora)
    ).scalars():
        events.append({
            "date": c.data_hora.isoformat() if c.data_hora else None,
            "type": "consultation",
            "status": c.status,
            "title": c.tipo_consulta or "Consulta",
            "description": c.observacoes,
        })

    # Evoluções
    for e in db.session.execute(
        db.select(Evolucao).where(Evolucao.paciente_id == patient_id).order_by(Evolucao.data_evolucao)
    ).scalars():
        events.append({
            "date": e.data_evolucao.isoformat() if e.data_evolucao else None,
            "type": "evolution",
            "title": "Evolução Clínica",
            "description": e.nota_evolucao,
        })

    # Sintomas
    for s in db.session.execute(
        db.select(Sintoma).where(Sintoma.paciente_id == patient_id).order_by(Sintoma.data)
    ).scalars():
        events.append({
            "date": s.data.isoformat() if s.data else None,
            "type": "symptom",
            "title": f"Sintoma: {s.sintoma}",
            "description": f"Intensidade: {s.intensidade}/10",
        })

    # Doses (legacy)
    for d in db.session.execute(
        db.select(Dosagem).where(Dosagem.paciente_id == patient_id).order_by(Dosagem.data)
    ).scalars():
        events.append({
            "date": d.data.isoformat() if d.data else None,
            "type": "dosage",
            "title": f"Dosagem: {d.dosagem}",
            "description": f"{d.gotas} gotas, {d.frequencia_diaria}x ao dia",
        })

    # Exames
    for ex in db.session.execute(
        db.select(Exame).where(Exame.paciente_id == patient_id).order_by(Exame.data_exame)
    ).scalars():
        events.append({
            "date": ex.data_exame.isoformat() if ex.data_exame else None,
            "type": "exam",
            "title": f"Exame: {ex.titulo or ex.tipo_exame}",
            "description": ex.descricao,
        })

    # Cannabis doses
    for cd in db.session.execute(
        db.select(CannabisDoseEntryModel).where(
            CannabisDoseEntryModel.patient_id == patient_id
        ).order_by(CannabisDoseEntryModel.entry_date)
    ).scalars():
        events.append({
            "date": cd.entry_date.isoformat() if cd.entry_date else None,
            "type": "cannabis_dose",
            "title": f"Dose Cannabis: {cd.dose_mg}mg",
            "description": cd.reason,
        })

    # Cannabis outcomes
    for co in db.session.execute(
        db.select(CannabisOutcomeScoreModel).where(
            CannabisOutcomeScoreModel.patient_id == patient_id
        ).order_by(CannabisOutcomeScoreModel.recorded_at)
    ).scalars():
        events.append({
            "date": co.recorded_at.isoformat() if co.recorded_at else None,
            "type": "cannabis_outcome",
            "title": f"Outcome: {co.metric_name}",
            "description": f"Score: {co.score}/{co.max_score}",
        })

    events.sort(key=lambda x: x["date"] or "", reverse=True)

    return success_response(data={
        "events": events,
        "total_events": len(events),
        "date_range": {
            "from": events[-1]["date"] if events else None,
            "to": events[0]["date"] if events else None,
        },
    })


# ═══════════════════════════════════════════════════════════════
# OUTCOMES
# ═══════════════════════════════════════════════════════════════

@twin_bp.route("/<int:patient_id>/outcomes", methods=["GET"])
@jwt_required()
def get_outcomes(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id

    # Aggregate legacy symptom scores
    legacy_symptoms = {}
    for s in db.session.execute(
        db.select(Sintoma).where(Sintoma.paciente_id == patient_id).order_by(Sintoma.data)
    ).scalars():
        key = s.sintoma
        if key not in legacy_symptoms:
            legacy_symptoms[key] = []
        legacy_symptoms[key].append({"date": s.data.isoformat(), "score": s.intensidade, "max": 10})

    # Aggregate cannabis outcome scores
    cannabis_outcomes = {}
    for co in db.session.execute(
        db.select(CannabisOutcomeScoreModel).where(
            CannabisOutcomeScoreModel.patient_id == patient_id,
            CannabisOutcomeScoreModel.tenant_id == tenant_id,
        ).order_by(CannabisOutcomeScoreModel.recorded_at)
    ).scalars():
        key = co.metric_name
        if key not in cannabis_outcomes:
            cannabis_outcomes[key] = []
        cannabis_outcomes[key].append({
            "date": co.recorded_at.isoformat(),
            "score": co.score,
            "max": co.max_score,
        })

    # Compute trends
    def _trend(scores):
        if len(scores) < 2:
            return "insufficient_data"
        first = scores[0]["score"]
        last = scores[-1]["score"]
        if last < first:
            return "improving"
        elif last > first:
            return "worsening"
        return "stable"

    return success_response(data={
        "legacy_symptoms": {k: {"scores": v, "trend": _trend(v)} for k, v in legacy_symptoms.items()},
        "cannabis_outcomes": {k: {"scores": v, "trend": _trend(v)} for k, v in cannabis_outcomes.items()},
    })


# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@twin_bp.route("/<int:patient_id>/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard(patient_id):
    tenant_id = _require_tenant()
    if isinstance(tenant_id, tuple):
        return tenant_id
    patient, err = _get_patient_or_404(patient_id, tenant_id)
    if err:
        return err

    # Counts
    symptom_count = db.session.execute(
        db.select(func.count()).select_from(Sintoma).where(Sintoma.paciente_id == patient_id)
    ).scalar()
    dose_count = db.session.execute(
        db.select(func.count()).select_from(Dosagem).where(Dosagem.paciente_id == patient_id)
    ).scalar()
    evolution_count = db.session.execute(
        db.select(func.count()).select_from(Evolucao).where(Evolucao.paciente_id == patient_id)
    ).scalar()
    consultation_count = db.session.execute(
        db.select(func.count()).select_from(Consulta).where(Consulta.paciente_id == patient_id)
    ).scalar()
    exam_count = db.session.execute(
        db.select(func.count()).select_from(Exame).where(Exame.paciente_id == patient_id)
    ).scalar()

    # Cannabis counts
    cannabis_dose_count = db.session.execute(
        db.select(func.count()).select_from(CannabisDoseEntryModel).where(CannabisDoseEntryModel.patient_id == patient_id)
    ).scalar()
    cannabis_outcome_count = db.session.execute(
        db.select(func.count()).select_from(CannabisOutcomeScoreModel).where(CannabisOutcomeScoreModel.patient_id == patient_id)
    ).scalar()
    active_alerts = db.session.execute(
        db.select(func.count()).select_from(CannabisAlertModel).where(
            CannabisAlertModel.patient_id == patient_id,
            CannabisAlertModel.status == "active",
        )
    ).scalar()

    # Last activity
    last_consultation = db.session.execute(
        db.select(Consulta).where(Consulta.paciente_id == patient_id).order_by(Consulta.data_hora.desc()).limit(1)
    ).scalar_one_or_none()

    return success_response(data={
        "patient": _patient_summary(patient),
        "counts": {
            "symptoms": symptom_count,
            "dosages": dose_count,
            "evolutions": evolution_count,
            "consultations": consultation_count,
            "exams": exam_count,
            "cannabis_doses": cannabis_dose_count,
            "cannabis_outcomes": cannabis_outcome_count,
            "active_alerts": active_alerts,
        },
        "last_activity": {
            "type": "consultation" if last_consultation else None,
            "date": last_consultation.data_hora.isoformat() if last_consultation else None,
        },
        "treatment_status": patient.em_tratamento,
    })


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _patient_summary(patient):
    return {
        "id": patient.id,
        "name": patient.nome,
        "age": _calculate_age(patient.data_nascimento),
        "condition": patient.condicao_medica,
        "in_treatment": patient.em_tratamento,
    }


def _patient_demographics(patient):
    return {
        "id": patient.id,
        "name": patient.nome,
        "birth_date": patient.data_nascimento.isoformat() if patient.data_nascimento else None,
        "gender": patient.genero,
        "phone": patient.telefone,
        "email": patient.email,
        "address": patient.endereco,
        "diagnosis": patient.diagnostico,
    }


def _clinical_summary(patient_id, tenant_id):
    recent_symptoms = db.session.execute(
        db.select(Sintoma).where(Sintoma.paciente_id == patient_id).order_by(Sintoma.data.desc()).limit(5)
    ).scalars().all()

    recent_evolucoes = db.session.execute(
        db.select(Evolucao).where(Evolucao.paciente_id == patient_id).order_by(Evolucao.data_evolucao.desc()).limit(3)
    ).scalars().all()

    upcoming_consultations = db.session.execute(
        db.select(Consulta).where(
            Consulta.paciente_id == patient_id,
            Consulta.data_hora >= datetime.utcnow(),
        ).order_by(Consulta.data_hora).limit(3)
    ).scalars().all()

    return {
        "recent_symptoms": [{"date": s.data.isoformat(), "symptom": s.sintoma, "intensity": s.intensidade} for s in recent_symptoms],
        "recent_evolutions": [{"date": e.data_evolucao.isoformat(), "note": e.nota_evolucao} for e in recent_evolucoes],
        "upcoming_consultations": [{"date": c.data_hora.isoformat(), "type": c.tipo_consulta, "status": c.status} for c in upcoming_consultations],
    }


def _cannabis_summary(patient_id, tenant_id):
    profile = db.session.execute(
        db.select(CannabisProfileModel).where(
            CannabisProfileModel.patient_id == patient_id,
            CannabisProfileModel.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()

    if not profile:
        return None

    active_medications = db.session.execute(
        db.select(CannabisMedicationModel).where(
            CannabisMedicationModel.patient_id == patient_id,
            CannabisMedicationModel.status == "active",
        )
    ).scalars().all()

    recent_doses = db.session.execute(
        db.select(CannabisDoseEntryModel).where(
            CannabisDoseEntryModel.patient_id == patient_id,
        ).order_by(CannabisDoseEntryModel.entry_date.desc()).limit(5)
    ).scalars().all()

    recent_outcomes = db.session.execute(
        db.select(CannabisOutcomeScoreModel).where(
            CannabisOutcomeScoreModel.patient_id == patient_id,
        ).order_by(CannabisOutcomeScoreModel.recorded_at.desc()).limit(5)
    ).scalars().all()

    active_alerts = db.session.execute(
        db.select(CannabisAlertModel).where(
            CannabisAlertModel.patient_id == patient_id,
            CannabisAlertModel.status == "active",
        ).order_by(CannabisAlertModel.triggered_at.desc())
    ).scalars().all()

    return {
        "profile_id": str(profile.id),
        "primary_condition": profile.primary_condition,
        "treatment_status": profile.treatment_status,
        "started_at": profile.started_at.isoformat() if profile.started_at else None,
        "active_medications": [{"id": str(m.id), "product": m.product.name if m.product else None, "dose_mg": m.prescribed_dose_mg} for m in active_medications],
        "recent_doses": [_dose_to_dict(d) for d in recent_doses],
        "recent_outcomes": [_outcome_to_dict(o) for o in recent_outcomes],
        "active_alerts": [{"id": str(a.id), "type": a.alert_type, "severity": a.severity, "title": a.title} for a in active_alerts],
    }


def _timeline_summary(patient_id, tenant_id):
    counts = {
        "consultations": db.session.execute(db.select(func.count()).select_from(Consulta).where(Consulta.paciente_id == patient_id)).scalar(),
        "evolutions": db.session.execute(db.select(func.count()).select_from(Evolucao).where(Evolucao.paciente_id == patient_id)).scalar(),
        "symptoms": db.session.execute(db.select(func.count()).select_from(Sintoma).where(Sintoma.paciente_id == patient_id)).scalar(),
        "exams": db.session.execute(db.select(func.count()).select_from(Exame).where(Exame.paciente_id == patient_id)).scalar(),
        "cannabis_doses": db.session.execute(db.select(func.count()).select_from(CannabisDoseEntryModel).where(CannabisDoseEntryModel.patient_id == patient_id)).scalar(),
        "cannabis_outcomes": db.session.execute(db.select(func.count()).select_from(CannabisOutcomeScoreModel).where(CannabisOutcomeScoreModel.patient_id == patient_id)).scalar(),
    }
    return counts


def _dose_to_dict(dose):
    return {
        "id": str(dose.id),
        "dose_mg": dose.dose_mg,
        "thc_mg": dose.thc_mg,
        "cbd_mg": dose.cbd_mg,
        "entry_type": dose.entry_type,
        "reason": dose.reason,
        "entry_date": dose.entry_date.isoformat() if dose.entry_date else None,
    }


def _outcome_to_dict(outcome):
    return {
        "id": str(outcome.id),
        "metric_name": outcome.metric_name,
        "score": outcome.score,
        "max_score": outcome.max_score,
        "recorded_at": outcome.recorded_at.isoformat() if outcome.recorded_at else None,
    }


def _calculate_age(birth_date):
    if not birth_date:
        return None
    today = datetime.today().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
