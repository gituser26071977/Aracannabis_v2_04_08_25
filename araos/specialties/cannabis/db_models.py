"""
ARAOS Cannabis Module — Persistent Database Models.

Week 11D — Productization Layer.
All patient-specific cannabis data lives in these SQLAlchemy tables.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models import db


# ───────────────────────────────────────────────────────────────
# 1. CANNABIS PROFILES
# ───────────────────────────────────────────────────────────────

class CannabisProfileModel(db.Model):
    __tablename__ = "cannabis_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    specialty_code = Column(String(50), default="cannabis", nullable=False)
    eligibility_status = Column(String(20), default="eligible")  # eligible, ineligible, pending
    eligibility_reason = Column(Text)
    primary_condition = Column(String(100))
    secondary_conditions = Column(JSON, default=list)
    treatment_status = Column(String(20), default="active")  # active, paused, discontinued, completed
    started_at = Column(DateTime)
    discontinued_at = Column(DateTime)
    discontinued_reason = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    goals = relationship("CannabisTherapeuticGoalModel", back_populates="profile", cascade="all, delete-orphan")
    medications = relationship("CannabisMedicationModel", back_populates="profile", cascade="all, delete-orphan")
    dose_entries = relationship("CannabisDoseEntryModel", back_populates="profile", cascade="all, delete-orphan")
    outcome_scores = relationship("CannabisOutcomeScoreModel", back_populates="profile", cascade="all, delete-orphan")
    alerts = relationship("CannabisAlertModel", back_populates="profile", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cannabis_profiles_patient_tenant", "patient_id", "tenant_id"),
        UniqueConstraint("patient_id", "tenant_id", name="uq_cannabis_profile_patient_tenant"),
    )


class CannabisTherapeuticGoalModel(db.Model):
    __tablename__ = "cannabis_therapeutic_goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_profiles.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    target_symptom = Column(String(100), nullable=False)
    target_metric = Column(String(100))
    baseline_score = Column(Float, default=0.0)
    target_score = Column(Float, default=0.0)
    current_score = Column(Float, default=0.0)
    achieved = Column(Boolean, default=False)
    achieved_at = Column(DateTime)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("CannabisProfileModel", back_populates="goals")

    __table_args__ = (
        Index("ix_cannabis_goals_profile", "profile_id"),
    )


# ───────────────────────────────────────────────────────────────
# 2. CANNABIS PRODUCTS (Catalog)
# ───────────────────────────────────────────────────────────────

class CannabisProductModel(db.Model):
    __tablename__ = "cannabis_products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    manufacturer = Column(String(200))
    formulation = Column(String(50))  # oil, flower, capsule, topical, etc.
    spectrum = Column(String(50))  # full, broad, isolate
    cbd_mg = Column(Float, default=0.0)
    thc_mg = Column(Float, default=0.0)
    cbg_mg = Column(Float, default=0.0)
    cbn_mg = Column(Float, default=0.0)
    cbc_mg = Column(Float, default=0.0)
    thcv_mg = Column(Float, default=0.0)
    unit = Column(String(20), default="mg/ml")
    volume_ml = Column(Float)
    route = Column(String(50))  # sublingual, oral, inhaled, topical
    batch_number = Column(String(100))
    expiry_date = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    medications = relationship("CannabisMedicationModel", back_populates="product")

    __table_args__ = (
        Index("ix_cannabis_products_tenant", "tenant_id"),
    )


# ───────────────────────────────────────────────────────────────
# 3. CANNABIS MEDICATIONS (Prescriptions)
# ───────────────────────────────────────────────────────────────

class CannabisMedicationModel(db.Model):
    __tablename__ = "cannabis_medications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_profiles.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_products.id", ondelete="SET NULL"), nullable=True)
    prescribed_dose_mg = Column(Float)
    frequency = Column(String(50))  # twice_daily, three_times_daily, etc.
    status = Column(String(20), default="active")  # active, stopped, completed
    instructions = Column(Text)
    prescribed_by = Column(Integer, ForeignKey("profissionais.id", ondelete="SET NULL"))
    prescribed_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    stopped_at = Column(DateTime)
    stopped_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("CannabisProfileModel", back_populates="medications")
    product = relationship("CannabisProductModel", back_populates="medications")

    __table_args__ = (
        Index("ix_cannabis_medications_patient", "patient_id"),
        Index("ix_cannabis_medications_tenant", "tenant_id"),
    )


# ───────────────────────────────────────────────────────────────
# 4. CANNABIS DOSE ENTRIES (Timeline)
# ───────────────────────────────────────────────────────────────

class CannabisDoseEntryModel(db.Model):
    __tablename__ = "cannabis_dose_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_profiles.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    medication_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_medications.id", ondelete="SET NULL"), nullable=True)
    dose_mg = Column(Float)
    thc_mg = Column(Float)
    cbd_mg = Column(Float)
    entry_type = Column(String(20), default="administered")  # administered, adjusted, paused, resumed
    reason = Column(Text)
    physician_id = Column(Integer, ForeignKey("profissionais.id", ondelete="SET NULL"))
    entry_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("CannabisProfileModel", back_populates="dose_entries")

    __table_args__ = (
        Index("ix_cannabis_dose_entries_patient_date", "patient_id", "entry_date"),
        Index("ix_cannabis_dose_entries_tenant", "tenant_id"),
    )


# ───────────────────────────────────────────────────────────────
# 5. CANNABIS OUTCOME SCORES
# ───────────────────────────────────────────────────────────────

class CannabisOutcomeScoreModel(db.Model):
    __tablename__ = "cannabis_outcome_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_profiles.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # pain, anxiety, sleep, quality_of_life
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=10.0)
    unit = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.utcnow)
    context = Column(Text)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("CannabisProfileModel", back_populates="outcome_scores")

    __table_args__ = (
        Index("ix_cannabis_outcome_scores_patient_metric", "patient_id", "metric_name"),
        Index("ix_cannabis_outcome_scores_recorded", "recorded_at"),
    )


# ───────────────────────────────────────────────────────────────
# 6. CANNABIS ALERTS
# ───────────────────────────────────────────────────────────────

class CannabisAlertModel(db.Model):
    __tablename__ = "cannabis_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("cannabis_profiles.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="low")  # info, low, medium, high, critical
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

    profile = relationship("CannabisProfileModel", back_populates="alerts")

    __table_args__ = (
        Index("ix_cannabis_alerts_patient_status", "patient_id", "status"),
        Index("ix_cannabis_alerts_tenant", "tenant_id"),
        Index("ix_cannabis_alerts_severity", "severity"),
    )
