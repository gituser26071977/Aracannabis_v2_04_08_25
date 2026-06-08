"""
AraOS Follow-up — Core Models.

Modelos fundamentais do motor de acompanhamento longitudinal.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class FollowupStatus(str, Enum):
    """Status de um programa de acompanhamento."""
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class AlertSeverity(str, Enum):
    """Severidade de um alerta de follow-up."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Status de um alerta."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class QuestionType(str, Enum):
    """Tipo de pergunta em um questionário."""
    SCALE = "scale"           # 0-10
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    NUMBER = "number"
    CHECKLIST = "checklist"


@dataclass
class FollowupQuestion:
    """Pergunta de um questionário de follow-up."""
    question_id: str
    text: str
    question_type: QuestionType
    options: List[str] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ""
    required: bool = True
    category: str = ""  # pain, anxiety, sleep, adverse_effect, adherence, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "text": self.text,
            "question_type": self.question_type.value,
            "options": self.options,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "required": self.required,
            "category": self.category,
            "metadata": self.metadata,
        }


@dataclass
class FollowupQuestionnaire:
    """Questionário de follow-up."""
    questionnaire_id: str
    name: str
    description: str = ""
    questions: List[FollowupQuestion] = field(default_factory=list)
    estimated_duration_minutes: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "questionnaire_id": self.questionnaire_id,
            "name": self.name,
            "description": self.description,
            "question_count": len(self.questions),
            "questions": [q.to_dict() for q in self.questions],
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "metadata": self.metadata,
        }

    def add_question(self, question: FollowupQuestion) -> None:
        self.questions.append(question)

    def get_questions_by_category(self, category: str) -> List[FollowupQuestion]:
        return [q for q in self.questions if q.category == category]


@dataclass
class FollowupResponse:
    """Resposta de um paciente a um questionário."""
    response_id: str
    program_id: str
    patient_id: str
    tenant_id: str
    questionnaire_id: str
    checkpoint_id: str
    answers: Dict[str, Any] = field(default_factory=dict)
    answered_at: datetime = field(default_factory=now_utc)
    channel: str = "whatsapp"  # whatsapp, app, sms, email, phone
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "program_id": self.program_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "questionnaire_id": self.questionnaire_id,
            "checkpoint_id": self.checkpoint_id,
            "answers": self.answers,
            "answered_at": self.answered_at.isoformat(),
            "channel": self.channel,
            "metadata": self.metadata,
        }

    def get_answer(self, question_id: str, default: Any = None) -> Any:
        return self.answers.get(question_id, default)


@dataclass
class FollowupCheckpoint:
    """Ponto de verificação em um programa de follow-up."""
    checkpoint_id: str
    name: str
    description: str = ""
    day_offset: int = 0  # dias a partir do início do programa
    window_days: int = 2  # janela de tolerância (+/- dias)
    questionnaire: Optional[FollowupQuestionnaire] = None
    required: bool = True
    auto_trigger: bool = True  # dispara automaticamente
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "name": self.name,
            "description": self.description,
            "day_offset": self.day_offset,
            "window_days": self.window_days,
            "questionnaire_id": self.questionnaire.questionnaire_id if self.questionnaire else None,
            "required": self.required,
            "auto_trigger": self.auto_trigger,
            "metadata": self.metadata,
        }

    def is_due(self, program_start: datetime, now: Optional[datetime] = None) -> bool:
        """Verifica se o checkpoint está dentro da janela de execução."""
        if now is None:
            now = now_utc()
        target = program_start + timedelta(days=self.day_offset)
        window_start = target - timedelta(days=self.window_days)
        window_end = target + timedelta(days=self.window_days)
        return window_start <= now <= window_end

    def days_until_due(self, program_start: datetime, now: Optional[datetime] = None) -> int:
        """Dias até o checkpoint ficar devendo."""
        if now is None:
            now = now_utc()
        target = program_start + timedelta(days=self.day_offset)
        delta = target - now
        return delta.days


@dataclass
class FollowupPhase:
    """Fase terapêutica de um programa de follow-up."""
    phase_id: str
    name: str
    description: str = ""
    order: int = 0
    duration_days: Optional[int] = None  # None = indeterminado
    checkpoints: List[FollowupCheckpoint] = field(default_factory=list)
    entry_criteria: List[str] = field(default_factory=list)
    exit_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "duration_days": self.duration_days,
            "checkpoint_count": len(self.checkpoints),
            "checkpoints": [c.to_dict() for c in self.checkpoints],
            "entry_criteria": self.entry_criteria,
            "exit_criteria": self.exit_criteria,
            "metadata": self.metadata,
        }

    def add_checkpoint(self, checkpoint: FollowupCheckpoint) -> None:
        self.checkpoints.append(checkpoint)

    def get_checkpoints_ordered(self) -> List[FollowupCheckpoint]:
        return sorted(self.checkpoints, key=lambda c: c.day_offset)


@dataclass
class FollowupAlert:
    """Alerta gerado pelo follow-up."""
    alert_id: str
    program_id: str
    patient_id: str
    tenant_id: str
    severity: AlertSeverity
    title: str
    description: str = ""
    status: AlertStatus = AlertStatus.OPEN
    triggered_by: str = ""  # rule_id, checkpoint_id, manual
    triggered_at: datetime = field(default_factory=now_utc)
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "program_id": self.program_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "triggered_by": self.triggered_by,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "assigned_to": self.assigned_to,
            "metadata": self.metadata,
        }

    def acknowledge(self, user_id: str) -> None:
        self.status = AlertStatus.ACKNOWLEDGED
        self.assigned_to = user_id

    def resolve(self) -> None:
        self.status = AlertStatus.RESOLVED
        self.resolved_at = now_utc()

    def escalate(self) -> None:
        self.status = AlertStatus.ESCALATED

    def is_open(self) -> bool:
        return self.status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)


@dataclass
class FollowupRule:
    """Regra do motor de follow-up."""
    rule_id: str
    name: str
    description: str = ""
    condition: str = ""  # expressão simples ou DSL
    condition_fn: Optional[Any] = None  # função de avaliação (runtime)
    actions: List[str] = field(default_factory=list)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "actions": self.actions,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


@dataclass
class FollowupProgram:
    """
    Programa de acompanhamento longitudinal.

    Define fases terapêuticas, checkpoints, questionários e regras
    para acompanhamento contínuo de um paciente.

    Uso:
        program = FollowupProgram(
            program_id="cannabis_001",
            patient_id="p_001",
            tenant_id="t_001",
            specialty_code="cannabis",
            name="Acompanhamento Cannabis Medicinal",
        )
        program.add_phase(phase_initial)
        program.add_phase(phase_titration)
    """
    program_id: str
    patient_id: str
    tenant_id: str
    specialty_code: str
    name: str
    description: str = ""
    status: FollowupStatus = FollowupStatus.SCHEDULED
    phases: List[FollowupPhase] = field(default_factory=list)
    rules: List[FollowupRule] = field(default_factory=list)
    alerts: List[FollowupAlert] = field(default_factory=list)
    responses: List[FollowupResponse] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "program_id": self.program_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "specialty_code": self.specialty_code,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "phase_count": len(self.phases),
            "rule_count": len(self.rules),
            "alert_count": len(self.alerts),
            "response_count": len(self.responses),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    def add_phase(self, phase: FollowupPhase) -> None:
        self.phases.append(phase)

    def add_rule(self, rule: FollowupRule) -> None:
        self.rules.append(rule)

    def add_alert(self, alert: FollowupAlert) -> None:
        self.alerts.append(alert)

    def add_response(self, response: FollowupResponse) -> None:
        self.responses.append(response)

    def get_phases_ordered(self) -> List[FollowupPhase]:
        return sorted(self.phases, key=lambda p: p.order)

    def get_current_phase(self) -> Optional[FollowupPhase]:
        """Retorna a fase atual baseada no progresso."""
        # Stub: primeira fase ativa
        for phase in self.get_phases_ordered():
            return phase
        return None

    def get_open_alerts(self, severity: Optional[AlertSeverity] = None) -> List[FollowupAlert]:
        alerts = [a for a in self.alerts if a.is_open()]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_responses_for_checkpoint(self, checkpoint_id: str) -> List[FollowupResponse]:
        return [r for r in self.responses if r.checkpoint_id == checkpoint_id]

    def start(self) -> None:
        self.status = FollowupStatus.ACTIVE
        self.started_at = now_utc()

    def complete(self) -> None:
        self.status = FollowupStatus.COMPLETED
        self.completed_at = now_utc()

    def pause(self) -> None:
        self.status = FollowupStatus.PAUSED

    def cancel(self) -> None:
        self.status = FollowupStatus.CANCELLED

    def get_adherence_rate(self) -> float:
        """Taxa de adesão (respostas / checkpoints obrigatórios)."""
        total_required = 0
        answered = 0
        for phase in self.phases:
            for checkpoint in phase.checkpoints:
                if checkpoint.required:
                    total_required += 1
                    if self.get_responses_for_checkpoint(checkpoint.checkpoint_id):
                        answered += 1
        if total_required == 0:
            return 1.0
        return round(answered / total_required, 3)

    def get_response_rate(self) -> float:
        """Taxa de resposta (respostas / tentativas de contato)."""
        # Stub: simplificado
        return self.get_adherence_rate()
