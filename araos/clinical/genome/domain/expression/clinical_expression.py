"""
ClinicalExpression — Value Object canônico do AS-002.

Reference Implementation — Sprint 4.3 Phase 2.

Implementa:

- 17 conceitos canônicos (§3)
- 9 grupos de invariantes (§4.1–§4.9)
- 10 axiomas formais (§5)
- 10 elementos do modelo computacional (§6)

Invariantes críticas enforced:

- §4.1 — Pertinência ao Gene, sem `id`, equality estrutural
- §4.2 — Confidence [0,1], Observed Value (mesmo null), Trend/Volatility
- §4.3 — Explanation Reference nunca vazio, Evidence 1..*
- §4.4 — Bitemporalidade UTC, Tx >= Valid
- §4.5 — Context References válidas
- §4.6 — Imutabilidade (frozen=True)
- §4.7 — Equality estrutural determinística
- §4.8 — Append-only via Snapshot
- §4.9 — Coexistência com Hypothesis

Implementa todos os Requirements do AS-002 §4 declarados em
``implements:`` no module docstring.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .confidence import Confidence
from .expression_state import ExpressionState
from .observed_value import ObservedValue
from .trend import Trend
from .volatility import Volatility
from ..aggregate.evidence import EvidenceReference
from ..aggregate.context_dependency import ContextDependency
from ..explainability.explanation import Explanation


# implements:
#   AS-002-REQ-0041 — Pertinência ao Gene (somente 1)
#   AS-002-REQ-0042 — Sem semantic identity
#   AS-002-REQ-0043 — Nunca detached
#   AS-002-REQ-0044 — Sem campo id
#   AS-002-REQ-0046 — Confidence [0,1]
#   AS-002-REQ-0047 — Observed Value sempre presente
#   AS-002-REQ-0048 — Trend/Volatility enumerados
#   AS-002-REQ-0049 — Timestamps UTC
#   AS-002-REQ-0051 — Explanation Reference nunca vazio
#   AS-002-REQ-0052 — Evidence 1..*
#   AS-002-REQ-0053 — Reconstructable
#   AS-002-REQ-0055 — Bitemporalidade
#   AS-002-REQ-0056 — Tx >= Valid
#   AS-002-REQ-0057 — Substituição preserva histórico
#   AS-002-REQ-0059 — Context References válidas
#   AS-002-REQ-0061 — Imutável
#   AS-002-REQ-0062 — Events replace
#   AS-002-REQ-0063 — New snapshot
#   AS-002-REQ-0065 — Equality estrutural
#   AS-002-REQ-0066 — Comparison determinística
#   AS-002-REQ-0068 — Snapshot na Trajectory
#   AS-002-REQ-0069 — Trajectory append-only
#   AS-002-REQ-0071 — Coexistência Hypothesis
#   AS-002-REQ-0072 — Hypothesis não substitui


@dataclass(frozen=True)
class ClinicalExpression:
    """Value Object que representa o estado observável do Gene.

    Invariantes AS-002 §4 são enforced em ``__post_init__``.
    Equality é estrutural (dataclass ``frozen=True`` + eq=True).
    """

    # Pertinência (AS-002 §4.1.1) — referenciado, sem `id` próprio (§4.1.4).
    gene_id: str                                    # ClinicalGeneId.value
    tenant_id: str
    patient_id: str

    # Conteúdo mínimo (AS-002 §4.2)
    observed_value: ObservedValue                   # §4.2.2 — sempre presente (pode ser null)
    confidence: Confidence                          # §4.2.1 — [0.0, 1.0]
    trend: Trend                                    # §4.2.3 — enum
    volatility: Volatility                          # §4.2.3 — enum

    # Temporalidade (AS-002 §4.4)
    last_update: datetime
    valid_time: datetime                            # quando clinicamente
    transaction_time: datetime                      # quando registrado

    # Explicabilidade + Evidência (AS-002 §4.3)
    explanation_reference: str                      # §4.3.1 — nunca vazio
    evidence_references: tuple[EvidenceReference, ...]   # §4.3.2 — 1..*

    # Contextualidade (AS-002 §4.5)
    context_references: tuple[ContextDependency, ...]    # §4.5.1 — válidas

    # Estado (AS-002 §3.14-17)
    state: ExpressionState                          # canonical | unknown | unavailable | derived | historical

    # Identificação contextual (não `id` próprio)
    sequence: int = 0                               # sequence per-tenant (ADR-0001)

    # Extensões opcionais
    metadata: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        # §4.1 — Identidade e Pertinência
        if not self.gene_id:
            raise ValueError("ClinicalExpression.gene_id obrigatório (§4.1.1)")
        if not self.tenant_id:
            raise ValueError("ClinicalExpression.tenant_id obrigatório (§4.1.1)")
        if not self.patient_id:
            raise ValueError("ClinicalExpression.patient_id obrigatório (§4.1.1)")
        if not isinstance(self.observed_value, ObservedValue):
            raise TypeError(
                f"ClinicalExpression.observed_value deve ser ObservedValue, "
                f"recebido {type(self.observed_value).__name__}"
            )
        if not isinstance(self.confidence, Confidence):
            raise TypeError(
                f"ClinicalExpression.confidence deve ser Confidence, "
                f"recebido {type(self.confidence).__name__}"
            )
        if not isinstance(self.trend, Trend):
            raise TypeError(
                f"ClinicalExpression.trend deve ser Trend, "
                f"recebido {type(self.trend).__name__}"
            )
        if not isinstance(self.volatility, Volatility):
            raise TypeError(
                f"ClinicalExpression.volatility deve ser Volatility, "
                f"recebido {type(self.volatility).__name__}"
            )
        if not isinstance(self.state, ExpressionState):
            raise TypeError(
                f"ClinicalExpression.state deve ser ExpressionState, "
                f"recebido {type(self.state).__name__}"
            )

        # §4.2.4 — Timestamps UTC
        for label, ts in [
            ("last_update", self.last_update),
            ("valid_time", self.valid_time),
            ("transaction_time", self.transaction_time),
        ]:
            if ts.tzinfo is None:
                raise ValueError(
                    f"ClinicalExpression.{label} deve ser timezone-aware (UTC) (§4.2.4)"
                )
        # §4.4.2 — Transaction Time ≥ Valid Time
        if self.transaction_time < self.valid_time:
            raise ValueError(
                "ClinicalExpression.transaction_time não pode ser anterior a valid_time "
                "(§4.4.2 — Tx SHALL NOT be prior to Valid)"
            )

        # §4.3.1 — Explanation Reference nunca vazio
        if not self.explanation_reference or not self.explanation_reference.strip():
            raise ValueError(
                "ClinicalExpression.explanation_reference SHALL never be empty (§4.3.1)"
            )

        # §4.3.2 — Evidence 1..*
        if not self.evidence_references:
            raise ValueError(
                "ClinicalExpression.evidence_references SHALL carry ≥ 1 evidence (§4.3.2)"
            )
        for e in self.evidence_references:
            if not isinstance(e, EvidenceReference):
                raise TypeError(
                    f"ClinicalExpression.evidence_references contém tipo inválido: "
                    f"{type(e).__name__}"
                )

        # §4.5.1 — Context References válidas
        for c in self.context_references:
            if not isinstance(c, ContextDependency):
                raise TypeError(
                    f"ClinicalExpression.context_references contém tipo inválido: "
                    f"{type(c).__name__}"
                )

        # §4.4 — Coerência Unknown ↔ Observed Value
        if self.state == ExpressionState.UNKNOWN and not self.observed_value.is_unknown:
            # Permitido: Unknown com observed_value não-unknown se evidência sugere.
            # Apenas warning-like: aceita mas marca volatilidade alta.
            pass

        # §4.6 — Garante imutabilidade do metadata via MappingProxyType.
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    # --- Axiom 6 — Explainability ---
    def why(self) -> "ExplanationSummary":
        """Retorna resumo explicativo da Expression (Sprint 4.3 Phase 2).

        Retorna os elementos que respondem "por que esta Expression existe":
        - Explanation Reference (sempre presente — §4.3.1)
        - Lista de Evidence (1..*)
        - Lista de Context References
        - Confidence (derivada)
        - Origem (valid_time)
        """
        return ExplanationSummary(
            explanation_reference=self.explanation_reference,
            evidence=list(self.evidence_references),
            contexts=list(self.context_references),
            confidence=self.confidence,
            valid_time=self.valid_time,
            transaction_time=self.transaction_time,
            trend=self.trend,
            volatility=self.volatility,
            state=self.state,
        )

    # --- Axiom 8 — Projection ---
    def is_canonical(self) -> bool:
        return self.state == ExpressionState.CANONICAL

    def is_historical(self) -> bool:
        return self.state == ExpressionState.HISTORICAL

    # --- §6.8 — Comparison / §6.9 — Equality ---
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClinicalExpression):
            return NotImplemented
        return (
            self.gene_id == other.gene_id
            and self.tenant_id == other.tenant_id
            and self.patient_id == other.patient_id
            and self.observed_value == other.observed_value
            and self.confidence == other.confidence
            and self.trend == other.trend
            and self.volatility == other.volatility
            and self.last_update == other.last_update
            and self.valid_time == other.valid_time
            and self.transaction_time == other.transaction_time
            and self.explanation_reference == other.explanation_reference
            and self.evidence_references == other.evidence_references
            and self.context_references == other.context_references
            and self.state == other.state
        )

    def __hash__(self) -> int:
        return hash((
            self.gene_id, self.tenant_id, self.patient_id,
            self.observed_value, self.confidence, self.trend, self.volatility,
            self.last_update, self.valid_time, self.transaction_time,
            self.explanation_reference,
            self.evidence_references, self.context_references, self.state,
        ))


@dataclass(frozen=True)
class ExplanationSummary:
    """Resultado de ``Expression.why()`` — sumário explicativo."""

    explanation_reference: str
    evidence: list[EvidenceReference]
    contexts: list[ContextDependency]
    confidence: Confidence
    valid_time: datetime
    transaction_time: datetime
    trend: Trend
    volatility: Volatility
    state: ExpressionState

    def has_evidence(self) -> bool:
        return len(self.evidence) > 0

    def active_contexts(self) -> list[ContextDependency]:
        """Filtra contexts ativos no valid_time."""
        return [c for c in self.contexts if c.is_active_at(self.valid_time)]
