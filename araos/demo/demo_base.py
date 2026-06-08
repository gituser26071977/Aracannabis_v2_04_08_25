"""
AraOS Demo — Base Environment.

Configura ambiente completo para demonstrações:
    - SQLite em memória
    - Tenant, Organization, Clinic
    - Professional, User
    - Patient (como entidade clínica)
    - Event Bus em memória
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from araos.platform.tenant.models import (
    Base, Organization, Clinic, Professional, User, ServiceAccount
)
from araos.clinical.entities.models import (
    Diagnosis, Medication, Allergy, Procedure, RiskFactor
)
from araos.clinical.profile.models import ClinicalProfile
from araos.clinical.timeline.models import TimelineEntry


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class InMemoryEventBus:
    """Event Bus em memória para demonstrações."""
    
    def __init__(self):
        self.events: list = []
        self.subscribers: Dict[str, list] = {}
    
    async def publish(self, event) -> str:
        self.events.append(event)
        for handler in self.subscribers.get(event.event_type, []):
            try:
                await handler(event)
            except Exception:
                pass
        return event.event_id
    
    async def subscribe(self, event_types, group, handler) -> None:
        for et in event_types:
            if et not in self.subscribers:
                self.subscribers[et] = []
            self.subscribers[et].append(handler)
    
    def get_events(self, event_type: Optional[str] = None) -> list:
        if event_type:
            return [e for e in self.events if e.event_type == event_type]
        return self.events
    
    def get_correlation_chain(self, correlation_id: str) -> list:
        return [e for e in self.events if getattr(e, 'correlation_id', None) == correlation_id]
    
    def clear(self) -> None:
        self.events.clear()
        self.subscribers.clear()


class DemoEnvironment:
    """
    Ambiente completo para demonstrações.
    
    Uso:
        env = DemoEnvironment()
        env.setup()
        
        # Usar em fluxos
        env.db.query(ClinicalProfile).filter(...)
        await env.event_bus.publish(event)
    """
    
    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.db: Optional[Session] = None
        self.event_bus = InMemoryEventBus()
        
        # IDs fixos para demo
        self.tenant_id = "demo_org_001"
        self.clinic_id = "demo_clinic_001"
        self.patient_id = "demo_patient_001"
        self.doctor_id = "demo_doctor_001"
        self.nurse_id = "demo_nurse_001"
    
    def setup(self) -> "DemoEnvironment":
        """Configura ambiente completo."""
        # Criar tabelas
        Base.metadata.create_all(self.engine)
        self.db = self.Session()
        
        # Criar organização
        org = Organization(
            id=self.tenant_id,
            name="Clínica Demo AraOS",
            slug="demo-clinica",
            plan="enterprise",
            status="active",
            settings={"features": ["voice", "concierge", "smart_flow"]},
        )
        self.db.add(org)
        
        # Criar clínica
        clinic = Clinic(
            id=self.clinic_id,
            organization_id=self.tenant_id,
            name="Unidade Centro",
            timezone="America/Sao_Paulo",
            active=True,
        )
        self.db.add(clinic)
        
        # Criar médico
        doctor = Professional(
            id=self.doctor_id,
            organization_id=self.tenant_id,
            full_name="Dr. Anderson Silva",
            email="dr.anderson@demo.com",
            specialty="Clínica Geral",
            professional_registry="CRM-SP 123456",
            clinic_ids=[self.clinic_id],
        )
        self.db.add(doctor)
        
        # Criar enfermeira
        nurse = Professional(
            id=self.nurse_id,
            organization_id=self.tenant_id,
            full_name="Enf. Maria Santos",
            email="maria@demo.com",
            specialty="Enfermagem",
            clinic_ids=[self.clinic_id],
        )
        self.db.add(nurse)
        
        # Criar usuário admin
        admin = User(
            id="demo_admin_001",
            organization_id=self.tenant_id,
            email="admin@demo.com",
            password_hash="hashed",
            full_name="Administrador Demo",
            roles=["admin"],
            clinic_ids=[self.clinic_id],
            active=True,
        )
        self.db.add(admin)
        
        # Criar ClinicalProfile para o paciente demo
        profile = ClinicalProfile(
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            active_diagnoses=[],
            active_medications=[],
            allergies=[],
            risk_factors=[],
            procedures=[],
        )
        self.db.add(profile)
        
        self.db.commit()
        return self
    
    def create_patient_with_data(self) -> Dict[str, Any]:
        """Cria paciente com dados clínicos iniciais."""
        # Diagnóstico
        diag = Diagnosis(
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            description="Hipertensão Arterial Sistêmica",
            icd10_code="I10",
            is_primary=True,
            is_chronic=True,
            recorded_by=self.doctor_id,
        )
        self.db.add(diag)
        
        # Medicação
        med = Medication(
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            name="Losartana",
            generic_name="Losartan",
            dosage="50mg",
            frequency="1x ao dia",
            route="oral",
            prescribed_by=self.doctor_id,
        )
        self.db.add(med)
        
        # Alergia
        allergy = Allergy(
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            substance="Penicilina",
            reaction="Urticária",
            severity="moderate",
            recorded_by=self.nurse_id,
        )
        self.db.add(allergy)
        
        # Fator de risco
        risk = RiskFactor(
            tenant_id=self.tenant_id,
            patient_id=self.patient_id,
            factor_type="sedentarismo",
            severity="moderate",
            is_active=True,
        )
        self.db.add(risk)
        
        # Atualizar profile
        profile = self.db.query(ClinicalProfile).filter(
            ClinicalProfile.patient_id == self.patient_id
        ).first()
        profile.update_from_entities(
            diagnoses=[diag.to_dict()],
            medications=[med.to_dict()],
            allergies=[allergy.to_dict()],
            risk_factors=[risk.to_dict()],
        )
        
        self.db.commit()
        
        return {
            "patient_id": self.patient_id,
            "diagnosis_id": diag.id,
            "medication_id": med.id,
            "allergy_id": allergy.id,
            "risk_factor_id": risk.id,
        }
    
    def teardown(self) -> None:
        """Limpa ambiente."""
        if self.db:
            self.db.close()
        self.event_bus.clear()
    
    def print_header(self, title: str) -> None:
        """Imprime cabeçalho formatado."""
        print()
        print("=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_section(self, title: str) -> None:
        """Imprime seção formatada."""
        print()
        print(f"── {title} ")
