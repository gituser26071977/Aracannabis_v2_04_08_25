"""
AraOS Specialty Framework — Specialty Protocol.

Protocolos especializados e escalas de avaliação.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProtocolStepType(str, Enum):
    """Tipo de passo em um protocolo."""
    ASSESSMENT = "assessment"
    MEASUREMENT = "measurement"
    PRESCRIPTION = "prescription"
    FOLLOW_UP = "follow_up"
    REFERRAL = "referral"
    EDUCATION = "education"
    DOCUMENTATION = "documentation"
    DECISION = "decision"


class ProtocolTrigger(str, Enum):
    """Gatilhos para ativação de protocolo."""
    DIAGNOSIS = "diagnosis"
    SYMPTOM = "symptom"
    MEDICATION_START = "medication_start"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    ALERT = "alert"


@dataclass
class ProtocolStep:
    """Passo de um protocolo especializado."""
    step_id: str
    order: int
    step_type: ProtocolStepType
    title: str
    description: str = ""
    required: bool = True
    estimated_duration_minutes: int = 0
    fields: List[str] = field(default_factory=list)  # nomes de SpecialtyField esperados
    conditions: List[str] = field(default_factory=list)  # expressões condicionais
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "order": self.order,
            "step_type": self.step_type.value,
            "title": self.title,
            "description": self.description,
            "required": self.required,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "fields": self.fields,
            "conditions": self.conditions,
            "metadata": self.metadata,
        }


@dataclass
class SpecialtyProtocol:
    """
    Protocolo especializado.

    Define um fluxo de atendimento para uma especialidade.
    Não contém regras clínicas específicas — apenas estrutura.

    Exemplos futuros:
        - CannabisFollowUpProtocol
        - CardiologyHypertensionProtocol
        - PsychiatryDepressionProtocol

    Attributes:
        protocol_id: ID único
        specialty_code: Especialidade dona do protocolo
        name: Nome legível
        version: Versão
        steps: Passos do protocolo
        triggers: Gatilhos de ativação
        target_conditions: Condições-alvo (ICD-10, etc.)
    """
    protocol_id: str
    specialty_code: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: List[ProtocolStep] = field(default_factory=list)
    triggers: List[ProtocolTrigger] = field(default_factory=list)
    target_conditions: List[str] = field(default_factory=list)  # ICD-10 codes
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "specialty_code": self.specialty_code,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": [s.to_dict() for s in sorted(self.steps, key=lambda x: x.order)],
            "triggers": [t.value for t in self.triggers],
            "target_conditions": self.target_conditions,
            "metadata": self.metadata,
        }

    def add_step(self, step: ProtocolStep) -> None:
        """Adiciona um passo ao protocolo."""
        self.steps.append(step)

    def get_step(self, step_id: str) -> Optional[ProtocolStep]:
        """Recupera um passo pelo ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_steps_ordered(self) -> List[ProtocolStep]:
        """Retorna passos ordenados."""
        return sorted(self.steps, key=lambda s: s.order)

    def can_trigger(self, trigger: ProtocolTrigger) -> bool:
        """Verifica se o protocolo pode ser ativado por um gatilho."""
        return trigger in self.triggers

    def matches_condition(self, icd10_code: str) -> bool:
        """Verifica se o protocolo se aplica a uma condição."""
        return icd10_code in self.target_conditions
