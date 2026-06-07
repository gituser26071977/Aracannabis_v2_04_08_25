"""
AraOS Clinical — Entity Models.

Entidades clínicas estruturadas:
    - Diagnosis (ICD-10, SNOMED)
    - Medication
    - Allergy
    - Procedure
    - RiskFactor

Todas são imutáveis versionadas — alterações geram novos registros,
não updates. Isso preserva histórico e timeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, JSON, Index, Integer
)

from araos.platform.tenant.models import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalEntityStatus(str, Enum):
    """Status de uma entidade clínica."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    CHRONIC = "chronic"
    ACUTE = "acute"
    HISTORY = "history"  # Apenas histórico


class ClinicalEntityBase(Base):
    """Base abstrata para entidades clínicas."""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    
    status = Column(String(20), nullable=False, default=ClinicalEntityStatus.ACTIVE.value)
    
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    recorded_by = Column(String(36), nullable=True)  # professional_id
    
    # Metadados para extensibilidade futura
    entity_metadata = Column(JSON, nullable=True, default=dict)
    
    # Versionamento
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)
    previous_version_id = Column(String(36), nullable=True)


class Diagnosis(ClinicalEntityBase):
    """
    Diagnóstico clínico.
    
    Suporta:
        - ICD-10 (classificação internacional)
        - SNOMED CT (terminologia clínica)
        - CID-11 (futuro)
    """
    __tablename__ = "araos_clinical_diagnoses"
    
    description = Column(Text, nullable=False)
    icd10_code = Column(String(10), nullable=True, index=True)
    icd10_description = Column(Text, nullable=True)
    snomed_code = Column(String(20), nullable=True, index=True)
    snomed_description = Column(Text, nullable=True)
    
    onset_date = Column(DateTime(timezone=True), nullable=True)
    resolution_date = Column(DateTime(timezone=True), nullable=True)
    
    is_primary = Column(Boolean, nullable=False, default=False)
    is_chronic = Column(Boolean, nullable=False, default=False)
    
    # Qualificadores
    laterality = Column(String(20), nullable=True)  # left, right, bilateral
    severity = Column(String(20), nullable=True)    # mild, moderate, severe
    
    __table_args__ = (
        Index("ix_diagnosis_patient_current", "patient_id", "is_current"),
        Index("ix_diagnosis_icd10", "icd10_code"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "icd10_code": self.icd10_code,
            "snomed_code": self.snomed_code,
            "status": self.status,
            "is_primary": self.is_primary,
            "is_chronic": self.is_chronic,
            "onset_date": self.onset_date.isoformat() if self.onset_date else None,
        }


class Medication(ClinicalEntityBase):
    """
    Medicação.
    
    Representa prescrição ativa ou histórica.
    """
    __tablename__ = "araos_clinical_medications"
    
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    
    dosage = Column(String(100), nullable=True)  # ex: "50mg"
    frequency = Column(String(100), nullable=True)  # ex: "2x ao dia"
    route = Column(String(50), nullable=True)  # oral, IV, topical, etc
    
    prescribed_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    stopped_reason = Column(Text, nullable=True)
    
    prescribed_by = Column(String(36), nullable=True)  # professional_id
    
    __table_args__ = (
        Index("ix_medication_patient_current", "patient_id", "is_current"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "route": self.route,
            "status": self.status,
            "prescribed_at": self.prescribed_at.isoformat() if self.prescribed_at else None,
        }


class Allergy(ClinicalEntityBase):
    """
    Alergia ou intolerância.
    """
    __tablename__ = "araos_clinical_allergies"
    
    substance = Column(String(255), nullable=False)  # Penicilina, Amendoim, etc
    substance_category = Column(String(100), nullable=True)  # medication, food, environmental
    
    reaction = Column(Text, nullable=True)  # Urticária, Anafilaxia
    severity = Column(String(20), nullable=True)  # mild, moderate, severe, life_threatening
    
    onset_date = Column(DateTime(timezone=True), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        Index("ix_allergy_patient_current", "patient_id", "is_current"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "substance": self.substance,
            "reaction": self.reaction,
            "severity": self.severity,
            "verified": self.verified,
        }


class Procedure(ClinicalEntityBase):
    """
    Procedimento realizado.
    """
    __tablename__ = "araos_clinical_procedures"
    
    description = Column(Text, nullable=False)
    procedure_code = Column(String(20), nullable=True)  # CBHPM, TUSS, etc
    
    performed_at = Column(DateTime(timezone=True), nullable=True)
    performed_by = Column(String(36), nullable=True)
    
    result_summary = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("ix_procedure_patient_date", "patient_id", "performed_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "procedure_code": self.procedure_code,
            "performed_at": self.performed_at.isoformat() if self.performed_at else None,
        }


class RiskFactor(ClinicalEntityBase):
    """
    Fator de risco.
    """
    __tablename__ = "araos_clinical_risk_factors"
    
    factor_type = Column(String(50), nullable=False)
    # smoking, alcohol, sedentary, obesity, hypertension, diabetes, etc
    
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # mild, moderate, high
    
    is_active = Column(Boolean, nullable=False, default=True)
    identified_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("ix_risk_patient_active", "patient_id", "is_active"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "factor_type": self.factor_type,
            "description": self.description,
            "severity": self.severity,
            "is_active": self.is_active,
        }
