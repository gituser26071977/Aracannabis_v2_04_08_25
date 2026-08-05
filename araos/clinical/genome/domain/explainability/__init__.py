"""
araos.clinical.genome.domain.explainability — Explainability cross-cutting.

Reference Implementation — Sprint 4.3 Phase 2.

Note: ``ExplanationSummary`` (o tipo de retorno de ``ClinicalExpression.why()``)
é exportado a partir de ``araos.clinical.genome.domain.expression`` para evitar
importação circular.
"""

from .explanation import Explanation

__all__ = ["Explanation"]