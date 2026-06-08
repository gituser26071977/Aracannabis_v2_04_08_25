"""
AraOS Specialty Framework — Specialty Workflow.

Workflow especializado integrado ao Workflow Engine.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class WorkflowStatus(str, Enum):
    """Status de um workflow especializado."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class WorkflowPhase(str, Enum):
    """Fase de um workflow especializado."""
    INTAKE = "intake"
    ASSESSMENT = "assessment"
    TREATMENT = "treatment"
    MONITORING = "monitoring"
    FOLLOW_UP = "follow_up"
    COMPLETION = "completion"


@dataclass
class WorkflowCheckpoint:
    """Ponto de verificação em um workflow."""
    checkpoint_id: str
    phase: WorkflowPhase
    title: str
    description: str = ""
    required_fields: List[str] = field(default_factory=list)
    required_scores: List[str] = field(default_factory=list)
    due_days_from_start: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase.value,
            "title": self.title,
            "description": self.description,
            "required_fields": self.required_fields,
            "required_scores": self.required_scores,
            "due_days_from_start": self.due_days_from_start,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowInstance:
    """Instância de um workflow em execução."""
    instance_id: str
    workflow_id: str
    patient_id: str
    tenant_id: str
    specialty_code: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_phase: WorkflowPhase = WorkflowPhase.INTAKE
    completed_checkpoints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "workflow_id": self.workflow_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "specialty_code": self.specialty_code,
            "status": self.status.value,
            "current_phase": self.current_phase.value,
            "completed_checkpoints": self.completed_checkpoints,
            "metadata": self.metadata,
        }

    def complete_checkpoint(self, checkpoint_id: str) -> None:
        """Marca um checkpoint como completo."""
        if checkpoint_id not in self.completed_checkpoints:
            self.completed_checkpoints.append(checkpoint_id)

    def is_checkpoint_completed(self, checkpoint_id: str) -> bool:
        """Verifica se um checkpoint foi completado."""
        return checkpoint_id in self.completed_checkpoints


class SpecialtyWorkflow:
    """
    Workflow especializado.

    Define um percurso de cuidado para uma especialidade.
    Integra com o Workflow Engine da plataforma.

    Exemplos futuros:
        - CannabisFollowUpWorkflow
        - NutrologyWeightLossJourney
        - PsychiatryMedicationMonitoring

    Attributes:
        workflow_id: ID único
        specialty_code: Especialidade dona do workflow
        name: Nome legível
        description: Descrição
        checkpoints: Pontos de verificação do workflow
    """

    def __init__(
        self,
        workflow_id: str,
        specialty_code: str,
        name: str,
        description: str = "",
    ):
        self.workflow_id = workflow_id
        self.specialty_code = specialty_code
        self.name = name
        self.description = description
        self._checkpoints: List[WorkflowCheckpoint] = []
        self._metadata: Dict[str, Any] = {}

    def add_checkpoint(self, checkpoint: WorkflowCheckpoint) -> None:
        """Adiciona um checkpoint ao workflow."""
        self._checkpoints.append(checkpoint)

    def get_checkpoints(self, phase: Optional[WorkflowPhase] = None) -> List[WorkflowCheckpoint]:
        """Recupera checkpoints, opcionalmente filtrados por fase."""
        if phase:
            return [c for c in self._checkpoints if c.phase == phase]
        return self._checkpoints.copy()

    def get_checkpoint(self, checkpoint_id: str) -> Optional[WorkflowCheckpoint]:
        """Recupera um checkpoint pelo ID."""
        for cp in self._checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def get_phases(self) -> List[WorkflowPhase]:
        """Retorna todas as fases únicas do workflow."""
        seen = set()
        phases = []
        for cp in self._checkpoints:
            if cp.phase not in seen:
                seen.add(cp.phase)
                phases.append(cp.phase)
        return phases

    def create_instance(
        self,
        instance_id: str,
        patient_id: str,
        tenant_id: str,
    ) -> WorkflowInstance:
        """Cria uma instância do workflow para um paciente."""
        return WorkflowInstance(
            instance_id=instance_id,
            workflow_id=self.workflow_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            specialty_code=self.specialty_code,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "specialty_code": self.specialty_code,
            "name": self.name,
            "description": self.description,
            "checkpoint_count": len(self._checkpoints),
            "checkpoints": [c.to_dict() for c in self._checkpoints],
            "phases": [p.value for p in self.get_phases()],
            "metadata": self._metadata,
        }
