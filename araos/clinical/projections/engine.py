"""
AraOS Clinical — Projection Engine.

Consome eventos clínicos e atualiza o modelo de conhecimento.

Week 7A Hardening:
    - Usa ClinicalRepository (desacoplado do ORM)
    - IdempotencyTracker (exactly-once processing)
    - Invalida cache do Digital Twin após projeção
"""

from typing import Dict, Any, Optional

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
from ..entities.models import (
    Diagnosis, Medication, Allergy, Procedure, RiskFactor, ClinicalEntityStatus
)
from ..profile.models import ClinicalProfile
from ..timeline.models import TimelineEntry
from ..summary.engine import ClinicalSummaryEngine
from ..repository import ClinicalRepository
from ..idempotency import IdempotencyTracker
from ..cache import TwinCache


class ClinicalProjectionEngine:
    """
    Engine de projeções clínicas.
    
    Args:
        repository: ClinicalRepository para acesso a dados
        tracker: IdempotencyTracker para deduplicação
        cache: TwinCache para invalidação após projeção
    """
    
    def __init__(
        self,
        repository: ClinicalRepository,
        tracker: Optional[IdempotencyTracker] = None,
        cache: Optional[TwinCache] = None,
    ):
        self.repository = repository
        self.tracker = tracker
        self.cache = cache
    
    async def process(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """
        Processa um evento clínico com idempotência.
        
        Returns:
            Resultado da projeção
        """
        # 1. Idempotência
        if self.tracker:
            is_processed = await self.tracker.is_processed(event.event_id)
            if is_processed:
                return {"processed": False, "reason": "already_processed", "event_id": event.event_id}
        
        # 2. Validação de categoria
        if event.event_category != EventCategory.CLINICAL:
            return {"processed": False, "reason": "not_clinical"}
        
        # 3. Routing
        handler = self._get_handler(event.event_type)
        if not handler:
            return {"processed": False, "reason": "no_handler"}
        
        # 4. Execução
        try:
            result = handler(event)
        except Exception as e:
            if self.tracker:
                await self.tracker.mark_failed(event.event_id)
            raise
        
        # 5. Timeline
        await self._add_timeline_entry(event, result.get("entity_type"), result.get("entity_id"))
        
        # 6. Profile
        await self._update_profile(event.tenant_id, event.payload.get("patient_id"))
        
        # 7. Marcar como processado
        if self.tracker:
            await self.tracker.mark_processed(event.event_id)
        
        # 8. Invalidar cache do Digital Twin
        if self.cache:
            patient_id = event.payload.get("patient_id")
            if patient_id:
                await self.cache.invalidate(patient_id, event.tenant_id)
        
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
        
        self.repository.save_entity(diagnosis)
        
        return {
            "entity_type": "diagnosis",
            "entity_id": diagnosis.id,
            "action": "created",
        }
    
    def _handle_diagnosis_updated(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Atualiza diagnóstico existente."""
        data = event.payload
        diagnosis_id = data.get("diagnosis_id")
        
        # Nota: repository não tem get_by_id ainda; fallback para query direta
        # em implementação real, adicionar método ao repository
        diagnoses = self.repository.get_diagnoses(
            patient_id=data.get("patient_id", ""),
            tenant_id=event.tenant_id,
            active_only=False,
        )
        for old in diagnoses:
            if old.id == diagnosis_id:
                old.is_current = False
                old.status = data.get("status", old.status)
                self.repository.commit()
                break
        
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
        
        self.repository.save_entity(medication)
        
        return {
            "entity_type": "medication",
            "entity_id": medication.id,
            "action": "created",
        }
    
    def _handle_medication_stopped(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa MEDICATION_STOPPED."""
        data = event.payload
        medication_id = data.get("medication_id")
        
        meds = self.repository.get_medications(
            patient_id=data.get("patient_id", ""),
            tenant_id=event.tenant_id,
            active_only=False,
        )
        for med in meds:
            if med.id == medication_id:
                med.status = ClinicalEntityStatus.INACTIVE.value
                med.stopped_at = data.get("stopped_at")
                med.stopped_reason = data.get("reason")
                self.repository.commit()
                break
        
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
        
        self.repository.save_entity(allergy)
        
        return {
            "entity_type": "allergy",
            "entity_id": allergy.id,
            "action": "created",
        }
    
    def _handle_allergy_removed(self, event: EventEnvelopeV2) -> Dict[str, Any]:
        """Processa ALLERGY_REMOVED."""
        data = event.payload
        allergy_id = data.get("allergy_id")
        
        allergies = self.repository.get_allergies(
            patient_id=data.get("patient_id", ""),
            tenant_id=event.tenant_id,
            active_only=False,
        )
        for allergy in allergies:
            if allergy.id == allergy_id:
                allergy.status = ClinicalEntityStatus.INACTIVE.value
                self.repository.commit()
                break
        
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
        
        profile = self.repository.get_profile(event.tenant_id, patient_id)
        if not profile:
            profile = ClinicalProfile(
                tenant_id=event.tenant_id,
                patient_id=patient_id,
            )
            self.repository.save_entity(profile)
        
        profile.add_exam_result(exam_type, {
            "value": data.get("value"),
            "unit": data.get("unit"),
            "reference_range": data.get("reference_range"),
            "date": data.get("resulted_at"),
        })
        self.repository.update_profile(profile)
        
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
        
        self.repository.save_entity(procedure)
        
        return {
            "entity_type": "procedure",
            "entity_id": procedure.id,
            "action": "created",
        }
    
    # ─── Atualização de Profile e Timeline ───────────────────────────
    
    def _get_or_create_profile(self, tenant_id: str, patient_id: str) -> ClinicalProfile:
        """Busca ou cria ClinicalProfile."""
        profile = self.repository.get_profile(patient_id, tenant_id)
        
        if not profile:
            profile = ClinicalProfile(
                tenant_id=tenant_id,
                patient_id=patient_id,
            )
            self.repository.save_entity(profile)
        
        return profile
    
    async def _update_profile(self, tenant_id: str, patient_id: Optional[str]) -> None:
        """Atualiza ClinicalProfile a partir de entidades atuais."""
        if not patient_id:
            return
        
        profile = self._get_or_create_profile(tenant_id, patient_id)
        
        diagnoses = self.repository.get_diagnoses(patient_id, tenant_id, active_only=True)
        medications = self.repository.get_medications(patient_id, tenant_id, active_only=True)
        allergies = self.repository.get_allergies(patient_id, tenant_id, active_only=True)
        risk_factors = self.repository.get_risk_factors(patient_id, tenant_id, active_only=True)
        procedures = self.repository.get_procedures(patient_id, tenant_id, limit=10)
        
        profile.update_from_entities(
            diagnoses=[d.to_dict() for d in diagnoses],
            medications=[m.to_dict() for m in medications],
            allergies=[a.to_dict() for a in allergies],
            risk_factors=[r.to_dict() for r in risk_factors],
            procedures=[p.to_dict() for p in procedures],
        )
        
        engine = ClinicalSummaryEngine()
        summary = engine.generate(profile.to_dict())
        profile.last_summary = summary.text
        profile.summary_version = summary.version
        
        self.repository.update_profile(profile)
    
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
        
        self.repository.add_timeline_entry(entry)
