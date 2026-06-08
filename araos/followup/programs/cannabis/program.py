"""
AraOS Follow-up — Cannabis Follow-up Program V1.

Primeiro programa operacional de acompanhamento.

FASE 1 — Início (Dias 0–14)
FASE 2 — Titulação (Dias 15–45)
FASE 3 — Estabilização (Dias 45–90)
FASE 4 — Manutenção (Dia 90+)

Week 11A — Adaptive Follow-up Engine (Part 9)
"""

from typing import Dict, Any, List

from araos.followup.core.models import (
    FollowupPhase, FollowupCheckpoint, FollowupQuestionnaire,
    FollowupQuestion, QuestionType, FollowupRule, AlertSeverity,
)
from araos.followup.core.specialty_integration import SpecialtyFollowupProgram


# ═══════════════════════════════════════════════════════════════════════
# QUESTIONÁRIOS
# ═══════════════════════════════════════════════════════════════════════

def build_pain_questionnaire() -> FollowupQuestionnaire:
    """Questionário de avaliação de dor."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_pain_v1",
        name="Avaliação de Dor",
        description="Avaliação da intensidade e impacto da dor",
        estimated_duration_minutes=2,
    )
    q.add_question(FollowupQuestion(
        question_id="pain_intensity",
        text="Qual a intensidade da sua dor hoje? (0 = nenhuma, 10 = pior possível)",
        question_type=QuestionType.SCALE,
        min_value=0, max_value=10,
        category="pain",
    ))
    q.add_question(FollowupQuestion(
        question_id="pain_impact_sleep",
        text="A dor está interferindo no seu sono?",
        question_type=QuestionType.YES_NO,
        category="pain",
    ))
    q.add_question(FollowupQuestion(
        question_id="pain_impact_activity",
        text="A dor está limitando suas atividades diárias?",
        question_type=QuestionType.YES_NO,
        category="pain",
    ))
    return q


def build_anxiety_questionnaire() -> FollowupQuestionnaire:
    """Questionário de avaliação de ansiedade."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_anxiety_v1",
        name="Avaliação de Ansiedade",
        description="Avaliação dos sintomas de ansiedade",
        estimated_duration_minutes=2,
    )
    q.add_question(FollowupQuestion(
        question_id="anxiety_level",
        text="Como você avalia seu nível de ansiedade hoje? (0 = nenhuma, 10 = pior possível)",
        question_type=QuestionType.SCALE,
        min_value=0, max_value=10,
        category="anxiety",
    ))
    q.add_question(FollowupQuestion(
        question_id="anxiety_panic",
        text="Você teve crises de pânico desde o último contato?",
        question_type=QuestionType.YES_NO,
        category="anxiety",
    ))
    return q


def build_sleep_questionnaire() -> FollowupQuestionnaire:
    """Questionário de avaliação do sono."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_sleep_v1",
        name="Avaliação do Sono",
        description="Avaliação da qualidade do sono",
        estimated_duration_minutes=2,
    )
    q.add_question(FollowupQuestion(
        question_id="sleep_quality",
        text="Como você avalia a qualidade do seu sono? (0 = péssima, 10 = excelente)",
        question_type=QuestionType.SCALE,
        min_value=0, max_value=10,
        category="sleep",
    ))
    q.add_question(FollowupQuestion(
        question_id="sleep_hours",
        text="Quantas horas você dormiu na última noite?",
        question_type=QuestionType.NUMBER,
        unit="hours",
        category="sleep",
    ))
    return q


def REDACTED() -> FollowupQuestionnaire:
    """Questionário de qualidade de vida."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_qol_v1",
        name="Qualidade de Vida",
        description="Avaliação geral da qualidade de vida",
        estimated_duration_minutes=1,
    )
    q.add_question(FollowupQuestion(
        question_id="qol_general",
        text="Como você avalia sua qualidade de vida geral? (0 = péssima, 10 = excelente)",
        question_type=QuestionType.SCALE,
        min_value=0, max_value=10,
        category="quality_of_life",
    ))
    return q


def REDACTED() -> FollowupQuestionnaire:
    """Questionário de efeitos adversos."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_adverse_v1",
        name="Efeitos Adversos",
        description="Avaliação de efeitos adversos do tratamento",
        estimated_duration_minutes=2,
    )
    q.add_question(FollowupQuestion(
        question_id="ae_drowsiness",
        text="Você sentiu sonolência excessiva?",
        question_type=QuestionType.YES_NO,
        category="adverse_effect",
    ))
    q.add_question(FollowupQuestion(
        question_id="ae_dizziness",
        text="Você sentiu tontura?",
        question_type=QuestionType.YES_NO,
        category="adverse_effect",
    ))
    q.add_question(FollowupQuestion(
        question_id="ae_dry_mouth",
        text="Você sentiu boca seca?",
        question_type=QuestionType.YES_NO,
        category="adverse_effect",
    ))
    q.add_question(FollowupQuestion(
        question_id="ae_paradoxical_anxiety",
        text="Você notou aumento de ansiedade?",
        question_type=QuestionType.YES_NO,
        category="adverse_effect",
    ))
    q.add_question(FollowupQuestion(
        question_id="ae_tachycardia",
        text="Você sentiu batimentos cardíacos acelerados?",
        question_type=QuestionType.YES_NO,
        category="adverse_effect",
    ))
    q.add_question(FollowupQuestion(
        question_id="ae_severity",
        text="Se teve algum efeito adverso, qual a intensidade? (0 = leve, 10 = grave)",
        question_type=QuestionType.SCALE,
        min_value=0, max_value=10,
        category="adverse_effect",
    ))
    return q


def build_adherence_questionnaire() -> FollowupQuestionnaire:
    """Questionário de adesão ao tratamento."""
    q = FollowupQuestionnaire(
        questionnaire_id="cannabis_adherence_v1",
        name="Adesão ao Tratamento",
        description="Avaliação da adesão à medicação",
        estimated_duration_minutes=1,
    )
    q.add_question(FollowupQuestion(
        question_id="adh_took_correctly",
        text="Você tomou a medicação corretamente conforme prescrito?",
        question_type=QuestionType.YES_NO,
        category="adherence",
    ))
    q.add_question(FollowupQuestion(
        question_id="adh_missed_doses",
        text="Quantas doses você esqueceu de tomar?",
        question_type=QuestionType.NUMBER,
        category="adherence",
    ))
    q.add_question(FollowupQuestion(
        question_id="adh_stopped",
        text="Você interrompeu o tratamento por algum motivo?",
        question_type=QuestionType.YES_NO,
        category="adherence",
    ))
    return q


# ═══════════════════════════════════════════════════════════════════════
# REGRAS DE ESCALONAMENTO
# ═══════════════════════════════════════════════════════════════════════

def build_severe_adverse_rule() -> FollowupRule:
    return FollowupRule(
        rule_id="cannabis_severe_ae",
        name="Efeito Adverso Grave",
        description="Efeito adverso com intensidade >= 7 ou múltiplos sintomas graves",
        condition="severe_adverse_effect",
        actions=["alert_physician", "create_urgent_review", "whatsapp_alert"],
        severity=AlertSeverity.CRITICAL,
    )


def build_worsening_rule() -> FollowupRule:
    return FollowupRule(
        rule_id="cannabis_worsening",
        name="Piora dos Sintomas",
        description="Piora significativa nos scores de dor, ansiedade ou sono",
        condition="worsening_symptoms",
        actions=["alert_physician", "schedule_review"],
        severity=AlertSeverity.HIGH,
    )


def build_no_response_rule() -> FollowupRule:
    return FollowupRule(
        rule_id="cannabis_no_response",
        name="Ausência de Resposta",
        description="Paciente não respondeu a 3 tentativas consecutivas",
        condition="patient_no_response",
        actions=["reengage_patient", "alert_team"],
        severity=AlertSeverity.MEDIUM,
    )


def build_help_request_rule() -> FollowupRule:
    return FollowupRule(
        rule_id="cannabis_help_request",
        name="Solicitação de Ajuda",
        description="Paciente solicitou ajuda explicitamente",
        condition="patient_requests_help",
        actions=["escalate_immediately", "alert_physician"],
        severity=AlertSeverity.CRITICAL,
    )


# ═══════════════════════════════════════════════════════════════════════
# FASES
# ═══════════════════════════════════════════════════════════════════════

def build_initial_phase() -> FollowupPhase:
    """Fase 1 — Início (Dias 0–14)."""
    phase = FollowupPhase(
        phase_id="cannabis_initial",
        name="Início",
        description="Fase inicial de acompanhamento — avaliação de adesão, tolerabilidade e efeitos adversos",
        order=1,
        duration_days=14,
    )

    # D+2: Adesão e efeitos adversos iniciais
    phase.add_checkpoint(FollowupCheckpoint(
        checkpoint_id="cp_d2",
        name="Avaliação D+2",
        description="Primeira avaliação de adesão e efeitos adversos",
        day_offset=2,
        window_days=1,
        questionnaire=build_adherence_questionnaire(),
    ))

    # D+5: Sintomas e efeitos adversos
    phase.add_checkpoint(FollowupCheckpoint(
        checkpoint_id="cp_d5",
        name="Avaliação D+5",
        description="Avaliação de sintomas e efeitos adversos",
        day_offset=5,
        window_days=1,
        questionnaire=REDACTED(),
    ))

    # D+10: Avaliação completa
    phase.add_checkpoint(FollowupCheckpoint(
        checkpoint_id="cp_d10",
        name="Avaliação D+10",
        description="Avaliação completa de dor, ansiedade, sono e qualidade de vida",
        day_offset=10,
        window_days=2,
        questionnaire=build_pain_questionnaire(),
    ))

    # D+14: Transição de fase
    phase.add_checkpoint(FollowupCheckpoint(
        checkpoint_id="cp_d14",
        name="Avaliação D+14 — Transição",
        description="Avaliação final da fase inicial",
        day_offset=14,
        window_days=2,
        questionnaire=build_pain_questionnaire(),
    ))

    return phase


def build_titration_phase() -> FollowupPhase:
    """Fase 2 — Titulação (Dias 15–45)."""
    phase = FollowupPhase(
        phase_id="cannabis_titration",
        name="Titulação",
        description="Fase de ajuste de dose — avaliação semanal da resposta clínica",
        order=2,
        duration_days=30,
    )

    # Checkpoints semanais
    for week, day in enumerate([21, 28, 35, 42], 1):
        phase.add_checkpoint(FollowupCheckpoint(
            checkpoint_id=f"cp_d{day}",
            name=f"Avaliação Semana {week}",
            description=f"Avaliação semanal — dor, ansiedade, sono, efeitos adversos",
            day_offset=day,
            window_days=2,
            questionnaire=build_pain_questionnaire(),
        ))

    return phase


def build_stabilization_phase() -> FollowupPhase:
    """Fase 3 — Estabilização (Dias 45–90)."""
    phase = FollowupPhase(
        phase_id="cannabis_stabilization",
        name="Estabilização",
        description="Fase de estabilização — avaliações quinzenais",
        order=3,
        duration_days=45,
    )

    # Checkpoints quinzenais
    for day in [60, 75, 90]:
        phase.add_checkpoint(FollowupCheckpoint(
            checkpoint_id=f"cp_d{day}",
            name=f"Avaliação D+{day}",
            description="Avaliação quinzenal de manutenção",
            day_offset=day,
            window_days=3,
            questionnaire=build_pain_questionnaire(),
        ))

    return phase


def build_maintenance_phase() -> FollowupPhase:
    """Fase 4 — Manutenção (Dia 90+)."""
    phase = FollowupPhase(
        phase_id="cannabis_maintenance",
        name="Manutenção",
        description="Fase de manutenção — avaliações mensais ou bimestrais",
        order=4,
        duration_days=None,  # Indeterminado
    )

    # Checkpoints mensais (120, 150, 180...)
    for month in [4, 5, 6]:
        day = month * 30
        phase.add_checkpoint(FollowupCheckpoint(
            checkpoint_id=f"cp_d{day}",
            name=f"Avaliação Mês {month}",
            description="Avaliação mensal de manutenção",
            day_offset=day,
            window_days=5,
            questionnaire=build_pain_questionnaire(),
        ))

    return phase


# ═══════════════════════════════════════════════════════════════════════
# PROGRAMA COMPLETO
# ═══════════════════════════════════════════════════════════════════════

def build_cannabis_followup_program() -> SpecialtyFollowupProgram:
    """
    Constrói o programa completo de acompanhamento Cannabis.

    Returns:
        SpecialtyFollowupProgram pronto para instanciar por paciente.
    """
    program = SpecialtyFollowupProgram(
        specialty_code="cannabis",
        name="Acompanhamento Cannabis Medicinal",
        description="Programa de acompanhamento longitudinal para pacientes em tratamento com cannabis medicinal",
    )

    # Fases
    program.add_phase(build_initial_phase())
    program.add_phase(build_titration_phase())
    program.add_phase(build_stabilization_phase())
    program.add_phase(build_maintenance_phase())

    # Questionários globais (podem ser usados em múltiplas fases)
    program.add_questionnaire(build_pain_questionnaire())
    program.add_questionnaire(build_anxiety_questionnaire())
    program.add_questionnaire(build_sleep_questionnaire())
    program.add_questionnaire(REDACTED())
    program.add_questionnaire(REDACTED())
    program.add_questionnaire(build_adherence_questionnaire())

    # Regras de escalonamento
    program.add_rule(build_severe_adverse_rule())
    program.add_rule(build_worsening_rule())
    program.add_rule(build_no_response_rule())
    program.add_rule(build_help_request_rule())

    return program


# Instância global do programa
CANNABIS_FOLLOWUP_PROGRAM = build_cannabis_followup_program()
