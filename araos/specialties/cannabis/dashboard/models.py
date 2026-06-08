"""
AraOS Cannabis Module — Dashboard Models.

Contratos para KPIs, métricas e gráficos do módulo Cannabis.

Week 11B — Cannabis Module V1

Sem frontend. Apenas modelos e contratos.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from araos.specialties.core.dashboard import (
    SpecialtyDashboard, SpecialtyMetric, SpecialtyKPI, SpecialtyChart,
    MetricType, ChartType, KpiSeverity,
)


@dataclass
class SymptomEvolutionData:
    """Dados de evolução de sintomas."""
    symptom_name: str
    dates: List[str] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)
    baseline_score: float = 0.0
    current_score: float = 0.0
    best_score: float = 0.0
    worst_score: float = 0.0
    change_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symptom_name": self.symptom_name,
            "dates": self.dates,
            "scores": self.scores,
            "baseline_score": self.baseline_score,
            "current_score": self.current_score,
            "best_score": self.best_score,
            "worst_score": self.worst_score,
            "change_percent": round(self.change_percent, 1),
        }


@dataclass
class DoseEvolutionData:
    """Dados de evolução de dose."""
    dates: List[str] = field(default_factory=list)
    doses_mg: List[float] = field(default_factory=list)
    thc_mg: List[float] = field(default_factory=list)
    cbd_mg: List[float] = field(default_factory=list)
    current_dose_mg: float = 0.0
    total_adjustments: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dates": self.dates,
            "doses_mg": self.doses_mg,
            "thc_mg": self.thc_mg,
            "cbd_mg": self.cbd_mg,
            "current_dose_mg": self.current_dose_mg,
            "total_adjustments": self.total_adjustments,
        }


@dataclass
class AdherenceData:
    """Dados de adesão."""
    total_checkpoints: int = 0
    completed_checkpoints: int = 0
    missed_checkpoints: int = 0
    adherence_rate: float = 0.0
    response_rate: float = 0.0
    trend: str = "stable"  # improving, worsening, stable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checkpoints": self.total_checkpoints,
            "completed_checkpoints": self.completed_checkpoints,
            "missed_checkpoints": self.missed_checkpoints,
            "adherence_rate": round(self.adherence_rate, 3),
            "response_rate": round(self.response_rate, 3),
            "trend": self.trend,
        }


@dataclass
class ClinicalResponseData:
    """Dados de resposta clínica."""
    metrics: List[str] = field(default_factory=list)
    responses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    overall_response: str = ""  # responder, partial_responder, non_responder

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "responses": self.responses,
            "overall_response": self.overall_response,
        }


@dataclass
class AlertSummaryData:
    """Dados de resumo de alertas."""
    total_alerts: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    resolved_alerts: int = 0
    escalated_alerts: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_alerts": self.total_alerts,
            "open_alerts": self.open_alerts,
            "critical_alerts": self.critical_alerts,
            "resolved_alerts": self.resolved_alerts,
            "escalated_alerts": self.escalated_alerts,
            "by_type": self.by_type,
        }


class CannabisDashboardBuilder:
    """
    Builder para dashboard do módulo Cannabis.

    Constrói SpecialtyDashboard com todos os KPIs e gráficos.
    """

    def __init__(self):
        pass

    def build(
        self,
        patient_id: str,
        symptom_data: Optional[SymptomEvolutionData] = None,
        dose_data: Optional[DoseEvolutionData] = None,
        adherence_data: Optional[AdherenceData] = None,
        response_data: Optional[ClinicalResponseData] = None,
        alert_data: Optional[AlertSummaryData] = None,
    ) -> SpecialtyDashboard:
        """Constrói dashboard completo."""
        dashboard = SpecialtyDashboard("cannabis", f"Dashboard Cannabis — {patient_id}")

        # KPIs
        if symptom_data:
            dashboard.add_kpi(SpecialtyKPI(
                kpi_id="symptom_change",
                name=f"Mudança {symptom_data.symptom_name}",
                value=symptom_data.change_percent,
                unit="%",
                threshold_warning=20.0,
                threshold_critical=50.0,
            ))

        if dose_data:
            dashboard.add_kpi(SpecialtyKPI(
                kpi_id="current_dose",
                name="Dose Atual",
                value=dose_data.current_dose_mg,
                unit="mg",
            ))

        if adherence_data:
            dashboard.add_kpi(SpecialtyKPI(
                kpi_id="adherence",
                name="Adesão",
                value=adherence_data.adherence_rate * 100,
                unit="%",
                target=80.0,
                threshold_warning=60.0,
                threshold_critical=40.0,
            ))

        if alert_data:
            dashboard.add_kpi(SpecialtyKPI(
                kpi_id="open_alerts",
                name="Alertas em Aberto",
                value=alert_data.open_alerts,
                threshold_warning=2.0,
                threshold_critical=5.0,
            ))

        # Métricas
        if symptom_data:
            dashboard.add_metric(SpecialtyMetric(
                metric_id="baseline_score",
                name="Baseline",
                metric_type=MetricType.COUNT,
                value=symptom_data.baseline_score,
            ))

        if dose_data:
            dashboard.add_metric(SpecialtyMetric(
                metric_id="dose_adjustments",
                name="Ajustes de Dose",
                metric_type=MetricType.COUNT,
                value=dose_data.total_adjustments,
            ))

        # Gráficos
        if symptom_data and symptom_data.dates:
            dashboard.add_chart(SpecialtyChart(
                chart_id="symptom_evolution",
                name=f"Evolução {symptom_data.symptom_name}",
                chart_type=ChartType.LINE,
                data={
                    "x": symptom_data.dates,
                    "y": symptom_data.scores,
                },
            ))

        if dose_data and dose_data.dates:
            dashboard.add_chart(SpecialtyChart(
                chart_id="dose_evolution",
                name="Evolução de Dose",
                chart_type=ChartType.LINE,
                data={
                    "x": dose_data.dates,
                    "y": dose_data.doses_mg,
                },
            ))

        if adherence_data:
            dashboard.add_chart(SpecialtyChart(
                chart_id="adherence_pie",
                name="Adesão",
                chart_type=ChartType.PIE,
                data={
                    "labels": ["Completados", "Perdidos"],
                    "values": [
                        adherence_data.completed_checkpoints,
                        adherence_data.missed_checkpoints,
                    ],
                },
            ))

        if alert_data and alert_data.by_type:
            dashboard.add_chart(SpecialtyChart(
                chart_id="alerts_by_type",
                name="Alertas por Tipo",
                chart_type=ChartType.BAR,
                data={
                    "x": list(alert_data.by_type.keys()),
                    "y": list(alert_data.by_type.values()),
                },
            ))

        return dashboard
