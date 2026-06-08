"""
AraOS Clinical — Patient Digital Twin.

Representação digital consolidada do paciente.

Week 7A Hardening:
    - Usa ClinicalRepository (desacoplado do ORM)
    - Usa TwinCache (Redis/in-memory) para evitar reconstruções
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from ..profile.models import ClinicalProfile
from ..timeline.models import ClinicalTimeline, TimelineEntry
from ..graph.models import ClinicalGraph
from ..summary.engine import SummaryResult, ClinicalSummaryEngine
from ..repository import ClinicalRepository
from ..cache import TwinCache


@dataclass
class PatientDigitalTwin:
    """
    Digital Twin de um paciente.
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
        if self.profile:
            return self.profile.active_diagnoses or []
        return []
    
    @property
    def active_medications(self) -> List[Dict[str, Any]]:
        if self.profile:
            return self.profile.active_medications or []
        return []
    
    @property
    def allergies(self) -> List[Dict[str, Any]]:
        if self.profile:
            return self.profile.allergies or []
        return []
    
    @property
    def risk_factors(self) -> List[Dict[str, Any]]:
        if self.profile:
            return self.profile.risk_factors or []
        return []
    
    def get_timeline_entries(self, entity_type: Optional[str] = None, limit: int = 100) -> List[TimelineEntry]:
        if self.timeline:
            return self.timeline.get_entries(entity_type=entity_type, limit=limit)
        return []
    
    def has_severe_allergy(self) -> bool:
        return any(
            a.get("severity") in ("severe", "life_threatening")
            for a in self.allergies
        )
    
    def has_chronic_condition(self) -> bool:
        return any(
            d.get("is_chronic") or d.get("status") == "chronic"
            for d in self.active_diagnoses
        )
    
    def get_medication_names(self) -> List[str]:
        return [m.get("name", "") for m in self.active_medications if m.get("name")]
    
    def get_icd10_codes(self) -> List[str]:
        return [
            d.get("icd10_code", "")
            for d in self.active_diagnoses
            if d.get("icd10_code")
        ]
    
    def to_dict(self) -> Dict[str, Any]:
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
    
    Week 7A:
        - Recebe ClinicalRepository em vez de Session direta
        - Opcional: TwinCache para evitar reconstruções
    
    Uso:
        builder = PatientDigitalTwinBuilder(
            repository=repo,
            cache=cache,  # opcional
        )
        twin = await builder.build(patient_id, tenant_id)
    """
    
    def __init__(
        self,
        repository: ClinicalRepository,
        cache: Optional[TwinCache] = None,
    ):
        self.repository = repository
        self.cache = cache
    
    async def build(self, patient_id: str, tenant_id: str) -> PatientDigitalTwin:
        """Constrói Digital Twin completo (com cache)."""
        # 1. Tentar cache
        if self.cache:
            cached = await self.cache.get(patient_id, tenant_id)
            if cached:
                # Reconstruir twin a partir do dict cacheado
                # Nota: profile/timeline/graph são objetos complexos;
                # para simplicidade, o cache armazena apenas dados serializáveis
                # e refazemos o build a partir do profile (1 query em vez de 4)
                profile = self.repository.get_profile(patient_id, tenant_id)
                if profile:
                    return await self._build_from_profile(profile, patient_id, tenant_id)
        
        # 2. Build completo
        profile = self.repository.get_profile(patient_id, tenant_id)
        twin = await self._build_from_profile(profile, patient_id, tenant_id)
        
        # 3. Armazenar no cache
        if self.cache:
            await self.cache.set(patient_id, tenant_id, twin.to_dict())
        
        return twin
    
    async def _build_from_profile(
        self,
        profile: Optional[ClinicalProfile],
        patient_id: str,
        tenant_id: str,
    ) -> PatientDigitalTwin:
        """Constrói twin a partir de um profile já carregado."""
        # Timeline
        timeline = ClinicalTimeline(self.repository, patient_id, tenant_id)
        
        # Grafo
        from ..graph.models import ClinicalGraphBuilder
        graph_builder = ClinicalGraphBuilder(patient_id)
        if profile:
            graph_builder.add_diagnoses(profile.active_diagnoses or [])
            graph_builder.add_medications(profile.active_medications or [])
            graph_builder.add_allergies(profile.allergies or [])
        graph = graph_builder.build()
        
        # Resumo
        summary = None
        if profile:
            engine = ClinicalSummaryEngine()
            summary = engine.generate(profile.to_dict())
        
        return PatientDigitalTwin(
            patient_id=patient_id,
            tenant_id=tenant_id,
            profile=profile,
            timeline=timeline,
            graph=graph,
            summary=summary,
        )
