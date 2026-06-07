"""
AraOS Clinical — Patient Digital Twin.

Representação digital consolidada do paciente.

Composto por:
    1. Dados estruturados (ClinicalProfile)
    2. Timeline clínica (ClinicalTimeline)
    3. Eventos clínicos (Clinical Event Stream)
    4. Resumo clínico (ClinicalSummaryEngine)
    5. Grafo clínico (ClinicalGraph)

NÃO contém IA.
É a fundação sobre a qual a inteligência será construída.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ..profile.models import ClinicalProfile
from ..timeline.models import ClinicalTimeline, TimelineEntry
from ..graph.models import ClinicalGraph
from ..summary.engine import SummaryResult


@dataclass
class PatientDigitalTwin:
    """
    Digital Twin de um paciente.
    
    Atributos:
        patient_id: ID do paciente
        tenant_id: ID da organização
        profile: Perfil clínico consolidado
        timeline: Timeline clínica
        graph: Grafo clínico conceitual
        summary: Último resumo gerado
        metadata: Metadados adicionais
    """
    
    patient_id: str
    tenant_id: str
    profile: Optional[ClinicalProfile] = None
    timeline: Optional[ClinicalTimeline] = None
    graph: Optional[ClinicalGraph] = None
    summary: Optional[SummaryResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def active_diagnoses(self) -> List[Dict[str, Any]]:
        """Retorna diagnósticos ativos."""
        if self.profile:
            return self.profile.active_diagnoses or []
        return []
    
    @property
    def active_medications(self) -> List[Dict[str, Any]]:
        """Retorna medicações ativas."""
        if self.profile:
            return self.profile.active_medications or []
        return []
    
    @property
    def allergies(self) -> List[Dict[str, Any]]:
        """Retorna alergias."""
        if self.profile:
            return self.profile.allergies or []
        return []
    
    @property
    def risk_factors(self) -> List[Dict[str, Any]]:
        """Retorna fatores de risco."""
        if self.profile:
            return self.profile.risk_factors or []
        return []
    
    def get_timeline_entries(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[TimelineEntry]:
        """Retorna entradas da timeline."""
        if self.timeline:
            return self.timeline.get_entries(entity_type=entity_type, limit=limit)
        return []
    
    def has_severe_allergy(self) -> bool:
        """Verifica se paciente tem alergia grave."""
        return any(
            a.get("severity") in ("severe", "life_threatening")
            for a in self.allergies
        )
    
    def has_chronic_condition(self) -> bool:
        """Verifica se paciente tem condição crônica."""
        return any(
            d.get("is_chronic") or d.get("status") == "chronic"
            for d in self.active_diagnoses
        )
    
    def get_medication_names(self) -> List[str]:
        """Retorna nomes das medicações ativas."""
        return [m.get("name", "") for m in self.active_medications if m.get("name")]
    
    def get_icd10_codes(self) -> List[str]:
        """Retorna códigos ICD-10 ativos."""
        return [
            d.get("icd10_code", "")
            for d in self.active_diagnoses
            if d.get("icd10_code")
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa twin para dict."""
        return {
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "profile": self.profile.to_dict() if self.profile else None,
            "graph": self.graph.to_dict() if self.graph else None,
            "summary": {
                "text": self.summary.text if self.summary else None,
                "warnings": self.summary.warnings if self.summary else [],
                "generated_at": self.summary.generated_at if self.summary else None,
            },
            "metadata": self.metadata,
        }


class PatientDigitalTwinBuilder:
    """
    Builder para construir o Digital Twin de um paciente.
    
    Uso:
        builder = PatientDigitalTwinBuilder(db_session, patient_id, tenant_id)
        twin = await builder.build()
    """
    
    def __init__(self, db_session, patient_id: str, tenant_id: str):
        self.db = db_session
        self.patient_id = patient_id
        self.tenant_id = tenant_id
    
    async def build(self) -> PatientDigitalTwin:
        """Constrói Digital Twin completo."""
        from ..profile.models import ClinicalProfile
        from ..timeline.models import ClinicalTimeline
        from ..graph.models import ClinicalGraphBuilder
        from ..summary.engine import ClinicalSummaryEngine
        
        # 1. Buscar perfil
        profile = self.db.query(ClinicalProfile).filter(
            ClinicalProfile.patient_id == self.patient_id,
            ClinicalProfile.tenant_id == self.tenant_id,
        ).first()
        
        # 2. Construir timeline
        timeline = ClinicalTimeline(self.db, self.patient_id, self.tenant_id)
        
        # 3. Construir grafo
        graph_builder = ClinicalGraphBuilder(self.patient_id)
        if profile:
            graph_builder.add_diagnoses(profile.active_diagnoses or [])
            graph_builder.add_medications(profile.active_medications or [])
            graph_builder.add_allergies(profile.allergies or [])
        graph = graph_builder.build()
        
        # 4. Gerar resumo
        summary = None
        if profile:
            engine = ClinicalSummaryEngine()
            summary = engine.generate(profile.to_dict())
        
        return PatientDigitalTwin(
            patient_id=self.patient_id,
            tenant_id=self.tenant_id,
            profile=profile,
            timeline=timeline,
            graph=graph,
            summary=summary,
        )
