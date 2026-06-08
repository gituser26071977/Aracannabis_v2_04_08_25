"""
AraOS Follow-up — Rule Engine.

Motor de regras para alertas, reengajamento e escalação.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from araos.followup.core.models import (
    FollowupProgram, FollowupResponse, FollowupAlert, FollowupRule,
    AlertSeverity, AlertStatus,
)


@dataclass
class RuleEvaluationContext:
    """Contexto para avaliação de regras."""
    program: FollowupProgram
    response: Optional[FollowupResponse] = None
    patient_twin: Optional[Any] = None
    checkpoint_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FollowupRuleEngine:
    """
    Motor de regras de follow-up.

    Permite regras do tipo SE/ENTÃO:
        SE efeito adverso grave → alertar médico
        SE ausência de resposta clínica → criar revisão
        SE paciente não responde → reengajar
        SE paciente solicita ajuda → escalar imediatamente

    Uso:
        engine = FollowupRuleEngine()

        # Registrar regra
        engine.register_rule(FollowupRule(
            rule_id="severe_adverse_effect",
            name="Efeito Adverso Grave",
            condition="adverse_effect.severity == 'severe'",
            actions=["alert_physician", "create_urgent_review"],
            severity=AlertSeverity.CRITICAL,
        ))

        # Avaliar
        alerts = engine.evaluate(program, response)
    """

    def __init__(self):
        self._rules: Dict[str, FollowupRule] = {}
        self._builtin_conditions: Dict[str, Callable] = {
            "severe_adverse_effect": self._check_severe_adverse_effect,
            "no_clinical_response": self._check_no_clinical_response,
            "patient_no_response": self._check_patient_no_response,
            "patient_requests_help": self._check_patient_requests_help,
            "dose_tolerance_issue": self._check_dose_tolerance,
            "worsening_symptoms": self._check_worsening_symptoms,
        }

    def register_rule(self, rule: FollowupRule) -> None:
        """Registra uma regra."""
        self._rules[rule.rule_id] = rule

    def unregister_rule(self, rule_id: str) -> bool:
        """Remove uma regra."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def evaluate(
        self,
        program: FollowupProgram,
        response: Optional[FollowupResponse] = None,
        context: Optional[RuleEvaluationContext] = None,
    ) -> List[FollowupAlert]:
        """
        Avalia todas as regras registradas.

        Returns:
            Lista de alertas gerados.
        """
        alerts = []
        ctx = context or RuleEvaluationContext(program=program, response=response)

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            triggered = self._evaluate_condition(rule, ctx)
            if triggered:
                alert = self._create_alert(rule, program)
                alerts.append(alert)

        return alerts

    def evaluate_single(
        self,
        rule_id: str,
        program: FollowupProgram,
        response: Optional[FollowupResponse] = None,
    ) -> Optional[FollowupAlert]:
        """Avalia uma regra específica."""
        rule = self._rules.get(rule_id)
        if not rule or not rule.enabled:
            return None

        ctx = RuleEvaluationContext(program=program, response=response)
        triggered = self._evaluate_condition(rule, ctx)
        if triggered:
            return self._create_alert(rule, program)
        return None

    def _evaluate_condition(self, rule: FollowupRule, ctx: RuleEvaluationContext) -> bool:
        """Avalia a condição de uma regra."""
        # 1. Se tem condition_fn customizada, usa ela
        if rule.condition_fn:
            try:
                return rule.condition_fn(ctx)
            except Exception:
                return False

        # 2. Se é uma condição built-in, usa o handler
        if rule.condition in self._builtin_conditions:
            try:
                return self._builtin_conditions[rule.condition](ctx)
            except Exception:
                return False

        # 3. Stub: avaliação de string simples
        # Futuro: parser DSL completo
        return False

    def _create_alert(self, rule: FollowupRule, program: FollowupProgram) -> FollowupAlert:
        """Cria alerta a partir de uma regra disparada."""
        from datetime import datetime, timezone
        return FollowupAlert(
            alert_id=f"alert_{rule.rule_id}_{datetime.now(timezone.utc).timestamp()}",
            program_id=program.program_id,
            patient_id=program.patient_id,
            tenant_id=program.tenant_id,
            severity=rule.severity,
            title=f"Alerta: {rule.name}",
            description=rule.description,
            triggered_by=rule.rule_id,
        )

    # ── Built-in Conditions ──

    def _check_severe_adverse_effect(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica se há efeito adverso grave na resposta."""
        if not ctx.response:
            return False
        # Buscar respostas na categoria adverse_effect com valor alto
        answers = ctx.response.answers
        for key, value in answers.items():
            if "adverse" in key.lower() or "severe" in str(value).lower():
                if isinstance(value, (int, float)) and value >= 7:
                    return True
                if isinstance(value, str) and value.lower() in ("severe", "grave", "sim"):
                    return True
        return False

    def _check_no_clinical_response(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica ausência de resposta clínica após período."""
        # Stub: verificaria histórico de scores
        return False

    def _check_patient_no_response(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica se paciente não respondeu a múltiplas tentativas."""
        # Stub: verificaria tentativas de contato
        return False

    def _check_patient_requests_help(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica se paciente solicitou ajuda explicitamente."""
        if not ctx.response:
            return False
        answers = ctx.response.answers
        for key, value in answers.items():
            if "help" in key.lower() or "ajuda" in key.lower() or "socorro" in key.lower():
                if isinstance(value, str) and value.lower() in ("sim", "yes", "true"):
                    return True
        return False

    def _check_dose_tolerance(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica problemas de tolerância à dose."""
        if not ctx.response:
            return False
        answers = ctx.response.answers
        for key, value in answers.items():
            if "toler" in key.lower() or "tolerance" in key.lower():
                if isinstance(value, str) and value.lower() in ("não", "no", "false", "ruim", "bad"):
                    return True
        return False

    def _check_worsening_symptoms(self, ctx: RuleEvaluationContext) -> bool:
        """Verifica piora de sintomas."""
        # Stub: compararia com baseline
        return False
