"""
AraOS Clinical — Clinical Profile.

Representação consolidada do estado clínico do paciente.

Atualizado automaticamente via ClinicalProjectionEngine a partir de:
    - DIAGNOSIS_ADDED / DIAGNOSIS_UPDATED
    - MEDICATION_PRESCRIBED / MEDICATION_STOPPED
    - ALLERGY_REGISTERED
    - EXAM_REQUESTED / EXAM_RESULTED
    - PROCEDURE realizado
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, Text, DateTime, JSON, Index, Integer
)

from araos.platform.tenant.models import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalProfile(Base):
    """
    Perfil clínico consolidado de um paciente.
    
    Uma única linha por paciente.
    Atualizada via projeções de eventos clínicos.
    
    Campos:
        patient_id: ID do paciente
        active_diagnoses: Lista de diagnósticos ativos
        active_medications: Lista de medicações ativas
        allergies: Lista de alergias
        risk_factors: Lista de fatores de risco
        procedures: Lista de procedimentos recentes
        family_history: História familiar estruturada
        social_history: História social estruturada
        last_exams: Últimos exames relevantes
        last_summary: Último resumo clínico gerado
        last_updated: Última atualização
    """
    __tablename__ = "araos_clinical_profiles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, unique=True, index=True)
    
    # Dados consolidados
    active_diagnoses = Column(JSON, nullable=False, default=list)
    active_medications = Column(JSON, nullable=False, default=list)
    allergies = Column(JSON, nullable=False, default=list)
    risk_factors = Column(JSON, nullable=False, default=list)
    procedures = Column(JSON, nullable=False, default=list)
    
    family_history = Column(JSON, nullable=True, default=dict)
    social_history = Column(JSON, nullable=True, default=dict)
    
    # Últimos exames relevantes (ex: HbA1c, Creatinina, etc)
    last_exams = Column(JSON, nullable=True, default=dict)
    
    # Resumo clínico gerado (rules-based)
    last_summary = Column(Text, nullable=True)
    summary_version = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=now_utc)
    last_updated = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
    
    # Metadados
    profile_metadata = Column(JSON, nullable=True, default=dict)
    
    __table_args__ = (
        Index("ix_clinical_profile_tenant", "tenant_id"),
    )
    
    def update_from_entities(
        self,
        diagnoses: Optional[List[Dict[str, Any]]] = None,
        medications: Optional[List[Dict[str, Any]]] = None,
        allergies: Optional[List[Dict[str, Any]]] = None,
        risk_factors: Optional[List[Dict[str, Any]]] = None,
        procedures: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Atualiza perfil a partir de entidades clínicas."""
        if diagnoses is not None:
            self.active_diagnoses = [d for d in diagnoses if d.get("status") in ("active", "chronic")]
        if medications is not None:
            self.active_medications = [m for m in medications if m.get("status") in ("active",)]
        if allergies is not None:
            self.allergies = allergies
        if risk_factors is not None:
            self.risk_factors = [r for r in risk_factors if r.get("is_active", True)]
        if procedures is not None:
            self.procedures = procedures[:10]  # Mantém últimos 10
        
        self.last_updated = now_utc()
    
    def add_exam_result(self, exam_type: str, result: Dict[str, Any]) -> None:
        """Adiciona resultado de exame."""
        if self.last_exams is None:
            self.last_exams = {}
        self.last_exams[exam_type] = result
        self.last_updated = now_utc()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "active_diagnoses": self.active_diagnoses,
            "active_medications": self.active_medications,
            "allergies": self.allergies,
            "risk_factors": self.risk_factors,
            "procedures": self.procedures,
            "family_history": self.family_history,
            "social_history": self.social_history,
            "last_exams": self.last_exams,
            "last_summary": self.last_summary,
            "summary_version": self.summary_version,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
