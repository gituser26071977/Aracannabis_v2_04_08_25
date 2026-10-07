"""
Modelos de dados para ARAOS Voice.
Compatível com Flask-SQLAlchemy (db.Model).
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from models import db


class SessionStatus(PyEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ActionStatus(PyEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    EXPIRED = "expired"


class VoiceSessionModel(db.Model):
    """Sessão de consulta por voz."""
    __tablename__ = "voice_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), nullable=False)
    patient_id = db.Column(db.String(36), nullable=False)
    doctor_id = db.Column(db.String(36), nullable=False)

    specialty = db.Column(db.String(50), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    wake_word = db.Column(db.String(50), default="Ara")
    language = db.Column(db.String(10), default="pt-BR")
    mode = db.Column(db.String(20), default="full")

    status = db.Column(db.String(20), default=SessionStatus.ACTIVE.value)

    total_audio_duration_ms = db.Column(db.Integer, default=0)
    speech_duration_ms = db.Column(db.Integer, default=0)
    doctor_speech_duration_ms = db.Column(db.Integer, default=0)
    patient_speech_duration_ms = db.Column(db.Integer, default=0)

    structured_data = db.Column(db.JSON, default=dict)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transcripts = db.relationship("VoiceTranscriptModel", back_populates="session", cascade="all, delete-orphan")
    entities = db.relationship("VoiceEntityModel", back_populates="session", cascade="all, delete-orphan")
    actions = db.relationship("VoiceActionModel", back_populates="session", cascade="all, delete-orphan")
    audit_logs = db.relationship("VoiceAuditLogModel", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        db.Index("idx_voice_sessions_patient", "patient_id", "started_at"),
        db.Index("idx_voice_sessions_tenant", "tenant_id", "started_at"),
    )


class VoiceTranscriptModel(db.Model):
    """Transcrição de um segmento de fala."""
    __tablename__ = "voice_transcripts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False)

    segment_index = db.Column(db.Integer, nullable=False)
    speaker = db.Column(db.String(20), nullable=False)

    start_time_ms = db.Column(db.Integer, nullable=False)
    end_time_ms = db.Column(db.Integer, nullable=False)

    text = db.Column(db.Text, nullable=False)
    text_normalized = db.Column(db.Text, nullable=True)

    confidence = db.Column(db.Float, nullable=True)
    is_final = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default="pt-BR")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("VoiceSessionModel", back_populates="transcripts")

    __table_args__ = (
        db.UniqueConstraint("session_id", "segment_index"),
        db.Index("idx_voice_transcripts_session", "session_id", "segment_index"),
    )


class VoiceEntityModel(db.Model):
    """Entidade clínica extraída da transcrição."""
    __tablename__ = "voice_entities"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False)
    transcript_id = db.Column(db.String(36), db.ForeignKey("voice_transcripts.id"), nullable=True)

    entity_type = db.Column(db.String(30), nullable=False)
    text = db.Column(db.Text, nullable=False)
    normalized_name = db.Column(db.String(255), nullable=True)

    cui = db.Column(db.String(20), nullable=True)
    icd10 = db.Column(db.String(20), nullable=True)
    atc = db.Column(db.String(20), nullable=True)
    loinc = db.Column(db.String(20), nullable=True)

    value = db.Column(db.Text, nullable=True)
    unit = db.Column(db.String(50), nullable=True)

    temporal = db.Column(db.String(50), nullable=True)
    negated = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, nullable=True)
    source = db.Column(db.String(20), default="patient")

    start_time_ms = db.Column(db.Integer, nullable=True)
    end_time_ms = db.Column(db.Integer, nullable=True)

    persisted_to_ehr = db.Column(db.Boolean, default=False)
    persisted_record_id = db.Column(db.String(36), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("VoiceSessionModel", back_populates="entities")

    __table_args__ = (
        db.Index("idx_voice_entities_session", "session_id", "entity_type"),
    )


class VoiceActionModel(db.Model):
    """Ação proposta/executada durante a sessão de voz."""
    __tablename__ = "voice_actions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False)

    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    parameters = db.Column(db.JSON, default=dict)
    preview = db.Column(db.JSON, nullable=True)

    status = db.Column(db.String(20), default=ActionStatus.PROPOSED.value)

    confirmed_by = db.Column(db.String(36), nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmation_method = db.Column(db.String(20), nullable=True)

    executed_at = db.Column(db.DateTime, nullable=True)
    result = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("VoiceSessionModel", back_populates="actions")


class VoiceAuditLogModel(db.Model):
    """Log de auditoria completo da sessão de voz."""
    __tablename__ = "voice_audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("voice_sessions.id", ondelete="CASCADE"), nullable=False)

    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.JSON, default=dict)

    doctor_id = db.Column(db.String(36), nullable=False)
    patient_id = db.Column(db.String(36), nullable=False)

    occurred_at = db.Column(db.DateTime, default=datetime.utcnow)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    session = db.relationship("VoiceSessionModel", back_populates="audit_logs")

    __table_args__ = (
        db.Index("idx_voice_audit_session", "session_id", "occurred_at"),
    )
