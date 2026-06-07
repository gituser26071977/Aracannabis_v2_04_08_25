"""
AraOS Clinical — Summary Engine.

Gera resumos clínicos estruturados baseados em regras.
NÃO usa LLM — apenas lógica determinística.
"""

from .engine import ClinicalSummaryEngine, SummaryResult

__all__ = ["ClinicalSummaryEngine", "SummaryResult"]
