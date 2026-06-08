"""
AraOS Specialty Framework — Specialty Profile.

Contrato e implementação base para perfis especializados.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .definitions import SpecialtyDefinition, SpecialtyCapability


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SpecialtyField:
    """Campo de dado especializado."""
    name: str
    value: Any
    field_type: str = "string"  # string, number, date, enum, boolean, list
    label: str = ""
    unit: str = ""
    required: bool = False
    readonly: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "field_type": self.field_type,
            "label": self.label,
            "unit": self.unit,
            "required": self.required,
            "readonly": self.readonly,
            "metadata": self.metadata,
        }


@dataclass
class SpecialtyScore:
    """Escala/pontuação especializada."""
    scale_name: str
    score: float
    max_score: float = 100.0
    interpretation: str = ""
    severity: str = ""  # mild, moderate, severe
    date: datetime = field(default_factory=now_utc)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scale_name": self.scale_name,
            "score": self.score,
            "max_score": self.max_score,
            "interpretation": self.interpretation,
            "severity": self.severity,
            "date": self.date.isoformat(),
            "metadata": self.metadata,
        }


class SpecialtyProfile(ABC):
    """
    Contrato base para perfis especializados.

    Todo módulo de especialidade deve implementar um profile
    que herda desta classe.

    Exemplos:
        - CannabisProfile(SpecialtyProfile)
        - CardiologyProfile(SpecialtyProfile)
        - PsychiatryProfile(SpecialtyProfile)

    Uso:
        profile = CannabisProfile(patient_id="p_001", tenant_id="t_001")
        profile.add_field(SpecialtyField(name="thc_dose", value=25.0, unit="mg"))
        data = profile.to_dict()
    """

    def __init__(self, patient_id: str, tenant_id: str, specialty_code: str):
        self.patient_id = patient_id
        self.tenant_id = tenant_id
        self.specialty_code = specialty_code
        self._fields: Dict[str, SpecialtyField] = {}
        self._scores: List[SpecialtyScore] = []
        self._metadata: Dict[str, Any] = {}
        self._created_at = now_utc()
        self._updated_at = now_utc()

    # ── Campos especializados ──

    def add_field(self, field: SpecialtyField) -> None:
        """Adiciona um campo ao perfil."""
        self._fields[field.name] = field
        self._updated_at = now_utc()

    def get_field(self, name: str) -> Optional[SpecialtyField]:
        """Recupera um campo pelo nome."""
        return self._fields.get(name)

    def get_field_value(self, name: str, default: Any = None) -> Any:
        """Recupera o valor de um campo."""
        field = self._fields.get(name)
        return field.value if field else default

    def list_fields(self) -> List[SpecialtyField]:
        """Lista todos os campos."""
        return list(self._fields.values())

    def remove_field(self, name: str) -> bool:
        """Remove um campo."""
        if name in self._fields:
            del self._fields[name]
            self._updated_at = now_utc()
            return True
        return False

    # ── Escalas / Scores ──

    def add_score(self, score: SpecialtyScore) -> None:
        """Adiciona uma pontuação de escala."""
        self._scores.append(score)
        self._updated_at = now_utc()

    def get_scores(self, scale_name: Optional[str] = None) -> List[SpecialtyScore]:
        """Recupera pontuações, opcionalmente filtradas por escala."""
        if scale_name:
            return [s for s in self._scores if s.scale_name == scale_name]
        return self._scores.copy()

    def get_latest_score(self, scale_name: str) -> Optional[SpecialtyScore]:
        """Recupera a pontuação mais recente de uma escala."""
        scores = self.get_scores(scale_name)
        if not scores:
            return None
        return max(scores, key=lambda s: s.date)

    # ── Metadados ──

    def set_metadata(self, key: str, value: Any) -> None:
        """Define metadado."""
        self._metadata[key] = value
        self._updated_at = now_utc()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Recupera metadado."""
        return self._metadata.get(key, default)

    # ── Serialização ──

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o perfil para dicionário."""
        return {
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "specialty_code": self.specialty_code,
            "fields": {k: v.to_dict() for k, v in self._fields.items()},
            "scores": [s.to_dict() for s in self._scores],
            "metadata": self._metadata,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "field_count": len(self._fields),
            "score_count": len(self._scores),
        }

    @abstractmethod
    def validate(self) -> List[str]:
        """
        Valida o perfil especializado.

        Returns:
            Lista de mensagens de erro (vazia se válido).
        """
        ...

    @abstractmethod
    def get_definition(self) -> SpecialtyDefinition:
        """Retorna a definição da especialidade."""
        ...

    def is_valid(self) -> bool:
        """Verifica se o perfil é válido."""
        return len(self.validate()) == 0
