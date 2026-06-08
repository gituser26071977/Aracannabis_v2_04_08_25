"""
AraOS Cannabis Module — Profile.

Perfil especializado para Cannabis Medicinal.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from araos.specialties.core.profile import SpecialtyProfile, SpecialtyField


@dataclass
class CannabisTherapeuticGoal:
    """Objetivo terapêutico do tratamento com cannabis."""
    goal_id: str
    description: str
    target_symptom: str = ""  # pain, anxiety, sleep, spasticity, seizures, etc.
    target_metric: str = ""   # EVA, GAD-7, etc.
    baseline_score: float = 0.0
    target_score: float = 0.0
    achieved: bool = False
    achieved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "target_symptom": self.target_symptom,
            "target_metric": self.target_metric,
            "baseline_score": self.baseline_score,
            "target_score": self.target_score,
            "achieved": self.achieved,
            "achieved_at": self.achieved_at.isoformat() if self.achieved_at else None,
            "metadata": self.metadata,
        }


class CannabisProfile(SpecialtyProfile):
    """
    Perfil especializado para Cannabis Medicinal.

    Campos:
        - condição principal
        - CID
        - condições associadas
        - objetivos terapêuticos
        - data de início
        - médico responsável
        - status terapêutico

    Integra com Patient Digital Twin.
    """

    def __init__(self, patient_id: str, tenant_id: str):
        super().__init__(patient_id, tenant_id, specialty_code="cannabis")
        self._therapeutic_goals: List[CannabisTherapeuticGoal] = []

    # ── Campos estruturados ──

    def set_main_condition(self, condition: str, icd10_code: str = "") -> None:
        """Define condição principal."""
        self.add_field(SpecialtyField(name="main_condition", value=condition, field_type="string"))
        if icd10_code:
            self.add_field(SpecialtyField(name="main_condition_icd10", value=icd10_code, field_type="string"))

    def add_associated_condition(self, condition: str, icd10_code: str = "") -> None:
        """Adiciona condição associada."""
        conditions = self.get_field_value("associated_conditions", [])
        if isinstance(conditions, list):
            conditions.append({"condition": condition, "icd10": icd10_code})
        else:
            conditions = [{"condition": condition, "icd10": icd10_code}]
        self.add_field(SpecialtyField(name="associated_conditions", value=conditions, field_type="list"))

    def set_start_date(self, date: datetime) -> None:
        """Define data de início do tratamento."""
        self.add_field(SpecialtyField(name="treatment_start_date", value=date.isoformat(), field_type="date"))

    def set_responsible_physician(self, physician_id: str, physician_name: str = "") -> None:
        """Define médico responsável."""
        self.add_field(SpecialtyField(
            name="responsible_physician",
            value={"id": physician_id, "name": physician_name},
            field_type="object",
        ))

    def set_therapeutic_status(self, status: str) -> None:
        """Define status terapêutico."""
        # active, titrating, stable, paused, discontinued
        self.add_field(SpecialtyField(name="therapeutic_status", value=status, field_type="enum"))

    # ── Objetivos terapêuticos ──

    def add_therapeutic_goal(self, goal: CannabisTherapeuticGoal) -> None:
        """Adiciona objetivo terapêutico."""
        self._therapeutic_goals.append(goal)

    def get_goals(self, target_symptom: Optional[str] = None) -> List[CannabisTherapeuticGoal]:
        """Recupera objetivos terapêuticos."""
        if target_symptom:
            return [g for g in self._therapeutic_goals if g.target_symptom == target_symptom]
        return self._therapeutic_goals.copy()

    def get_achieved_goals(self) -> List[CannabisTherapeuticGoal]:
        """Recupera objetivos alcançados."""
        return [g for g in self._therapeutic_goals if g.achieved]

    # ── Validação ──

    def validate(self) -> List[str]:
        errors = []
        if not self.get_field_value("main_condition"):
            errors.append("Condição principal não definida")
        if not self.get_field_value("responsible_physician"):
            errors.append("Médico responsável não definido")
        if not self._therapeutic_goals:
            errors.append("Nenhum objetivo terapêutico definido")
        return errors

    def get_definition(self):
        from araos.specialties.stubs.cannabis import CANNABIS_DEFINITION
        return CANNABIS_DEFINITION

    # ── Serialização ──

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["therapeutic_goals"] = [g.to_dict() for g in self._therapeutic_goals]
        base["achieved_goals_count"] = len(self.get_achieved_goals())
        return base
