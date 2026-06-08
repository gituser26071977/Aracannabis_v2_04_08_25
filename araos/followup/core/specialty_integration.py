"""
AraOS Follow-up — Specialty Integration.

Integra o motor de follow-up com o Specialty Framework.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any, List, Optional

from araos.specialties.core.definitions import SpecialtyDefinition, SpecialtyCapability
from araos.specialties.core.profile import SpecialtyProfile

from .models import (
    FollowupProgram, FollowupPhase, FollowupCheckpoint, FollowupQuestionnaire,
    FollowupQuestion, QuestionType, FollowupRule, FollowupStatus,
)


class SpecialtyFollowupProgram:
    """
    Programa de follow-up vinculado a uma especialidade.

    Permite que cada especialidade registre:
        - fases terapêuticas
        - questionários
        - regras
        - alertas

    Uso:
        specialty_program = SpecialtyFollowupProgram(
            specialty_code="cannabis",
            name="Acompanhamento Cannabis",
        )
        specialty_program.add_phase(phase_initial)
        specialty_program.add_questionnaire(questionnaire_pain)
        specialty_program.add_rule(rule_severe_adverse)

        # Criar instância para um paciente
        program = specialty_program.create_program(
            program_id="cannabis_p001",
            patient_id="p_001",
            tenant_id="t_001",
        )
    """

    def __init__(self, specialty_code: str, name: str, description: str = ""):
        self.specialty_code = specialty_code
        self.name = name
        self.description = description
        self._phases: List[FollowupPhase] = []
        self._questionnaires: Dict[str, FollowupQuestionnaire] = {}
        self._rules: List[FollowupRule] = []
        self._metadata: Dict[str, Any] = {}

    def add_phase(self, phase: FollowupPhase) -> None:
        """Adiciona uma fase ao programa."""
        self._phases.append(phase)

    def add_questionnaire(self, questionnaire: FollowupQuestionnaire) -> None:
        """Registra um questionário."""
        self._questionnaires[questionnaire.questionnaire_id] = questionnaire

    def add_rule(self, rule: FollowupRule) -> None:
        """Registra uma regra."""
        self._rules.append(rule)

    def get_questionnaire(self, questionnaire_id: str) -> Optional[FollowupQuestionnaire]:
        """Recupera um questionário pelo ID."""
        return self._questionnaires.get(questionnaire_id)

    def create_program(
        self,
        program_id: str,
        patient_id: str,
        tenant_id: str,
    ) -> FollowupProgram:
        """
        Cria uma instância do programa para um paciente.

        Copia fases, regras e questionários para o programa individual.
        """
        program = FollowupProgram(
            program_id=program_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            specialty_code=self.specialty_code,
            name=self.name,
            description=self.description,
        )

        # Copiar fases
        for phase in self._phases:
            program.add_phase(phase)

        # Copiar regras
        for rule in self._rules:
            program.add_rule(rule)

        return program

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialty_code": self.specialty_code,
            "name": self.name,
            "description": self.description,
            "phase_count": len(self._phases),
            "questionnaire_count": len(self._questionnaires),
            "rule_count": len(self._rules),
            "phases": [p.to_dict() for p in self._phases],
            "questionnaires": [q.to_dict() for q in self._questionnaires.values()],
            "rules": [r.to_dict() for r in self._rules],
            "metadata": self._metadata,
        }
