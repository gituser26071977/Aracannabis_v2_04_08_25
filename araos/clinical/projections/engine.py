"""
AraOS Clinical — Projection Engine.

Consome eventos clínicos da Week 3 e atualiza o modelo de conhecimento.

Eventos → Entidades:
    DIAGNOSIS_ADDED → Diagnosis
    MEDICATION_PRESCRIBED → Medication
    ALLERGY_REGISTERED → Allergy
    EXAM_RESULTED → atualiza last_exams
    PROCEDURE realizado → Procedure

Entidades → Profile:
    Sempre que entidades mudam, ClinicalProfile é atualizado.

Profile → Summary:
    Sempre que profile muda, resumo é regenerado.
"""

from typing import Dict, Any, Optional

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
from ..entities.models import (
    Diagnosis, Medication, Allergy, Procedure, RiskFactor, ClinicalEntityStatus
)
from ..profile.models import ClinicalProfile
from ..timeline.models import TimelineEntry
from ..summary.engine import ClinicalSummaryEngine


class ClinicalProjectionEngine:
    """
    Engine de projeções clínicas.
    
    Consome eventos e projeta estado atualizado.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def process(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """
        Processa um evento clínico.
        
        Returns:
            Resultado da projeção
        """
        if event.event_category != EventCategory.CLINICAL:
            return {"processed": False, "reason": "not_clinical"}
        
        handler = self._get_handler(event.event_type)
        if not handler:
            return {"processed": False, "reason": "no_handler"}
        
        result = handler(event)
        
        # Atualizar timeline
        await self._add_timeline_entry(event, result.get("entity_type"), result.get("entity_id"))
        
        # Atualizar perfil
        await self._update_profile(event.tenant_id, event.payload.get("patient_id"))
        
        return {"processed": True, **result}
    
    def _get_handler(self, event_type: str):
        """Retorna handler para tipo de evento."""
        handlers = {
            "DIAGNOSIS_ADDED": self._handle_diagnosis_added,
            "DIAGNOSIS_UPDATED": self._handle_diagnosis_updated,
            "MEDICATION_PRESCRIBED": self._handle_medication_prescribed,
            "MEDICATION_STOPPED": self._handle_medication_stopped,
            "ALLERGY_REGISTERED": self._handle_allergy_registered,
            "ALLERGY_REMOVED": self._handle_allergy_removed,
            "EXAM_RESULTED": self._handle_exam_resulted,
            "CLINICAL_NOTE_CREATED": self._handle_clinical_note,
            "PROCEDURE_APPLIED": self._handle_procedure,
        }
        return handlers.get(event_type)
    
    # ─── Handlers ────────────────────────────────────────────────────
    
    def _handle_diagnosis_added(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa DIAGNOSIS_ADDED."""
        data = event.payload
        
        diagnosis = Diagnosis(
            tenant_id=event.tenant_id,
            patient_id=data.get("patient_id"),
            description=data.get("description", ""),
            icd10_code=data.get("icd10_code"),
            snomed_code=data.get("snomed_code"),
            onset_date=data.get("onset_date"),
            is_primary=data.get("is_primary", False),
            is_chronic=data.get("is_chronic", False),
            recorded_by=event.actor_id,
            status=ClinicalEntityStatus.ACTIVE.value,
        )
        
        self.db.add(diagnosis)
        self.db.commit()
        
        return {
            "entity_type": "diagnosis",
            "entity_id": diagnosis.id,
            "action": "created",
        }
    
    def _handle_diagnosis_updated(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Atualiza diagnóstico existente e marca anterior como não atual."""
        data = event.payload
        diagnosis_id = data.get("diagnosis_id")
        
        old = self.db.query(Diagnosis).filter(Diagnosis.id == diagnosis_id).first()
        if old:
            old.is_current = False
            old.status = data.get("status", old.status)
            self.db.commit()
        
        return {
            "entity_type": "diagnosis",
            "entity_id": diagnosis_id,
            "action": "updated",
        }
    
    def _handle_medication_prescribed(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa MEDICATION_PRESCRIBED."""
        data = event.payload
        
        medication = Medication(
            tenant_id=event.tenant_id,
            patient_id=data.get("patient_id"),
            name=data.get("name", ""),
            generic_name=data.get("generic_name"),
            dosage=data.get("dosage"),
            frequency=data.get("frequency"),
            route=data.get("route"),
            prescribed_by=event.actor_id,
            prescribed_at=data.get("prescribed_at"),
            recorded_by=event.actor_id,
        )
        
        self.db.add(medication)
        self.db.commit()
        
        return {
            "entity_type": "medication",
            "entity_id": medication.id,
            "action": "created",
        }
    
    def _handle_medication_stopped(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa MEDICATION_STOPPED."""
        data = event.payload
        medication_id = data.get("medication_id")
        
        med = self.db.query(Medication).filter(Medication.id == medication_id).first()
        if med:
            med.status = ClinicalEntityStatus.INACTIVE.value
            med.stopped_at = data.get("stopped_at")
            med.stopped_reason = data.get("reason")
            self.db.commit()
        
        return {
            "entity_type": "medication",
            "entity_id": medication_id,
            "action": "stopped",
        }
    
    def _handle_allergy_registered(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa ALLERGY_REGISTERED."""
        data = event.payload
        
        allergy = Allergy(
            tenant_id=event.tenant_id,
            patient_id=data.get("patient_id"),
            substance=data.get("substance", ""),
            substance_category=data.get("substance_category"),
            reaction=data.get("reaction"),
            severity=data.get("severity"),
            recorded_by=event.actor_id,
        )
        
        self.db.add(allergy)
        self.db.commit()
        
        return {
            "entity_type": "allergy",
            "entity_id": allergy.id,
            "action": "created",
        }
    
    def _handle_allergy_removed(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa ALLERGY_REMOVED."""
        data = event.payload
        allergy_id = data.get("allergy_id")
        
        allergy = self.db.query(Allergy).filter(Allergy.id == allergy_id).first()
        if allergy:
            allergy.status = ClinicalEntityStatus.INACTIVE.value
            self.db.commit()
        
        return {
            "entity_type": "allergy",
            "entity_id": allergy_id,
            "action": "removed",
        }
    
    def _handle_exam_resulted(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa EXAM_RESULTED."""
        data = event.payload
        patient_id = data.get("patient_id")
        exam_type = data.get("exam_type")
        
        # Atualizar last_exams no perfil
        profile = self._get_or_create_profile(event.tenant_id, patient_id)
        profile.add_exam_result(exam_type, {
            "value": data.get("value"),
            "unit": data.get("unit"),
            "reference_range": data.get("reference_range"),
            "date": data.get("resulted_at"),
        })
        self.db.commit()
        
        return {
            "entity_type": "exam",
            "action": "resulted",
        }
    
    def _handle_clinical_note(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa CLINICAL_NOTE_CREATED."""
        return {
            "entity_type": "clinical_note",
            "action": "created",
        }
    
    def _handle_procedure(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa PROCEDURE_APPLIED."""
        data = event.payload
        
        procedure = Procedure(
            tenant_id=event.tenant_id,
            patient_id=data.get("patient_id"),
            description=data.get("description", ""),
            procedure_code=data.get("procedure_code"),
            performed_at=data.get("performed_at"),
            performed_by=event.actor_id,
            recorded_by=event.actor_id,
        )
        
        self.db.add(procedure)
        self.db.commit()
        
        return {
            "entity_type": "procedure",
            "entity_id": procedure.id,
            "action": "created",
        }
    
    # ─── Atualização de Profile e Timeline ───────────────────────────
    
    def _get_or_create_profile(self, tenant_id: str, patient_id: str) -> ClinicalProfile:
        """Busca ou cria ClinicalProfile."""
        profile = self.db.query(ClinicalProfile).filter(
            ClinicalProfile.tenant_id == tenant_id,
            ClinicalProfile.patient_id == patient_id,
        ).first()
        
        if not profile:
            profile = ClinicalProfile(
                tenant_id=tenant_id,
                patient_id=patient_id,
            )
            self.db.add(profile)
            self.db.commit()
        
        return profile
    
    async def _update_profile(self, tenant_id: str, patient_id: Optional[str]) -> None:
        """Atualiza ClinicalProfile a partir de entidades atuais."""
        if not patient_id:
            return
        
        profile = self._get_or_create_profile(tenant_id, patient_id)
        
        # Buscar entidades atuais
        diagnoses = self.db.query(Diagnosis).filter(
            Diagnosis.tenant_id == tenant_id,
            Diagnosis.patient_id == patient_id,
            Diagnosis.is_current == True,
        ).all()
        
        medications = self.db.query(Medication).filter(
            Medication.tenant_id == tenant_id,
            Medication.patient_id == patient_id,
            Medication.status == ClinicalEntityStatus.ACTIVE.value,
        ).all()
        
        allergies = self.db.query(Allergy).filter(
            Allergy.tenant_id == tenant_id,
            Allergy.patient_id == patient_id,
            Allergy.status == ClinicalEntityStatus.ACTIVE.value,
        ).all()
        
        risk_factors = self.db.query(RiskFactor).filter(
            RiskFactor.tenant_id == tenant_id,
            RiskFactor.patient_id == patient_id,
            RiskFactor.is_active == True,
        ).all()
        
        procedures = self.db.query(Procedure).filter(
            Procedure.tenant_id == tenant_id,
            Procedure.patient_id == patient_id,
        ).order_by(Procedure.performed_at.desc()).limit(10).all()
        
        # Atualizar profile
        profile.update_from_entities(
            diagnoses=[d.to_dict() for d in diagnoses],
            medications=[m.to_dict() for m in medications],
            allergies=[a.to_dict() for a in allergies],
            risk_factors=[r.to_dict() for r in risk_factors],
            procedures=[p.to_dict() for p in procedures],
        )
        
        # Regenerar resumo
        engine = ClinicalSummaryEngine()
        summary = engine.generate(profile.to_dict())
        profile.last_summary = summary.text
        profile.summary_version = summary.version
        
        self.db.commit()
    
    async def _add_timeline_entry(
        self,
        event: EventEnvelopeV2,
        entity_type: Optional[str],
        entity_id: Optional[str],
    ) -> None:
        """Adiciona entrada na timeline clínica."""
        patient_id = event.payload.get("patient_id")
        if not patient_id:
            return
        
        # Título baseado no tipo de evento
        title_map = {
            "DIAGNOSIS_ADDED": "Diagnóstico registrado",
            "MEDICATION_PRESCRIBED": "Medicação prescrita",
            "ALLERGY_REGISTERED": "Alergia registrada",
            "EXAM_RESULTED": "Resultado de exame",
            "CLINICAL_NOTE_CREATED": "Evolução clínica",
            "PROCEDURE_APPLIED": "Procedimento realizado",
        }
        
        from datetime import datetime
        entry = TimelineEntry(
            tenant_id=event.tenant_id,
            patient_id=patient_id,
            event_id=event.event_id,
            event_type=event.event_type,
            event_category=event.event_category.value,
            title=title_map.get(event.event_type, event.event_type),
            description=event.payload.get("description", ""),
            event_date=datetime.fromtimestamp(event.timestamp / 1000),
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=event.payload,
            recorded_by=event.actor_id,
            source=event.metadata.get("source", "unknown"),
        )
        
        self.db.add(entry)
        self.db.commit()
