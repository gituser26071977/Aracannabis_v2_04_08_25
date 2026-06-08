"""
AraOS Cannabis Module — Outcome Engine.

Avalia evolução longitudinal de sintomas e outcomes.

Week 11B — Cannabis Module V1

IMPORTANTE:
    Sem inferência clínica.
    Apenas análise matemática de scores ao longo do tempo.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TrendDirection(str, Enum):
    """Direção da tendência."""
    IMPROVING = "improving"
    WORSENING = "worsening"
    STABLE = "stable"
    INCONCLUSIVE = "inconclusive"


@dataclass
class OutcomeScore:
    """Pontuação de outcome em um momento."""
    score_id: str
    metric_name: str  # pain, anxiety, sleep, mood, spasticity, seizures, qol
    score: float
    max_score: float = 10.0
    unit: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: str = ""  # baseline, followup, checkpoint
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score_id": self.score_id,
            "metric_name": self.metric_name,
            "score": self.score,
            "max_score": self.max_score,
            "unit": self.unit,
            "recorded_at": self.recorded_at.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }

    def normalized(self) -> float:
        """Score normalizado 0.0-1.0."""
        if self.max_score == 0:
            return 0.0
        return self.score / self.max_score


@dataclass
class OutcomeAnalysis:
    """Resultado da análise de outcome."""
    metric_name: str
    baseline_score: float
    current_score: float
    best_score: float
    worst_score: float
    change_absolute: float
    change_percent: float
    trend: TrendDirection
    response_speed_days: Optional[float] = None
    is_significant: bool = False
    significance_threshold: float = 0.2  # 20% de mudança

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_score": self.baseline_score,
            "current_score": self.current_score,
            "best_score": self.best_score,
            "worst_score": self.worst_score,
            "change_absolute": round(self.change_absolute, 2),
            "change_percent": round(self.change_percent, 2),
            "trend": self.trend.value,
            "response_speed_days": self.response_speed_days,
            "is_significant": self.is_significant,
        }


class CannabisOutcome:
    """
    Outcome de cannabis para um paciente.

    Registra scores ao longo do tempo para múltiplas métricas.
    """

    def __init__(self, patient_id: str, tenant_id: str):
        self.patient_id = patient_id
        self.tenant_id = tenant_id
        self._scores: List[OutcomeScore] = []

    def add_score(self, score: OutcomeScore) -> None:
        """Adiciona uma pontuação."""
        self._scores.append(score)

    def get_scores(self, metric_name: str) -> List[OutcomeScore]:
        """Recupera scores para uma métrica."""
        return sorted(
            [s for s in self._scores if s.metric_name == metric_name],
            key=lambda s: s.recorded_at,
        )

    def get_baseline(self, metric_name: str) -> Optional[OutcomeScore]:
        """Recupera baseline de uma métrica."""
        scores = self.get_scores(metric_name)
        baselines = [s for s in scores if s.context == "baseline"]
        return baselines[0] if baselines else (scores[0] if scores else None)

    def get_latest(self, metric_name: str) -> Optional[OutcomeScore]:
        """Recupera score mais recente."""
        scores = self.get_scores(metric_name)
        return scores[-1] if scores else None

    def get_best(self, metric_name: str) -> Optional[OutcomeScore]:
        """Recupera melhor score (menor = melhor para dor/ansiedade)."""
        scores = self.get_scores(metric_name)
        return min(scores, key=lambda s: s.score) if scores else None

    def get_worst(self, metric_name: str) -> Optional[OutcomeScore]:
        """Recupera pior score."""
        scores = self.get_scores(metric_name)
        return max(scores, key=lambda s: s.score) if scores else None

    def to_dict(self) -> Dict[str, Any]:
        metrics = set(s.metric_name for s in self._scores)
        return {
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "total_scores": len(self._scores),
            "metrics_tracked": list(metrics),
            "scores_by_metric": {
                m: [s.to_dict() for s in self.get_scores(m)]
                for m in metrics
            },
        }


class OutcomeEngine:
    """
    Motor de análise de outcomes.

    Análise matemática pura — sem inferência clínica.

    Calcula:
        - melhora percentual
        - piora percentual
        - tendência
        - estabilidade
        - velocidade de resposta
    """

    def analyze(
        self,
        outcome: CannabisOutcome,
        metric_name: str,
        significance_threshold: float = 0.2,
    ) -> Optional[OutcomeAnalysis]:
        """
        Analisa evolução de uma métrica.

        Args:
            outcome: Objeto de outcome
            metric_name: Nome da métrica
            significance_threshold: Threshold para significância (0.0-1.0)

        Returns:
            OutcomeAnalysis com resultados matemáticos
        """
        baseline = outcome.get_baseline(metric_name)
        current = outcome.get_latest(metric_name)
        best = outcome.get_best(metric_name)
        worst = outcome.get_worst(metric_name)

        if not baseline or not current:
            return None

        # Mudança absoluta
        change_abs = current.score - baseline.score

        # Mudança percentual
        if baseline.score == 0:
            change_pct = 0.0 if current.score == 0 else 100.0
        else:
            change_pct = ((current.score - baseline.score) / baseline.score) * 100

        # Para métricas onde MENOR é melhor (dor, ansiedade):
        # change_percent negativo = melhora
        # Para métricas onde MAIOR é melhor (qol, sono):
        # change_percent positivo = melhora
        is_inverse = metric_name in ("pain", "anxiety", "spasticity", "seizures")

        if is_inverse:
            effective_change = -change_pct  # Inverter para melhora ser positiva
        else:
            effective_change = change_pct

        # Tendência
        trend = self._calculate_trend(outcome, metric_name, is_inverse)

        # Velocidade de resposta
        response_speed = None
        if baseline and current and trend == TrendDirection.IMPROVING:
            scores = outcome.get_scores(metric_name)
            for i, score in enumerate(scores):
                if score.context == "baseline":
                    continue
                effective_score_change = (baseline.score - score.score) / baseline.score if is_inverse and baseline.score > 0 else (score.score - baseline.score) / baseline.score
                if effective_score_change >= significance_threshold:
                    delta = score.recorded_at - baseline.recorded_at
                    response_speed = delta.days + delta.seconds / 86400
                    break

        # Significância
        is_significant = abs(effective_change / 100) >= significance_threshold

        return OutcomeAnalysis(
            metric_name=metric_name,
            baseline_score=baseline.score,
            current_score=current.score,
            best_score=best.score if best else current.score,
            worst_score=worst.score if worst else baseline.score,
            change_absolute=change_abs,
            change_percent=effective_change,
            trend=trend,
            response_speed_days=response_speed,
            is_significant=is_significant,
            significance_threshold=significance_threshold,
        )

    def analyze_all(self, outcome: CannabisOutcome) -> Dict[str, OutcomeAnalysis]:
        """Analisa todas as métricas."""
        metrics = set(s.metric_name for s in outcome._scores)
        return {
            m: analysis
            for m in metrics
            if (analysis := self.analyze(outcome, m)) is not None
        }

    def _calculate_trend(
        self,
        outcome: CannabisOutcome,
        metric_name: str,
        is_inverse: bool,
    ) -> TrendDirection:
        """Calcula tendência baseada nos últimos 3 scores."""
        scores = outcome.get_scores(metric_name)
        if len(scores) < 3:
            return TrendDirection.INCONCLUSIVE

        recent = scores[-3:]
        changes = []
        for i in range(1, len(recent)):
            changes.append(recent[i].score - recent[i - 1].score)

        avg_change = sum(changes) / len(changes)

        if is_inverse:
            # Menor = melhor
            if avg_change < -0.5:
                return TrendDirection.IMPROVING
            elif avg_change > 0.5:
                return TrendDirection.WORSENING
        else:
            # Maior = melhor
            if avg_change > 0.5:
                return TrendDirection.IMPROVING
            elif avg_change < -0.5:
                return TrendDirection.WORSENING

        return TrendDirection.STABLE

    def generate_summary_text(self, analysis: OutcomeAnalysis) -> str:
        """Gera texto de resumo matemático (não clínico)."""
        direction = "melhora" if analysis.trend == TrendDirection.IMPROVING else (
            "piora" if analysis.trend == TrendDirection.WORSENING else "estabilidade"
        )
        return (
            f"{analysis.metric_name}: {analysis.baseline_score:.1f} → {analysis.current_score:.1f} "
            f"({analysis.change_percent:+.1f}% — {direction})"
        )
