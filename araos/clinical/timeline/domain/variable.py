"""
VariableSpec — especificação de uma variável clínica para análise.

Usado por:
    - Analytics (Sprint 4.3): qual score de escala, qual medida.
    - Correlation (Sprint 4.4): qual par de variáveis correlacionar.
    - ML (Sprint 4.5): feature names.
    - Dashboard (Sprint 4.5): data_source dos gráficos.

VariableSpec é SEMANTICAMENTE um descritor — não o valor.
O valor vem dos eventos (extraído por `value_extractor`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class VariableSource(str, Enum):
    """De onde o valor da variável é extraído."""
    EVENT_PAYLOAD = "event_payload"          # event["payload"]["score"]
    EVENT_AGGREGATE = "event_aggregate"      # event["aggregate_id"]
    DERIVED = "derived"                       # computado em runtime


@dataclass(frozen=True)
class VariableSpec:
    """Especificação imutável de uma variável clínica."""

    name: str                                 # "CARS2_total_score"
    source: VariableSource
    source_event_type: str                    # "ASSESSMENT_APPLIED"
    value_extractor: str                      # JSON path: "computed_scores.total"
    description: Optional[str] = None
    unit: Optional[str] = None                # "points", "hours", "mg"
    filter_clause: Dict[str, Any] = field(default_factory=dict)
    # ex: {"scale_code": "CARS2"} para restringir a uma escala específica

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")
        if not self.source_event_type:
            raise ValueError("source_event_type is required")
        if not self.value_extractor:
            raise ValueError("value_extractor is required")

    def matches(self, event: Dict[str, Any]) -> bool:
        """True se este evento satisfaz o filter_clause + source_event_type."""
        if event.get("event_type") != self.source_event_type:
            return False
        payload = event.get("payload") or {}
        for key, expected in self.filter_clause.items():
            actual = payload.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def extract_value(self, event: Dict[str, Any]) -> Optional[float]:
        """Extrai o valor numérico desta variável do evento."""
        if not self.matches(event):
            return None
        payload = event.get("payload") or {}
        # value_extractor é um path dotted (ex: "computed_scores.total")
        cur: Any = payload
        for part in self.value_extractor.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
            if cur is None:
                return None
        if isinstance(cur, (int, float)):
            return float(cur)
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source.value,
            "source_event_type": self.source_event_type,
            "value_extractor": self.value_extractor,
            "description": self.description,
            "unit": self.unit,
            "filter_clause": dict(self.filter_clause),
        }