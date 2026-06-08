"""
AraOS Follow-up — Adaptive Engine.

Motor de acompanhamento longitudinal adaptativo.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from .models import (
    FollowupProgram, FollowupPhase, FollowupCheckpoint, FollowupStatus,
    FollowupResponse, FollowupAlert, AlertSeverity, AlertStatus,
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AdaptiveFollowupEngine:
    """
    Motor de acompanhamento longitudinal adaptativo.

    Responsabilidades:
        1. Gerenciar ciclo de vida de programas de follow-up
        2. Determinar próximos checkpoints baseado em fases
        3. Avaliar respostas e decidir transições de fase
        4. Disparar questionários no momento certo
        5. Integrar com Digital Twin, Event Bus, Alertas

    Uso:
        engine = AdaptiveFollowupEngine()

        # Registrar programa
        engine.register_program(program)

        # Processar resposta
        engine.process_response(program_id, response)

        # Verificar checkpoints devidos
        due = engine.get_due_checkpoints(program_id)

        # Avaliar regras
        alerts = engine.evaluate_rules(program_id)
    """

    def __init__(self):
        self._programs: Dict[str, FollowupProgram] = {}
        self._callbacks: Dict[str, List] = {
            "on_checkpoint_due": [],
            "on_response_received": [],
            "on_alert_triggered": [],
            "on_phase_changed": [],
            "on_program_completed": [],
        }

    def register_program(self, program: FollowupProgram) -> None:
        """Registra um programa no motor."""
        self._programs[program.program_id] = program

    def get_program(self, program_id: str) -> Optional[FollowupProgram]:
        """Recupera um programa."""
        return self._programs.get(program_id)

    def start_program(self, program_id: str) -> bool:
        """Inicia um programa de follow-up."""
        program = self._programs.get(program_id)
        if not program:
            return False
        program.start()
        self._emit("on_program_started", program)
        return True

    def get_due_checkpoints(
        self,
        program_id: str,
        now: Optional[datetime] = None,
    ) -> List[FollowupCheckpoint]:
        """
        Retorna checkpoints que estão devidos.

        Um checkpoint está devido se:
            - O programa está ativo
            - O checkpoint está dentro da janela de execução
            - Não há resposta registrada (se obrigatório)
        """
        if now is None:
            now = now_utc()

        program = self._programs.get(program_id)
        if not program or program.status != FollowupStatus.ACTIVE:
            return []

        if not program.started_at:
            return []

        due = []
        for phase in program.phases:
            for checkpoint in phase.checkpoints:
                if checkpoint.is_due(program.started_at, now):
                    # Verificar se já foi respondido
                    if checkpoint.required:
                        responses = program.get_responses_for_checkpoint(checkpoint.checkpoint_id)
                        if not responses:
                            due.append(checkpoint)
                    else:
                        due.append(checkpoint)

        return due

    def get_upcoming_checkpoints(
        self,
        program_id: str,
        days_ahead: int = 7,
    ) -> List[FollowupCheckpoint]:
        """Retorna checkpoints nos próximos N dias."""
        program = self._programs.get(program_id)
        if not program or not program.started_at:
            return []

        upcoming = []
        now = now_utc()
        for phase in program.phases:
            for checkpoint in phase.checkpoints:
                days_until = checkpoint.days_until_due(program.started_at, now)
                if 0 <= days_until <= days_ahead:
                    upcoming.append(checkpoint)

        return sorted(upcoming, key=lambda c: c.day_offset)

    def process_response(
        self,
        program_id: str,
        response: FollowupResponse,
    ) -> Dict[str, Any]:
        """
        Processa uma resposta do paciente.

        Returns:
            Dict com resultado do processamento:
                - response_accepted: bool
                - alerts_triggered: List[FollowupAlert]
                - phase_transition: Optional[str]
                - twin_updated: bool
        """
        program = self._programs.get(program_id)
        if not program:
            return {"error": "Program not found"}

        program.add_response(response)

        # Avaliar regras
        alerts = self._evaluate_rules_for_response(program, response)
        for alert in alerts:
            program.add_alert(alert)

        # Verificar transição de fase
        phase_transition = self._check_phase_transition(program)

        # Callbacks
        self._emit("on_response_received", program, response)
        for alert in alerts:
            self._emit("on_alert_triggered", program, alert)
        if phase_transition:
            self._emit("on_phase_changed", program, phase_transition)

        return {
            "response_accepted": True,
            "alerts_triggered": [a.to_dict() for a in alerts],
            "phase_transition": phase_transition,
        }

    def evaluate_rules(self, program_id: str) -> List[FollowupAlert]:
        """Avalia todas as regras de um programa."""
        program = self._programs.get(program_id)
        if not program:
            return []

        alerts = []
        for rule in program.rules:
            if not rule.enabled:
                continue
            alert = self._evaluate_rule(program, rule)
            if alert:
                program.add_alert(alert)
                alerts.append(alert)
                self._emit("on_alert_triggered", program, alert)

        return alerts

    def get_summary(self, program_id: str) -> Dict[str, Any]:
        """Retorna resumo de um programa."""
        program = self._programs.get(program_id)
        if not program:
            return {"error": "Program not found"}

        open_alerts = program.get_open_alerts()
        critical_alerts = program.get_open_alerts(AlertSeverity.CRITICAL)
        high_alerts = program.get_open_alerts(AlertSeverity.HIGH)

        return {
            "program_id": program.program_id,
            "status": program.status.value,
            "adherence_rate": program.get_adherence_rate(),
            "response_rate": program.get_response_rate(),
            "total_phases": len(program.phases),
            "total_checkpoints": sum(len(p.checkpoints) for p in program.phases),
            "total_responses": len(program.responses),
            "open_alerts": len(open_alerts),
            "critical_alerts": len(critical_alerts),
            "high_alerts": len(high_alerts),
            "current_phase": program.get_current_phase().name if program.get_current_phase() else None,
        }

    def on(self, event: str, callback) -> None:
        """Registra callback para evento."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args) -> None:
        """Emite evento para callbacks registrados."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args)
            except Exception:
                pass

    def _evaluate_rules_for_response(
        self,
        program: FollowupProgram,
        response: FollowupResponse,
    ) -> List[FollowupAlert]:
        """Avalia regras para uma resposta específica."""
        alerts = []
        for rule in program.rules:
            if not rule.enabled:
                continue
            # Stub: avaliação simplificada
            # Futuro: DSL completa com acesso a respostas, histórico, twin
            alert = self._evaluate_rule(program, rule, response)
            if alert:
                alerts.append(alert)
        return alerts

    def _evaluate_rule(
        self,
        program: FollowupProgram,
        rule,
        response: Optional[FollowupResponse] = None,
    ) -> Optional[FollowupAlert]:
        """Avalia uma regra individual."""
        # Stub: se a regra tem condition_fn, usa ela
        if rule.condition_fn:
            try:
                triggered = rule.condition_fn(program, response)
                if triggered:
                    return FollowupAlert(
                        alert_id=f"alert_{rule.rule_id}_{now_utc().timestamp()}",
                        program_id=program.program_id,
                        patient_id=program.patient_id,
                        tenant_id=program.tenant_id,
                        severity=rule.severity,
                        title=f"Alerta: {rule.name}",
                        description=rule.description,
                        triggered_by=rule.rule_id,
                    )
            except Exception:
                pass
        return None

    def _check_phase_transition(self, program: FollowupProgram) -> Optional[str]:
        """Verifica se há transição de fase necessária."""
        # Stub: lógica de transição será implementada por especialidade
        return None
