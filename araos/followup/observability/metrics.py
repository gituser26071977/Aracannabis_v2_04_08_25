"""
AraOS Follow-up — Observability.

Métricas e monitoramento do motor de acompanhamento.

Week 11A — Adaptive Follow-up Engine
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class FollowupMetric:
    """Métrica de follow-up."""
    metric_type: str
    value: float
    program_id: Optional[str] = None
    patient_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "program_id": self.program_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class FollowupObservability:
    """
    Observabilidade do motor de follow-up.

    Métricas coletadas:
        - taxa de resposta
        - taxa de adesão
        - alertas gerados
        - escalonamentos
        - satisfação
        - tempo até intervenção

    Uso:
        obs = FollowupObservability()

        # Registrar métrica
        obs.record_response_rate(program_id, 0.85)
        obs.record_alert(program_id, AlertSeverity.HIGH)

        # Resumo
        summary = obs.summary(program_id)
    """

    def __init__(self):
        self._metrics: List[FollowupMetric] = []
        self._alerts_by_severity: Dict[str, int] = {}
        self._escalations: int = 0
        self._intervention_times: List[float] = []

    def record_metric(
        self,
        metric_type: str,
        value: float,
        program_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> FollowupMetric:
        """Registra uma métrica."""
        metric = FollowupMetric(
            metric_type=metric_type,
            value=value,
            program_id=program_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
        )
        self._metrics.append(metric)
        return metric

    def record_response_rate(self, program_id: str, rate: float) -> None:
        """Registra taxa de resposta."""
        self.record_metric("response_rate", rate, program_id=program_id)

    def record_adherence_rate(self, program_id: str, rate: float) -> None:
        """Registra taxa de adesão."""
        self.record_metric("adherence_rate", rate, program_id=program_id)

    def record_alert(self, program_id: str, severity: str) -> None:
        """Registra alerta gerado."""
        self._alerts_by_severity[severity] = self._alerts_by_severity.get(severity, 0) + 1
        self.record_metric("alert_generated", 1.0, program_id=program_id)

    def record_escalation(self, program_id: str) -> None:
        """Registra escalonamento."""
        self._escalations += 1
        self.record_metric("escalation", 1.0, program_id=program_id)

    def record_satisfaction(self, program_id: str, score: float) -> None:
        """Registra satisfação do paciente."""
        self.record_metric("satisfaction", score, program_id=program_id)

    def record_intervention_time(self, program_id: str, hours: float) -> None:
        """Registra tempo até intervenção (em horas)."""
        self._intervention_times.append(hours)
        self.record_metric("intervention_time_hours", hours, program_id=program_id)

    def summary(self, program_id: Optional[str] = None) -> Dict[str, Any]:
        """Retorna resumo de métricas."""
        metrics = self._metrics
        if program_id:
            metrics = [m for m in metrics if m.program_id == program_id]

        response_rates = [m.value for m in metrics if m.metric_type == "response_rate"]
        adherence_rates = [m.value for m in metrics if m.metric_type == "adherence_rate"]
        satisfactions = [m.value for m in metrics if m.metric_type == "satisfaction"]
        intervention_times = [m.value for m in metrics if m.metric_type == "intervention_time_hours"]

        def avg(values: List[float]) -> float:
            return round(sum(values) / len(values), 3) if values else 0.0

        return {
            "total_metrics": len(metrics),
            "avg_response_rate": avg(response_rates),
            "avg_adherence_rate": avg(adherence_rates),
            "avg_satisfaction": avg(satisfactions),
            "avg_intervention_time_hours": avg(intervention_times),
            "total_alerts": sum(self._alerts_by_severity.values()),
            "alerts_by_severity": self._alerts_by_severity.copy(),
            "total_escalations": self._escalations,
        }

    def get_metrics(self, metric_type: str, program_id: Optional[str] = None) -> List[FollowupMetric]:
        """Recupera métricas por tipo."""
        results = [m for m in self._metrics if m.metric_type == metric_type]
        if program_id:
            results = [m for m in results if m.program_id == program_id]
        return results

    def clear(self) -> None:
        """Limpa todas as métricas."""
        self._metrics.clear()
        self._alerts_by_severity.clear()
        self._escalations = 0
        self._intervention_times.clear()
