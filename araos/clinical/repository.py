"""
AraOS Clinical — Repository Pattern.

Desacopla o domínio clínico do SQLAlchemy ORM.
"""

from typing import Optional, List, Any
from abc import ABC, abstractmethod


class ClinicalRepository(ABC):
    """
    Contrato para acesso a dados clínicos.
    
    Implementações:
        - SqlAlchemyClinicalRepository: produção (SQLAlchemy Session)
        - InMemoryClinicalRepository: testes/demos
    """
    
    @abstractmethod
    def get_profile(self, patient_id: str, tenant_id: str) -> Optional[Any]:
        """Busca ClinicalProfile por paciente."""
        ...
    
    @abstractmethod
    def get_diagnoses(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        ...
    
    @abstractmethod
    def get_medications(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        ...
    
    @abstractmethod
    def get_allergies(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        ...
    
    @abstractmethod
    def get_risk_factors(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        ...
    
    @abstractmethod
    def get_procedures(self, patient_id: str, tenant_id: str, limit: int = 10) -> List[Any]:
        ...
    
    @abstractmethod
    def save_entity(self, entity: Any) -> None:
        """Persiste uma entidade clínica."""
        ...
    
    @abstractmethod
    def update_profile(self, profile: Any) -> None:
        ...
    
    @abstractmethod
    def add_timeline_entry(self, entry: Any) -> None:
        ...
    
    @abstractmethod
    def commit(self) -> None:
        ...


class SqlAlchemyClinicalRepository(ClinicalRepository):
    """
    Implementação com SQLAlchemy Session.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_profile(self, patient_id: str, tenant_id: str) -> Optional[Any]:
        from .profile.models import ClinicalProfile
        return self.db.query(ClinicalProfile).filter(
            ClinicalProfile.patient_id == patient_id,
            ClinicalProfile.tenant_id == tenant_id,
        ).first()
    
    def get_diagnoses(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        from .entities.models import Diagnosis
        q = self.db.query(Diagnosis).filter(
            Diagnosis.patient_id == patient_id,
            Diagnosis.tenant_id == tenant_id,
        )
        if active_only:
            q = q.filter(Diagnosis.is_current == True)
        return q.all()
    
    def get_medications(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        from .entities.models import Medication, ClinicalEntityStatus
        q = self.db.query(Medication).filter(
            Medication.patient_id == patient_id,
            Medication.tenant_id == tenant_id,
        )
        if active_only:
            q = q.filter(Medication.status == ClinicalEntityStatus.ACTIVE.value)
        return q.all()
    
    def get_allergies(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        from .entities.models import Allergy, ClinicalEntityStatus
        q = self.db.query(Allergy).filter(
            Allergy.patient_id == patient_id,
            Allergy.tenant_id == tenant_id,
        )
        if active_only:
            q = q.filter(Allergy.status == ClinicalEntityStatus.ACTIVE.value)
        return q.all()
    
    def get_risk_factors(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        from .entities.models import RiskFactor
        q = self.db.query(RiskFactor).filter(
            RiskFactor.patient_id == patient_id,
            RiskFactor.tenant_id == tenant_id,
        )
        if active_only:
            q = q.filter(RiskFactor.is_active == True)
        return q.all()
    
    def get_procedures(self, patient_id: str, tenant_id: str, limit: int = 10) -> List[Any]:
        from .entities.models import Procedure
        return self.db.query(Procedure).filter(
            Procedure.patient_id == patient_id,
            Procedure.tenant_id == tenant_id,
        ).order_by(Procedure.performed_at.desc()).limit(limit).all()
    
    def save_entity(self, entity: Any) -> None:
        self.db.add(entity)
        self.db.commit()
    
    def update_profile(self, profile: Any) -> None:
        self.db.merge(profile)
        self.db.commit()
    
    def add_timeline_entry(self, entry: Any) -> None:
        self.db.add(entry)
        self.db.commit()
    
    def commit(self) -> None:
        self.db.commit()


class InMemoryClinicalRepository(ClinicalRepository):
    """
    Implementação em memória para testes/demos.
    """
    
    def __init__(self):
        self.profiles: dict = {}
        self.diagnoses: dict = {}
        self.medications: dict = {}
        self.allergies: dict = {}
        self.risk_factors: dict = {}
        self.procedures: dict = {}
        self.timeline_entries: list = []
    
    def _key(self, patient_id: str, tenant_id: str) -> str:
        return f"{tenant_id}:{patient_id}"
    
    def get_profile(self, patient_id: str, tenant_id: str) -> Optional[Any]:
        return self.profiles.get(self._key(patient_id, tenant_id))
    
    def get_diagnoses(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        items = self.diagnoses.get(self._key(patient_id, tenant_id), [])
        if active_only:
            return [d for d in items if getattr(d, "is_current", True)]
        return items
    
    def get_medications(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        items = self.medications.get(self._key(patient_id, tenant_id), [])
        if active_only:
            from .entities.models import ClinicalEntityStatus
            return [m for m in items if getattr(m, "status", ClinicalEntityStatus.ACTIVE.value) == ClinicalEntityStatus.ACTIVE.value]
        return items
    
    def get_allergies(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        items = self.allergies.get(self._key(patient_id, tenant_id), [])
        if active_only:
            from .entities.models import ClinicalEntityStatus
            return [a for a in items if getattr(a, "status", ClinicalEntityStatus.ACTIVE.value) == ClinicalEntityStatus.ACTIVE.value]
        return items
    
    def get_risk_factors(self, patient_id: str, tenant_id: str, active_only: bool = True) -> List[Any]:
        items = self.risk_factors.get(self._key(patient_id, tenant_id), [])
        if active_only:
            return [r for r in items if getattr(r, "is_active", True)]
        return items
    
    def get_procedures(self, patient_id: str, tenant_id: str, limit: int = 10) -> List[Any]:
        items = self.procedures.get(self._key(patient_id, tenant_id), [])
        return sorted(items, key=lambda p: getattr(p, "performed_at", None) or "", reverse=True)[:limit]
    
    def save_entity(self, entity: Any) -> None:
        key = self._key(getattr(entity, "patient_id", ""), getattr(entity, "tenant_id", ""))
        if hasattr(entity, "__tablename__"):
            if "diagnos" in entity.__tablename__:
                self.diagnoses.setdefault(key, []).append(entity)
            elif "medic" in entity.__tablename__:
                self.medications.setdefault(key, []).append(entity)
            elif "allerg" in entity.__tablename__:
                self.allergies.setdefault(key, []).append(entity)
            elif "risk" in entity.__tablename__:
                self.risk_factors.setdefault(key, []).append(entity)
            elif "procedure" in entity.__tablename__:
                self.procedures.setdefault(key, []).append(entity)
        # Para entidades sem __tablename__, inferir pela classe
        name = entity.__class__.__name__.lower()
        if "diagnos" in name:
            self.diagnoses.setdefault(key, []).append(entity)
        elif "medic" in name:
            self.medications.setdefault(key, []).append(entity)
        elif "allerg" in name:
            self.allergies.setdefault(key, []).append(entity)
        elif "risk" in name:
            self.risk_factors.setdefault(key, []).append(entity)
        elif "procedure" in name:
            self.procedures.setdefault(key, []).append(entity)
        elif "profile" in name:
            self.profiles[key] = entity
    
    def update_profile(self, profile: Any) -> None:
        key = self._key(profile.patient_id, profile.tenant_id)
        self.profiles[key] = profile
    
    def add_timeline_entry(self, entry: Any) -> None:
        self.timeline_entries.append(entry)
    
    def commit(self) -> None:
        pass
