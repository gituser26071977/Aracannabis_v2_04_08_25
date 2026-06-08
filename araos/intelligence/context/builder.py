"""
AraOS Intelligence — Clinical Context Builder.

Transforma dados clínicos (Digital Twin, Summary, Timeline, Events)
em contexto formatado para LLM.

Responsabilidades:
    - Serialização segura de dados clínicos
    - Token budgeting
    - Truncation strategies
    - Context versioning

Week 7B — Intelligence Layer v1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from araos.clinical.twin.models import PatientDigitalTwin
from araos.clinical.timeline.models import ClinicalTimeline, TimelineEntry
from araos.clinical.summary.engine import SummaryResult


@dataclass
class ClinicalContext:
    """
    Contexto clínico formatado para LLM.
    
    Attributes:
        system_prompt: Instruções de sistema para o LLM
        patient_context: Dados do paciente serializados
        twin_summary: Resumo do Digital Twin
        timeline_entries: Entradas recentes da timeline
        metadata: Metadados do contexto (versão, tamanho, etc.)
    """
    system_prompt: str
    patient_context: str
    twin_summary: str
    timeline_entries: str
    metadata: Dict[str, Any]


class ClinicalContextBuilder:
    """
    Builder para contexto clínico de LLM.
    
    Uso:
        builder = ClinicalContextBuilder(max_tokens=4000)
        context = builder.build(twin=twin, timeline_entries=entries)
        
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=context.system_prompt),
            LLMMessage(role=MessageRole.USER, content=context.patient_context),
        ]
    """
    
    DEFAULT_MAX_TOKENS = 4000
    TOKENS_PER_CHAR = 0.25  # Heurística aproximada para português
    
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.max_tokens = max_tokens
        self.max_chars = int(max_tokens / self.TOKENS_PER_CHAR)
    
    def build(
        self,
        twin: PatientDigitalTwin,
        timeline_entries: Optional[List[TimelineEntry]] = None,
        patient_question: str = "",
    ) -> ClinicalContext:
        """
        Constrói contexto clínico completo.
        
        Args:
            twin: PatientDigitalTwin do paciente
            timeline_entries: Entradas recentes da timeline (opcional)
            patient_question: Pergunta do paciente/médico (opcional)
        
        Returns:
            ClinicalContext formatado
        """
        # 1. System prompt
        system_prompt = self._build_system_prompt()
        
        # 2. Contexto do paciente (dados estruturados)
        patient_context = self._build_patient_context(twin)
        
        # 3. Resumo do twin
        twin_summary = self._build_twin_summary(twin)
        
        # 4. Timeline
        timeline_str = self._build_timeline(timeline_entries or [])
        
        # 5. Orquestrar com budgeting
        full_context = self._orchestrate_context(
            system_prompt=system_prompt,
            patient_context=patient_context,
            twin_summary=twin_summary,
            timeline_str=timeline_str,
            patient_question=patient_question,
        )
        
        # 6. Metadados
        total_chars = len(full_context)
        estimated_tokens = int(total_chars * self.TOKENS_PER_CHAR)
        
        metadata = {
            "version": "1.0",
            "max_tokens_budget": self.max_tokens,
            "estimated_tokens": estimated_tokens,
            "total_chars": total_chars,
            "truncation_applied": estimated_tokens > self.max_tokens,
            "has_twin": twin is not None,
            "has_timeline": bool(timeline_entries),
        }
        
        return ClinicalContext(
            system_prompt=system_prompt,
            patient_context=patient_context,
            twin_summary=twin_summary,
            timeline_entries=timeline_str,
            metadata=metadata,
        )
    
    def _build_system_prompt(self) -> str:
        """Constrói prompt de sistema com restrições clínicas."""
        return (
            "Você é Ara, assistente inteligente de uma clínica médica.\n"
            "REGRAS:\n"
            "1. NUNCA faça diagnósticos médicos.\n"
            "2. NUNCA prescreva medicamentos.\n"
            "3. NUNCA substitua o julgamento de um profissional de saúde.\n"
            "4. SEMPRE baseie suas respostas nos dados fornecidos.\n"
            "5. Se não tiver informação suficiente, diga que não sabe.\n"
            "6. Para informações clínicas, indique que o médico deve confirmar.\n"
        )
    
    def _build_patient_context(self, twin: PatientDigitalTwin) -> str:
        """Serializa dados estruturados do paciente."""
        if not twin or not twin.profile:
            return "[Paciente sem dados clínicos registrados]"
        
        lines = ["=== DADOS DO PACIENTE ==="]
        
        # Diagnósticos
        if twin.active_diagnoses:
            lines.append("\nDiagnósticos ativos:")
            for d in twin.active_diagnoses:
                lines.append(f"  - {d.get('description', 'N/A')} (ICD-10: {d.get('icd10_code', 'N/A')})")
        
        # Medicações
        if twin.active_medications:
            lines.append("\nMedicações ativas:")
            for m in twin.active_medications:
                lines.append(f"  - {m.get('name', 'N/A')} {m.get('dosage', '')} {m.get('frequency', '')}")
        
        # Alergias
        if twin.allergies:
            lines.append("\nAlergias:")
            for a in twin.allergies:
                lines.append(f"  - {a.get('substance', 'N/A')} [{a.get('severity', 'N/A')}]")
        
        # Fatores de risco
        if twin.risk_factors:
            lines.append("\nFatores de risco:")
            for r in twin.risk_factors:
                lines.append(f"  - {r.get('factor_type', 'N/A')} [{r.get('severity', 'N/A')}]")
        
        return "\n".join(lines)
    
    def _build_twin_summary(self, twin: PatientDigitalTwin) -> str:
        """Extrai resumo do twin."""
        if not twin or not twin.summary:
            return "[Sem resumo clínico disponível]"
        
        lines = ["=== RESUMO CLÍNICO ===", twin.summary.text]
        
        if twin.summary.warnings:
            lines.append("\nALERTAS:")
            for w in twin.summary.warnings:
                lines.append(f"  ⚠️  {w}")
        
        return "\n".join(lines)
    
    def _build_timeline(self, entries: List[TimelineEntry]) -> str:
        """Serializa entradas da timeline."""
        if not entries:
            return "[Sem eventos recentes na timeline]"
        
        lines = ["=== TIMELINE RECENTE ==="]
        for e in entries[:10]:  # Limitar a 10 entradas
            lines.append(f"  [{e.event_type}] {e.title}")
            if e.description:
                lines.append(f"    {e.description[:100]}")
        
        return "\n".join(lines)
    
    def _orchestrate_context(
        self,
        system_prompt: str,
        patient_context: str,
        twin_summary: str,
        timeline_str: str,
        patient_question: str,
    ) -> str:
        """
        Orquestra o contexto final com token budgeting.
        
        Prioridade (mais importante primeiro):
            1. System prompt
            2. Resumo clínico
            3. Dados estruturados
            4. Timeline
            5. Pergunta do paciente
        """
        parts = [
            system_prompt,
            twin_summary,
            patient_context,
            timeline_str,
        ]
        
        if patient_question:
            parts.append(f"=== PERGUNTA DO USUÁRIO ===\n{patient_question}")
        
        full = "\n\n".join(parts)
        
        # Truncation se necessário
        if len(full) > self.max_chars:
            # Truncar da parte menos importante (timeline primeiro, depois dados estruturados)
            max_without_timeline = self.max_chars - len(system_prompt) - len(twin_summary) - len(patient_question) - 100
            
            if len(timeline_str) > max_without_timeline // 3:
                timeline_str = timeline_str[:max_without_timeline // 3] + "\n[... timeline truncada ...]"
            
            full = "\n\n".join([
                system_prompt,
                twin_summary,
                patient_context,
                timeline_str,
                f"=== PERGUNTA ===\n{patient_question}" if patient_question else "",
            ]).strip()
            
            if len(full) > self.max_chars:
                full = full[:self.max_chars] + "\n[... contexto truncado ...]"
        
        return full
