"""
AraOS Intelligence — Voice Copilot Agent.

Agente de consulta read-only sobre dados do paciente.

Capacidades:
    - "Ara, resumo do paciente"
    - "Ara, medicamentos atuais"
    - "Ara, alergias registradas"
    - "Ara, histórico de diagnósticos"

RESTRIÇÕES:
    - APENAS leitura de dados estruturados
    - NUNCA faz inferências clínicas
    - NUNCA sugere tratamentos
    - Fonte sempre STRUCTURED_DATA ou GENERATED_SUMMARY

Week 7B — Intelligence Layer v1
"""

from typing import Dict, Any

from araos.agents.runtime.agent import BaseAgent, AgentCapability, AgentResult
from araos.agents.runtime.context import AgentContext
from araos.intelligence.trust.levels import TrustedResponse, SourceType, TrustLevel
from araos.intelligence.llm import LLMMessage, MessageRole
from araos.intelligence.runtime.runtime import LLMRuntime
from araos.intelligence.context.builder import ClinicalContextBuilder


class VoiceCopilotAgent(BaseAgent):
    """
    Agente Voice Copilot — consulta read-only.
    
    Recebe comandos de voz de médicos e responde com dados
    estruturados do paciente, sempre com proveniência.
    
    Uso:
        agent = VoiceCopilotAgent(llm_runtime)
        result = await agent.execute(context)
    """
    
    def __init__(self, llm_runtime: LLMRuntime):
        super().__init__(
            agent_id="voice_copilot_intelligent",
            name="Ara Voice Copilot",
            version="1.0.0",
            capabilities=[
                AgentCapability.VOICE,
                AgentCapability.CLINICAL_SUMMARY,
            ],
            required_permissions=[
                "voice.use",
                "patient.read",
                "consultation.read",
            ],
            description="Assistente de voz para médicos — consulta read-only de dados clínicos.",
        )
        self.llm_runtime = llm_runtime
        self.context_builder = ClinicalContextBuilder(max_tokens=2000)
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Executa o agente Voice Copilot.
        
        Args:
            context.input_data deve conter:
                - "command": str — comando de voz do médico
                - "consultation_id": str — ID da consulta atual
        
        Returns:
            AgentResult com resposta confiável baseada em dados estruturados
        """
        command = context.input_data.get("command", "")
        consultation_id = context.input_data.get("consultation_id", "")
        
        # 1. Analisar comando
        query_type = self._classify_query(command)
        
        # 2. Obter dados do paciente
        twin = context.patient_twin
        
        if not twin:
            return AgentResult(
                success=False,
                output={"error": "PatientDigitalTwin não disponível"},
                message="Não foi possível carregar os dados do paciente.",
                error="MISSING_TWIN",
            )
        
        # 3. Responder baseado no tipo de consulta
        response = await self._build_response(query_type, command, twin, context)
        
        # 4. Construir resultado
        output = {
            "response": response.to_dict(),
            "query_type": query_type,
            "consultation_id": consultation_id,
            "patient_id": context.patient_id,
            "requires_human_verification": response.requires_human_verification(),
        }
        
        return AgentResult(
            success=True,
            output=output,
            message=response.content,
        )
    
    def _classify_query(self, command: str) -> str:
        """
        Classifica o tipo de consulta do médico.
        
        Tipos:
            - summary: resumo geral do paciente
            - medications: lista de medicamentos
            - allergies: lista de alergias
            - diagnoses: diagnósticos ativos
            - timeline: timeline recente
            - unknown: não reconhecido
        """
        cmd_lower = command.lower()
        
        if any(kw in cmd_lower for kw in ["resumo", "summary", "paciente", "patient"]):
            return "summary"
        if any(kw in cmd_lower for kw in ["medicamento", "medicação", "remédio", "medication", "drug"]):
            return "medications"
        if any(kw in cmd_lower for kw in ["alergia", "allergy", "alérgico"]):
            return "allergies"
        if any(kw in cmd_lower for kw in ["diagnóstico", "diagnosis", "doença", "condition"]):
            return "diagnoses"
        if any(kw in cmd_lower for kw in ["timeline", "histórico", "history", "eventos"]):
            return "timeline"
        
        return "unknown"
    
    async def _build_response(
        self,
        query_type: str,
        command: str,
        twin,
        context: AgentContext,
    ) -> TrustedResponse:
        """Constrói resposta baseada em dados estruturados."""
        
        if query_type == "summary":
            return self._build_summary_response(twin)
        
        elif query_type == "medications":
            return self._build_medications_response(twin)
        
        elif query_type == "allergies":
            return self._build_allergies_response(twin)
        
        elif query_type == "diagnoses":
            return self._build_diagnoses_response(twin)
        
        elif query_type == "timeline":
            return await self._build_timeline_response(twin, context)
        
        else:
            # Query não reconhecida — usar LLM apenas para reformular
            return await self._build_unknown_response(command, twin, context)
    
    def _build_summary_response(self, twin) -> TrustedResponse:
        """Resposta com resumo clínico do paciente."""
        if twin.summary and twin.summary.text:
            content = twin.summary.text
            source = SourceType.GENERATED_SUMMARY
            trust = TrustLevel.GENERATED_SUMMARY
        else:
            # Fallback para dados estruturados
            parts = ["Resumo do paciente:"]
            if twin.active_diagnoses:
                parts.append(f"Diagnósticos: {', '.join(d.get('description', '') for d in twin.active_diagnoses)}")
            if twin.active_medications:
                parts.append(f"Medicações: {', '.join(m.get('name', '') for m in twin.active_medications)}")
            if twin.allergies:
                parts.append(f"Alergias: {', '.join(a.get('substance', '') for a in twin.allergies)}")
            content = "\n".join(parts)
            source = SourceType.STRUCTURED_DATA
            trust = TrustLevel.STRUCTURED_DATA
        
        return TrustedResponse(
            content=content,
            source_type=source,
            trust_level=trust,
            provider="voice_copilot",
            model="rules",
        )
    
    def _build_medications_response(self, twin) -> TrustedResponse:
        """Resposta com lista de medicamentos."""
        if not twin.active_medications:
            content = "O paciente não tem medicações ativas registradas."
        else:
            lines = ["Medicações ativas:"]
            for m in twin.active_medications:
                lines.append(f"  • {m.get('name', 'N/A')} {m.get('dosage', '')} — {m.get('frequency', '')}")
            content = "\n".join(lines)
        
        return TrustedResponse(
            content=content,
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="voice_copilot",
            model="rules",
        )
    
    def _build_allergies_response(self, twin) -> TrustedResponse:
        """Resposta com lista de alergias."""
        if not twin.allergies:
            content = "O paciente não tem alergias registradas."
        else:
            lines = ["Alergias registradas:"]
            for a in twin.allergies:
                lines.append(f"  • {a.get('substance', 'N/A')} [{a.get('severity', 'N/A')}]")
                if a.get('reaction'):
                    lines.append(f"    Reação: {a.get('reaction')}")
            content = "\n".join(lines)
        
        return TrustedResponse(
            content=content,
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="voice_copilot",
            model="rules",
        )
    
    def _build_diagnoses_response(self, twin) -> TrustedResponse:
        """Resposta com diagnósticos ativos."""
        if not twin.active_diagnoses:
            content = "O paciente não tem diagnósticos ativos registrados."
        else:
            lines = ["Diagnósticos ativos:"]
            for d in twin.active_diagnoses:
                lines.append(f"  • {d.get('description', 'N/A')}")
                if d.get('icd10_code'):
                    lines.append(f"    ICD-10: {d.get('icd10_code')}")
                if d.get('is_chronic'):
                    lines.append(f"    [Crônico]")
            content = "\n".join(lines)
        
        return TrustedResponse(
            content=content,
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="voice_copilot",
            model="rules",
        )
    
    async def _build_timeline_response(self, twin, context) -> TrustedResponse:
        """Resposta com timeline recente."""
        entries = twin.get_timeline_entries(limit=5)
        
        if not entries:
            content = "Não há eventos recentes na timeline do paciente."
        else:
            lines = ["Eventos recentes:"]
            for e in entries:
                lines.append(f"  • [{e.event_type}] {e.title}")
            content = "\n".join(lines)
        
        return TrustedResponse(
            content=content,
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="voice_copilot",
            model="rules",
        )
    
    async def _build_unknown_response(self, command, twin, context) -> TrustedResponse:
        """Resposta para comandos não reconhecidos."""
        # Usar LLM apenas para formular resposta educada, não para inferir dados
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Você é o assistente de voz Ara. "
                    "O médico deu um comando que você não reconheceu. "
                    "Responda educadamente listando o que você pode fazer: "
                    "resumo, medicamentos, alergias, diagnósticos, timeline."
                ),
            ),
            LLMMessage(role=MessageRole.USER, content=command),
        ]
        
        return await self.llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
