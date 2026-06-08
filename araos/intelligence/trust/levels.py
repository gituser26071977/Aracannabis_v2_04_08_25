"""
AraOS Intelligence — Trust Levels.

Toda resposta de inteligência artificial deve carregar um nível de confiança
e uma fonte de dados. Isso permite que consumidores (médicos, pacientes,
reguladores) entendam a proveniência de cada informação.

Week 7B — Intelligence Layer v1
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any


class TrustLevel(str, Enum):
    """
    Nível de confiança da informação.
    
    Ordem decrescente de confiabilidade:
        STRUCTURED_DATA    → Dado do banco (mais confiável)
        GENERATED_SUMMARY  → Resumo rules-based
        AI_INFERENCE       → Inferência do LLM (menos confiável)
    """
    STRUCTURED_DATA = "structured_data"
    GENERATED_SUMMARY = "generated_summary"
    AI_INFERENCE = "ai_inference"


class SourceType(str, Enum):
    """
    Fonte da informação.
    
    Valores:
        STRUCTURED_DATA    → Dado direto do banco (Digital Twin, Profile)
        GENERATED_SUMMARY  → Resumo gerado pelo ClinicalSummaryEngine
        AI_INFERENCE       → Inferência gerada por LLM
    """
    STRUCTURED_DATA = "structured_data"
    GENERATED_SUMMARY = "generated_summary"
    AI_INFERENCE = "ai_inference"


@dataclass
class TrustedResponse:
    """
    Resposta confiável com proveniência.
    
    Todo consumidor de IA no AraOS recebe um TrustedResponse,
    nunca uma string pura.
    
    Attributes:
        content: Texto da resposta
        source_type: De onde veio a informação
        trust_level: Nível de confiança
        provider: Qual provider LLM gerou (se aplicável)
        model: Qual modelo foi usado (se aplicável)
        metadata: Dados adicionais (latência, tokens, custo, etc.)
    """
    content: str
    source_type: SourceType
    trust_level: TrustLevel
    provider: str = ""
    model: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "source_type": self.source_type.value,
            "trust_level": self.trust_level.value,
            "provider": self.provider,
            "model": self.model,
            "metadata": self.metadata,
        }
    
    def is_structured_data(self) -> bool:
        return self.source_type == SourceType.STRUCTURED_DATA
    
    def is_generated_summary(self) -> bool:
        return self.source_type == SourceType.GENERATED_SUMMARY
    
    def is_ai_inference(self) -> bool:
        return self.source_type == SourceType.AI_INFERENCE
    
    def requires_human_verification(self) -> bool:
        """Retorna True se a informação requer verificação humana."""
        return self.source_type == SourceType.AI_INFERENCE
