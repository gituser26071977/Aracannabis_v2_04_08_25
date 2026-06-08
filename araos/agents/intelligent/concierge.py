"""
AraOS Intelligence — Concierge Agent.

Primeiro agente inteligente oficial do AraOS.

Capacidades:
    - Compreensão de intenção do paciente
    - Triagem administrativa
    - Agendamento de consultas
    - Captura de informações

RESTRIÇÕES:
    - NUNCA faz diagnóstico
    - NUNCA prescreve medicamentos
    - NUNCA recomenda tratamentos
    - SEMPRE encaminha questões clínicas para o médico

Week 7B — Intelligence Layer v1
"""

from typing import Dict, Any, List

from araos.agents.runtime.agent import BaseAgent, AgentCapability, AgentResult
from araos.agents.runtime.context import AgentContext
from araos.intelligence.llm import LLMMessage, MessageRole
from araos.intelligence.runtime.runtime import LLMRuntime
from araos.intelligence.trust.levels import TrustedResponse, SourceType, TrustLevel
from araos.intelligence.context.builder import ClinicalContextBuilder


class ConciergeAgent(BaseAgent):
    """
    Agente Concierge inteligente.
    
    Recebe mensagens de pacientes (WhatsApp, app, web) e responde
    de forma natural, usando LLM quando necessário.
    
    Uso:
        agent = ConciergeAgent(llm_runtime)
        result = await agent.execute(context)
    """
    
    def __init__(self, llm_runtime: LLMRuntime):
        super().__init__(
            agent_id="concierge_intelligent",
            name="Ara Concierge",
            version="1.0.0",
            capabilities=[
                AgentCapability.CHAT,
                AgentCapability.SCHEDULING,
                AgentCapability.NOTIFICATION,
            ],
            required_permissions=[
                "communication.send",
                "patient.read",
                "consultation.schedule",
            ],
            description="Assistente virtual para pacientes — triagem, agendamento e informações administrativas.",
        )
        self.llm_runtime = llm_runtime
        self.context_builder = ClinicalContextBuilder(max_tokens=3000)
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Executa o agente Concierge.
        
        Args:
            context.input_data deve conter:
                - "message": str — mensagem do paciente
                - "channel": str — whatsapp, app, web
        
        Returns:
            AgentResult com resposta confiável
        """
        message = context.input_data.get("message", "")
        channel = context.input_data.get("channel", "unknown")
        
        # 1. Detectar intenção
        intent = self._detect_intent(message)
        
        # 2. Responder baseado na intenção
        if intent == "clinical_question":
            # Questão clínica → NÃO responder com IA
            response = TrustedResponse(
                content=(
                    "Entendo sua preocupação. Questões de saúde devem ser avaliadas "
                    "pelo seu médico. Posso ajudar a agendar uma consulta?"
                ),
                source_type=SourceType.STRUCTURED_DATA,
                trust_level=TrustLevel.STRUCTURED_DATA,
                provider="concierge",
                model="rules",
            )
        
        elif intent == "scheduling":
            response = await self._handle_scheduling(message, context)
        
        elif intent == "information_request":
            response = await self._handle_information_request(message, context)
        
        elif intent == "symptom_report":
            # Capturar sintomas para o médico — NÃO diagnosticar
            response = await self._handle_symptom_report(message, context)
        
        else:
            # Conversa geral — usar LLM com restrições
            response = await self._handle_general_conversation(message, context)
        
        # 3. Construir resultado
        output = {
            "response": response.to_dict(),
            "intent": intent,
            "channel": channel,
            "requires_human_followup": response.requires_human_verification(),
        }
        
        return AgentResult(
            success=True,
            output=output,
            message=response.content,
        )
    
    def _detect_intent(self, message: str) -> str:
        """
        Detecta intenção da mensagem do paciente.
        
        Intenções:
            - clinical_question: perguntas sobre diagnóstico, tratamento
            - scheduling: agendamento, remarcação
            - information_request: informações sobre a clínica
            - symptom_report: relato de sintomas
            - general: conversa geral
        """
        msg_lower = message.lower()
        
        # Clinical question patterns
        clinical_keywords = [
            "diagnóstico", "doença", "tratamento", "remédio", "medicamento",
            "devo tomar", "posso tomar", "é grave", "sério", "câncer",
            "infecção", "virus", "bactéria", "diagnosis", "treatment",
            "medicine", "should i take", "is it serious",
        ]
        if any(kw in msg_lower for kw in clinical_keywords):
            return "clinical_question"
        
        # Scheduling patterns
        scheduling_keywords = [
            "agendar", "consulta", "marcar", "remarcar", "cancelar",
            "horário", "disponível", "schedule", "appointment", "book",
        ]
        if any(kw in msg_lower for kw in scheduling_keywords):
            return "scheduling"
        
        # Symptom report patterns
        symptom_keywords = [
            "dor", "febre", "tontura", "náusea", "vômito", "cansaço",
            "mal estar", "sintoma", "estou sentindo", "pain", "fever",
            "dizzy", "nausea", "symptom", "feeling",
        ]
        if any(kw in msg_lower for kw in symptom_keywords):
            return "symptom_report"
        
        # Information request
        info_keywords = [
            "endereço", "telefone", "horário", "funcionamento", "convênio",
            "preço", "custo", "address", "phone", "hours", "insurance",
        ]
        if any(kw in msg_lower for kw in info_keywords):
            return "information_request"
        
        return "general"
    
    async def _handle_scheduling(
        self,
        message: str,
        context: AgentContext,
    ) -> TrustedResponse:
        """Processa solicitações de agendamento."""
        # Usar LLM para extrair intenção de agendamento
        prompt = (
            "O paciente quer agendar uma consulta. "
            "Responda de forma útil e pergunte o dia/horário preferido. "
            "Não faça promessas de horários específicos."
        )
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=prompt),
            LLMMessage(role=MessageRole.USER, content=message),
        ]
        
        return await self.llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
    
    async def _handle_information_request(
        self,
        message: str,
        context: AgentContext,
    ) -> TrustedResponse:
        """Processa solicitações de informação."""
        # Respostas baseadas em dados estruturados quando possível
        # Usar LLM apenas para formatação
        
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Você é o assistente da clínica. "
                    "Responda perguntas administrativas (endereço, horários, convênios). "
                    "Se não souber a resposta, diga que vai verificar."
                ),
            ),
            LLMMessage(role=MessageRole.USER, content=message),
        ]
        
        return await self.llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
    
    async def _handle_symptom_report(
        self,
        message: str,
        context: AgentContext,
    ) -> TrustedResponse:
        """
        Processa relato de sintomas.
        
        IMPORTANTE: NÃO diagnostica. Apenas registra e encaminha.
        """
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "O paciente está relatando sintomas. "
                    "Agradeça pelo relato. Diga que os sintomas serão registrados "
                    "e avaliados pelo médico durante a consulta. "
                    "NÃO faça diagnóstico. NÃO recomende tratamento."
                ),
            ),
            LLMMessage(role=MessageRole.USER, content=message),
        ]
        
        return await self.llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
    
    async def _handle_general_conversation(
        self,
        message: str,
        context: AgentContext,
    ) -> TrustedResponse:
        """Processa conversa geral."""
        messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content=(
                    "Você é Ara, assistente da clínica. "
                    "Seja gentil, prestativo e objetivo. "
                    "NÃO dê conselhos médicos. "
                    "Se a conversa envolver saúde, encaminhe para o médico."
                ),
            ),
            LLMMessage(role=MessageRole.USER, content=message),
        ]
        
        return await self.llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
            correlation_id=context.correlation_id,
            tenant_id=context.tenant_id,
            actor_id=context.actor_id,
        )
