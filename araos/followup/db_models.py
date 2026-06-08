"""
ARAOS Follow-up Engine — Persistent Database Models.

Week 11D — Productization Layer.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models import db


class FollowupProgramModel(db.Model):
    __tablename__ = "followup_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    specialty_code = Column(String(50), default="cannabis")
    status = Column(String(20), default="active")  # active, completed, paused, cancelled
    current_phase = Column(String(50))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    phases = relationship("FollowupPhaseModel", back_populates="program", cascade="all, delete-orphan")
    checkpoints = relationship("FollowupCheckpointModel", back_populates="program", cascade="all, delete-orphan")
    questionnaires = relationship("FollowupQuestionnaireModel", back_populates="program", cascade="all, delete-orphan")
    alerts = relationship("FollowupAlertModel", back_populates="program", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_followup_programs_patient", "patient_id"),
        Index("ix_followup_programs_tenant", "tenant_id"),
    )


class FollowupPhaseModel(db.Model):
    __tablename__ = "followup_phases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("followup_programs.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, active, completed, skipped
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    target_duration_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    program = relationship("FollowupProgramModel", back_populates="phases")
    checkpoints = relationship("FollowupCheckpointModel", back_populates="phase", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_followup_phases_program", "program_id"),
    )


class FollowupCheckpointModel(db.Model):
    __tablename__ = "followup_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("followup_programs.id", ondelete="CASCADE"), nullable=False)
    phase_id = Column(UUID(as_uuid=True), ForeignKey("followup_phases.id", ondelete="CASCADE"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, overdue, completed, skipped
    notification_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    program = relationship("FollowupProgramModel", back_populates="checkpoints")
    phase = relationship("FollowupPhaseModel", back_populates="checkpoints")

    __table_args__ = (
        Index("ix_followup_checkpoints_program", "program_id"),
        Index("ix_followup_checkpoints_due", "due_date"),
    )


class FollowupQuestionnaireModel(db.Model):
    __tablename__ = "followup_questionnaires"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("followup_programs.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(50))  # pain, anxiety, sleep, general
    description = Column(Text)
    frequency_days = Column(Integer, default=7)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    program = relationship("FollowupProgramModel", back_populates="questionnaires")
    questions = relationship("FollowupQuestionModel", back_populates="questionnaire", cascade="all, delete-orphan")
    responses = relationship("FollowupResponseModel", back_populates="questionnaire", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_followup_questionnaires_program", "program_id"),
    )


class FollowupQuestionModel(db.Model):
    __tablename__ = "followup_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    questionnaire_id = Column(UUID(as_uuid=True), ForeignKey("followup_questionnaires.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    question_type = Column(String(20), default="scale")  # scale, yes_no, text, multiple_choice
    min_value = Column(Float, default=0.0)
    max_value = Column(Float, default=10.0)
    options = Column(JSON, default=list)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    questionnaire = relationship("FollowupQuestionnaireModel", back_populates="questions")

    __table_args__ = (
        Index("ix_followup_questions_questionnaire", "questionnaire_id"),
    )


class FollowupResponseModel(db.Model):
    __tablename__ = "followup_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    questionnaire_id = Column(UUID(as_uuid=True), ForeignKey("followup_questionnaires.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("followup_questions.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    value = Column(Text)
    numeric_value = Column(Float)
    responded_at = Column(DateTime, default=datetime.utcnow)
    responded_by = Column(String(50), default="patient")  # patient, physician, system
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    questionnaire = relationship("FollowupQuestionnaireModel", back_populates="responses")

    __table_args__ = (
        Index("ix_followup_responses_patient", "patient_id"),
        Index("ix_followup_responses_questionnaire", "questionnaire_id"),
    )


class FollowupAlertModel(db.Model):
    __tablename__ = "followup_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id = Column(UUID(as_uuid=True), ForeignKey("followup_programs.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="low")
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="active")  # active, acknowledged, resolved, dismissed
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("profissionais.id", ondelete="SET NULL"))
    escalation_level = Column(Integer, default=0)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    program = relationship("FollowupProgramModel", back_populates="alerts")

    __table_args__ = (
        Index("ix_followup_alerts_patient_status", "patient_id", "status"),
        Index("ix_followup_alerts_tenant", "tenant_id"),
    )


class FollowupEscalationModel(db.Model):
    __tablename__ = "followup_escalations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("followup_alerts.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    from_level = Column(Integer, default=0)
    to_level = Column(Integer, default=1)
    reason = Column(Text)
    escalated_at = Column(DateTime, default=datetime.utcnow)
    escalated_by = Column(Integer, ForeignKey("profissionais.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_followup_escalations_alert", "alert_id"),
    )
