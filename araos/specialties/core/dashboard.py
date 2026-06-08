"""
AraOS Specialty Framework — Specialty Dashboard.

Contratos para KPIs, métricas, gráficos e indicadores.

Week 10 — Specialty Framework Foundation

IMPORTANTE:
    Sem implementação de frontend.
    Apenas modelos e contratos para que cada especialidade
    possa declarar quais métricas e KPIs fornece.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MetricType(str, Enum):
    """Tipo de métrica."""
    COUNT = "count"
    AVERAGE = "average"
    SUM = "sum"
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    TREND = "trend"
    DISTRIBUTION = "distribution"
    TIMESERIES = "timeseries"


class ChartType(str, Enum):
    """Tipo de visualização."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    TABLE = "table"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    SCATTER = "scatter"


class KpiSeverity(str, Enum):
    """Severidade de um KPI."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"


@dataclass
class SpecialtyMetric:
    """Métrica especializada."""
    metric_id: str
    name: str
    metric_type: MetricType
    value: Any
    unit: str = ""
    description: str = ""
    target_value: Optional[Any] = None
    trend_direction: str = ""  # up, down, stable
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "name": self.name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "unit": self.unit,
            "description": self.description,
            "target_value": self.target_value,
            "trend_direction": self.trend_direction,
            "metadata": self.metadata,
        }


@dataclass
class SpecialtyKPI:
    """Indicador chave de performance especializado."""
    kpi_id: str
    name: str
    value: Any
    unit: str = ""
    target: Optional[Any] = None
    threshold_warning: Optional[Any] = None
    threshold_critical: Optional[Any] = None
    severity: KpiSeverity = KpiSeverity.INFO
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "target": self.target,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "severity": self.severity.value,
            "description": self.description,
            "metadata": self.metadata,
        }

    def evaluate(self) -> KpiSeverity:
        """Avalia a severidade baseada nos thresholds."""
        if self.threshold_critical is not None and self.value is not None:
            try:
                if self.value >= self.threshold_critical:
                    return KpiSeverity.CRITICAL
            except TypeError:
                pass

        if self.threshold_warning is not None and self.value is not None:
            try:
                if self.value >= self.threshold_warning:
                    return KpiSeverity.WARNING
            except TypeError:
                pass

        return KpiSeverity.NORMAL


@dataclass
class SpecialtyChart:
    """Configuração de gráfico especializado."""
    chart_id: str
    name: str
    chart_type: ChartType
    data: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "name": self.name,
            "chart_type": self.chart_type.value,
            "data": self.data,
            "config": self.config,
            "description": self.description,
        }


class SpecialtyDashboard:
    """
    Dashboard especializado.

    Contrato para que cada especialidade declare seus
    KPIs, métricas e gráficos.

    Uso:
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_kpi(SpecialtyKPI(...))
        dashboard.add_metric(SpecialtyMetric(...))
        dashboard.add_chart(SpecialtyChart(...))
        data = dashboard.to_dict()
    """

    def __init__(self, specialty_code: str, name: str = ""):
        self.specialty_code = specialty_code
        self.name = name or f"Dashboard — {specialty_code}"
        self._kpis: List[SpecialtyKPI] = []
        self._metrics: List[SpecialtyMetric] = []
        self._charts: List[SpecialtyChart] = []
        self._metadata: Dict[str, Any] = {}

    def add_kpi(self, kpi: SpecialtyKPI) -> None:
        """Adiciona um KPI."""
        self._kpis.append(kpi)

    def add_metric(self, metric: SpecialtyMetric) -> None:
        """Adiciona uma métrica."""
        self._metrics.append(metric)

    def add_chart(self, chart: SpecialtyChart) -> None:
        """Adiciona um gráfico."""
        self._charts.append(chart)

    def get_kpis(self, severity: Optional[KpiSeverity] = None) -> List[SpecialtyKPI]:
        """Recupera KPIs, opcionalmente filtrados por severidade."""
        if severity:
            return [k for k in self._kpis if k.severity == severity]
        return self._kpis.copy()

    def get_metrics(self, metric_type: Optional[MetricType] = None) -> List[SpecialtyMetric]:
        """Recupera métricas, opcionalmente filtradas por tipo."""
        if metric_type:
            return [m for m in self._metrics if m.metric_type == metric_type]
        return self._metrics.copy()

    def get_charts(self, chart_type: Optional[ChartType] = None) -> List[SpecialtyChart]:
        """Recupera gráficos, opcionalmente filtrados por tipo."""
        if chart_type:
            return [c for c in self._charts if c.chart_type == chart_type]
        return self._charts.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialty_code": self.specialty_code,
            "name": self.name,
            "kpi_count": len(self._kpis),
            "metric_count": len(self._metrics),
            "chart_count": len(self._charts),
            "kpis": [k.to_dict() for k in self._kpis],
            "metrics": [m.to_dict() for m in self._metrics],
            "charts": [c.to_dict() for c in self._charts],
            "metadata": self._metadata,
        }


class SpecialtyMetricsCollector:
    """
    Coletor de métricas especializadas.

    Responsável por calcular e agregar métricas de uma especialidade.
    """

    def __init__(self, specialty_code: str):
        self.specialty_code = specialty_code
        self._metrics: List[SpecialtyMetric] = []

    def record(self, metric: SpecialtyMetric) -> None:
        """Registra uma métrica."""
        self._metrics.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo de todas as métricas."""
        by_type: Dict[str, List[Any]] = {}
        for m in self._metrics:
            key = m.metric_type.value
            by_type.setdefault(key, []).append(m.value)

        return {
            "specialty_code": self.specialty_code,
            "total_metrics": len(self._metrics),
            "by_type": {k: len(v) for k, v in by_type.items()},
        }

    def clear(self) -> None:
        """Limpa métricas."""
        self._metrics.clear()
