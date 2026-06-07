"""
AraOS Clinical — Clinical Timeline.

Representação longitudinal da história clínica.

Baseada em eventos clínicos (Week 3):
    DIAGNOSIS_ADDED
    MEDICATION_PRESCRIBED
    EXAM_REQUESTED / EXAM_RESULTED
    ALLERGY_REGISTERED
    PROCEDURE realizado

Exemplo:
    2026-01: Diagnóstico HAS
    2026-03: Prescrição Losartana
    2026-04: HbA1c 7,3%
    2026-05: Ajuste terapêutico
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column, String, Text, DateTime, JSON, Index
)

from araos.platform.tenant.models import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class TimelineEntry(Base):
    """
    Entrada individual da timeline clínica.
    
    Cada entrada representa um evento clínico na vida do paciente.
    """
    __tablename__ = "araos_clinical_timeline_entries"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    
    # Evento que originou
    event_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(20), nullable=False)
    
    # Conteúdo
    title = Column(String(255), nullable=False)  # "Hipertensão diagnosticada"
    description = Column(Text, nullable=True)    # "HAS como diagnóstico primário"
    
    # Data do evento clínico (pode ser diferente da data de registro)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Dados estruturados
    entity_type = Column(String(50), nullable=True)  # diagnosis, medication, exam, etc
    entity_id = Column(String(36), nullable=True)
    entity_data = Column(JSON, nullable=True, default=dict)
    
    # Contexto
    recorded_by = Column(String(36), nullable=True)
    source = Column(String(50), nullable=True)  # core, voice, smart_flow, concierge
    
    created_at = Column(DateTime(timezone=True), default=now_utc)
    
    __table_args__ = (
        Index("ix_timeline_patient_date", "patient_id", "event_date"),
        Index("ix_timeline_event", "event_id"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "entity_type": self.entity_type,
            "entity_data": self.entity_data,
            "source": self.source,
        }


class ClinicalTimeline:
    """
    Timeline clínica de um paciente.
    
    Não é um modelo — é uma view/agregação sobre TimelineEntry.
    """
    
    def __init__(self, db_session, patient_id: str, tenant_id: str):
        self.db = db_session
        self.patient_id = patient_id
        self.tenant_id = tenant_id
    
    def get_entries(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[TimelineEntry]:
        """Retorna entradas da timeline."""
        query = self.db.query(TimelineEntry).filter(
            TimelineEntry.patient_id == self.patient_id,
            TimelineEntry.tenant_id == self.tenant_id,
        )
        
        if from_date:
            query = query.filter(TimelineEntry.event_date >= from_date)
        if to_date:
            query = query.filter(TimelineEntry.event_date <= to_date)
        if entity_type:
            query = query.filter(TimelineEntry.entity_type == entity_type)
        
        return query.order_by(TimelineEntry.event_date.desc()).limit(limit).all()
    
    def get_summary_by_year(self) -> Dict[str, List[Dict[str, Any]]]:
        """Agrupa entradas por ano."""
        entries = self.get_entries(limit=1000)
        
        result: Dict[str, List[Dict[str, Any]]] = {}
        for entry in entries:
            year = entry.event_date.year if entry.event_date else "unknown"
            key = str(year)
            if key not in result:
                result[key] = []
            result[key].append(entry.to_dict())
        
        return result
    
    def get_medication_history(self) -> List[TimelineEntry]:
        """Retorna histórico de medicações."""
        return self.get_entries(entity_type="medication", limit=100)
    
    def get_diagnosis_history(self) -> List[TimelineEntry]:
        """Retorna histórico de diagnósticos."""
        return self.get_entries(entity_type="diagnosis", limit=100)
