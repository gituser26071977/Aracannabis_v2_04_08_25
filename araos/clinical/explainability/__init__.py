"""
AraOS Clinical — Explainability Core (Sprint 4.1).

Toda análise de inteligência clínica DEVE emitir uma Explanation.
Esta é a infraestrutura cross-cutting que torna a IA auditável.

Princípios:
    - IA nunca diagnostica. Nunca substitui o médico.
    - Toda análise responde: por quê, com quais dados, em qual janela,
      com qual confiança, quais eventos contribuíram.
    - Se uma análise é emitida sem Explanation → black-box → DLQ.

API pública:
    Explanation            — value object imutável
    ExplanationRegistry    — ABC para registro
    InMemoryExplanationRegistry    — impl para testes
    SqlAlchemyExplanationRegistry  — impl produção (definida em Sprint 4.5+,
                                     stub InMemory por enquanto)

Reutiliza TimeWindow e VariableSpec de araos.clinical.timeline.domain.
"""

from araos.clinical.explainability.domain.explanation import (
    AnalysisType,
    Explanation,
)
from araos.clinical.explainability.registry import (
    ExplanationRegistry,
    InMemoryExplanationRegistry,
    new_explanation_id,
)

try:
    from araos.clinical.explainability.sql import (
        SqlAlchemyExplanationRegistry,
        IntelligenceExplanationModel,
        REDACTED,
    )
    _SQL_AVAILABLE = True
except ImportError:
    SqlAlchemyExplanationRegistry = None  # type: ignore[misc,assignment]
    IntelligenceExplanationModel = None   # type: ignore[misc,assignment]
    REDACTED = None  # type: ignore[misc,assignment]
    _SQL_AVAILABLE = False

__all__ = [
    "AnalysisType",
    "Explanation",
    "ExplanationRegistry",
    "InMemoryExplanationRegistry",
    "SqlAlchemyExplanationRegistry",
    "IntelligenceExplanationModel",
    "REDACTED",
    "new_explanation_id",
]