"""
AraOS Cannabis Module — Agent.

Agente especializado para Cannabis Medicinal.

Week 11B — Cannabis Module V1

IMPORTANTE:
    Todas as respostas baseadas em dados estruturados.
    Nenhuma inferência clínica sem identificação explícita.
    Trust Levels: STRUCTURED_DATA | GENERATED_SUMMARY | AI_INFERENCE
"""

from typing import Dict, Any, List, Optional

from araos.agents.runtime.agent import BaseAgent, AgentCapability, AgentResult
from araos.agents.runtime.context import AgentContext
from araos.intelligence.trust.levels import SourceType, TrustLevel, TrustedResponse

from araos.specialties.cannabis.profile.models import CannabisProfile
from araos.specialties.cannabis.dose.models import CannabisDoseTimeline
from araos.specialties.cannabis.outcome.engine import CannabisOutcome, OutcomeEngine
from araos.specialties.cannabis.alerts.models import CannabisAlertManager


class CannabisAgent(BaseAgent):
    """
    Agente especializado para Cannabis Medicinal.

    Capacidades:
        - Resumo terapêutico
        - Evolução longitudinal
        - Histórico de doses
        - Histórico de produtos
        - Efeitos adversos registrados
        - Adesão

    Exemplos de consultas:
        "Como evoluiu a dor?"
        "Qual foi a resposta após aumento da dose?"
        "Quais efeitos adversos foram registrados?"

    Sempre baseado em dados estruturados.
    """

    def __init__(self):
        super().__init__(
            agent_id="cannabis_specialist",
            name="AraOS Cannabis Specialist",
            version="1.0.0",
            capabilities=[
                AgentCapability.CLINICAL_SUMMARY,
                AgentCapability.DECISION_SUPPORT,
            ],
            required_permissions=["patient.read", "medication.read", "followup.read"],
        )
        self.outcome_engine = OutcomeEngine()

    async def execute(self, context: AgentContext) -> AgentResult:
        """Executa o agente Cannabis."""
        query = context.input_data.get("query", "")
        patient_id = context.input_data.get("patient_id", "")

        if not patient_id:
            return AgentResult(
                success=False,
                output={"error": "patient_id required"},
            )

        # Stub: em produção, buscaria do Digital Twin / Repository
        response = self._generate_response(query, patient_id, context)

        return AgentResult(
            success=True,
            output=response,
        )

    def _generate_response(self, query: str, patient_id: str, context: AgentContext) -> Dict[str, Any]:
        """Gera resposta baseada em dados estruturados."""
        # Stub: framework para respostas baseadas em dados
        return {
            "patient_id": patient_id,
            "query": query,
            "response_type": "structured_data",
            "trust_level": TrustLevel.STRUCTURED_DATA.value,
            "source_type": SourceType.STRUCTURED_DATA.value,
            "message": f"Resposta baseada em dados estruturados para: {query}",
            "requires_verification": False,
        }

    def generate_therapeutic_summary(
        self,
        profile: CannabisProfile,
        dose_timeline: CannabisDoseTimeline,
        outcome: CannabisOutcome,
        alert_manager: CannabisAlertManager,
    ) -> TrustedResponse:
        """
        Gera resumo terapêutico completo.

        Trust Level: GENERATED_SUMMARY (rules-based, não AI)
        """
        # Análise de doses
        dose_summary = dose_timeline.calculate_titration_summary()

        # Análise de outcomes
        analyses = self.outcome_engine.analyze_all(outcome)

        # Alertas em aberto
        open_alerts = alert_manager.get_alerts(patient_id=profile.patient_id, open_only=True)

        summary_parts = [
            f"Resumo Terapêutico — Paciente {profile.patient_id}",
            "",
            f"Condição Principal: {profile.get_field_value('main_condition', 'N/A')}",
            f"Status: {profile.get_field_value('therapeutic_status', 'N/A')}",
            "",
            "Dose Atual:",
            f"  Dose: {dose_summary.get('current_dose_mg', 'N/A')} mg",
            f"  THC: {dose_summary.get('current_thc_mg', 'N/A')} mg",
            f"  CBD: {dose_summary.get('current_cbd_mg', 'N/A')} mg",
            "",
            "Outcomes:",
        ]

        for metric_name, analysis in analyses.items():
            summary_parts.append(f"  {self.outcome_engine.generate_summary_text(analysis)}")

        if open_alerts:
            summary_parts.extend(["", "Alertas em Aberto:"])
            for alert in open_alerts:
                summary_parts.append(f"  • {alert.title} ({alert.severity.value})")

        content = "\n".join(summary_parts)

        return TrustedResponse(
            content=content,
            source_type=SourceType.GENERATED_SUMMARY,
            trust_level=TrustLevel.GENERATED_SUMMARY,
            provider="cannabis_agent",
            model="rules_based_v1",
            metadata={
                "patient_id": profile.patient_id,
                "dose_changes": dose_summary.get("total_adjustments", 0),
                "metrics_analyzed": len(analyses),
                "open_alerts": len(open_alerts),
            },

        )

    def answer_longitudinal_evolution(
        self,
        outcome: CannabisOutcome,
        metric_name: str,
    ) -> TrustedResponse:
        """
        Responde sobre evolução longitudinal de uma métrica.

        Trust Level: STRUCTURED_DATA
        """
        scores = outcome.get_scores(metric_name)
        if not scores:
            return TrustedResponse(
                content=f"Nenhum dado registrado para {metric_name}.",
                source_type=SourceType.STRUCTURED_DATA,
                trust_level=TrustLevel.STRUCTURED_DATA,
                provider="cannabis_agent",
                model="structured_query",
                metadata={"metric_name": metric_name},
    
            )

        baseline = outcome.get_baseline(metric_name)
        latest = outcome.get_latest(metric_name)
        best = outcome.get_best(metric_name)

        lines = [
            f"Evolução de {metric_name}:",
            "",
            f"Baseline: {baseline.score if baseline else 'N/A'}",
            f"Atual: {latest.score if latest else 'N/A'}",
            f"Melhor: {best.score if best else 'N/A'}",
            f"Registros: {len(scores)}",
        ]

        # Análise matemática
        analysis = self.outcome_engine.analyze(outcome, metric_name)
        if analysis:
            lines.extend([
                "",
                f"Mudança: {analysis.change_percent:+.1f}%",
                f"Tendência: {analysis.trend.value}",
            ])

        return TrustedResponse(
            content="\n".join(lines),
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="cannabis_agent",
            model="structured_query",
            metadata={
                "metric_name": metric_name,
                "score_count": len(scores),
            },

        )

    def answer_dose_history(
        self,
        dose_timeline: CannabisDoseTimeline,
    ) -> TrustedResponse:
        """
        Responde sobre histórico de doses.

        Trust Level: STRUCTURED_DATA
        """
        summary = dose_timeline.calculate_titration_summary()
        entries = dose_timeline.get_entries()

        lines = [
            "Histórico de Doses:",
            "",
            f"Dose Inicial: {summary.get('initial_dose_mg', 'N/A')} mg",
            f"Dose Atual: {summary.get('current_dose_mg', 'N/A')} mg",
            f"Ajustes: {summary.get('total_adjustments', 0)}",
            "",
            "Timeline:",
        ]

        for entry in entries[-5:]:  # Últimas 5 entradas
            lines.append(
                f"  {entry.entry_date.strftime('%Y-%m-%d')}: "
                f"{entry.dose_mg} mg ({entry.entry_type})"
            )

        return TrustedResponse(
            content="\n".join(lines),
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="cannabis_agent",
            model="structured_query",
            metadata={"entry_count": len(entries)},

        )
