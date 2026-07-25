"""
Cohort Builder — Sprint 4.4 Clinical Knowledge Engine v1.0.

PRINCÍPIOS:
    - Cohort é uma seleção ESTRUTURADA de pacientes via critérios.
    - Critérios são OPERATORS canônicos (EQ, NE, GT, LT, IN, NOT_IN, EXISTS).
    - Campos suportados:
        * patient.age, patient.sex (placeholder — Sprint 4.5 wire com registry)
        * diagnosis.code (placeholder — Sprint 4.5 wire com registry)
        * gene.id, gene.confidence, gene.state
        * expression.observed_value.data, expression.trend, expression.volatility
        * expression.valid_time (window)
        * context.context_type ("medication", "school", etc.)

Invariantes:
    - CohortBuilder é pure function.
    - state_hash SHA-256 (replay determinístico).
    - Match em N pacientes retorna Cohort com matched_patient_ids.

PURE DOMAIN: zero dependências externas.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...timeline.domain.window import TimeWindow
from .clinical_genome import ClinicalGenome


class CriterionOperator(str, Enum):
    """Operadores canônicos para critérios de Cohort."""

    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _content_cohort_id(tenant_id: str, name: str, criteria_signature: str) -> str:
    """ID determinístico: mesmo tenant+name+criteria = mesmo cohort_id."""
    raw = f"{tenant_id}|{name}|{criteria_signature}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"cohort_{digest}"


def _criteria_signature(criteria: Sequence[Criterion]) -> str:
    parts: list[str] = []
    for c in sorted(criteria, key=lambda x: x.field):
        parts.append(f"{c.field}|{c.operator.value}|{c.value!r}")
    return "|".join(parts)


@dataclass(frozen=True)
class Criterion:
    """Critério de seleção para Cohort."""

    field: str                                # dotted path (ex: "gene.id")
    operator: CriterionOperator
    value: Any = None                         # valor a comparar (para EXISTS é ignorado)
    window: TimeWindow | None = None           # restrição temporal opcional

    def __post_init__(self) -> None:
        if not self.field:
            raise ValueError("Criterion.field obrigatório")


@dataclass(frozen=True)
class Cohort:
    """Coorte de pacientes selecionados por critérios.

    Determinístico: mesmos critérios + mesmos pacientes → mesmo state_hash.
    """

    cohort_id: str
    tenant_id: str
    name: str
    criteria: tuple[Criterion, ...]
    matched_patient_ids: tuple[str, ...]
    built_at: datetime
    state_hash: str = ""

    def __post_init__(self) -> None:
        if not self.cohort_id:
            raise ValueError("Cohort.cohort_id obrigatório")
        if not self.name:
            raise ValueError("Cohort.name obrigatório")

    @property
    def count(self) -> int:
        return len(self.matched_patient_ids)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Canonical dict determinístico (exclui built_at — replay invariant)."""
        return {
            "type": "Cohort",
            "tenant_id": self.tenant_id,
            "name": self.name,
            "criteria": [
                {
                    "field": c.field,
                    "operator": c.operator.value,
                    "value": c.value,
                }
                for c in sorted(self.criteria, key=lambda x: x.field)
            ],
            "matched_patient_ids": sorted(self.matched_patient_ids),
            "count": self.count,
        }

    def compute_state_hash(self) -> str:
        canonical = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate_state_hash(self) -> None:
        """Sprint 4.4.5 — Hardening: state_hash MUST ser SHA-256 preenchido."""
        if not self.state_hash:
            raise ValueError(
                "Cohort.state_hash MUST ser preenchido após construção "
                "— use CohortBuilder.evaluate"
            )
        if len(self.state_hash) != 64:
            raise ValueError(
                f"Cohort.state_hash deve ser SHA-256 hex (64 chars), "
                f"recebido {len(self.state_hash)}"
            )


# ============================================================================
# PatientData — input shape para CohortBuilder
# ============================================================================


@dataclass(frozen=True)
class PatientData:
    """Dados disponíveis por paciente para avaliação de critérios.

    Por enquanto, os campos patient.* / diagnosis.* são placeholders
    (Sprint 4.5 wire com ClinicalIdentity registry).
    """

    patient_id: str
    tenant_id: str
    age: int | None = None
    sex: str | None = None
    diagnosis_codes: tuple[str, ...] = ()
    genomes: tuple[ClinicalGenome, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


# ============================================================================
# CohortBuilder — pure function, deterministic
# ============================================================================


class CohortBuilder:
    """Construtor de Cohort a partir de critérios + PatientData.

    Uso:
        builder = CohortBuilder()
        cohort = builder.evaluate(
            patients=[...],
            tenant_id="tenant_1",
            name="TEA + sono ruim",
            criteria=[...],
        )

    Regras:
        - AND lógico entre critérios (todos devem ser satisfeitos).
        - Operador EXISTS: campo deve estar presente e não-nulo.
        - Operador IN/NOT_IN: value deve ser iterável.
    """

    def evaluate(
        self,
        *,
        patients: Sequence[PatientData],
        tenant_id: str,
        name: str,
        criteria: Sequence[Criterion],
        built_at: datetime | None = None,
    ) -> Cohort:
        """Avalia critérios contra lista de pacientes e retorna Cohort."""
        matched: list[str] = []
        for patient in patients:
            if patient.tenant_id != tenant_id:
                continue  # tenant isolation
            if all(
                self._matches(criterion, patient)
                for criterion in criteria
            ):
                matched.append(patient.patient_id)
        cohort = Cohort(
            cohort_id=_content_cohort_id(
                tenant_id, name, _criteria_signature(criteria),
            ),
            tenant_id=tenant_id,
            name=name,
            criteria=tuple(criteria),
            matched_patient_ids=tuple(sorted(matched)),
            built_at=built_at or _utcnow(),
        )
        return _with_state_hash(cohort, cohort.compute_state_hash())

    # REDACTED
    # Avaliação por campo
    # REDACTED

    def _matches(self, criterion: Criterion, patient: PatientData) -> bool:
        field_value = self._resolve_field(criterion.field, patient)
        op = criterion.operator

        if op == CriterionOperator.EXISTS:
            return field_value is not None

        if op == CriterionOperator.EQ:
            return field_value == criterion.value

        if op == CriterionOperator.NE:
            return field_value != criterion.value

        if op == CriterionOperator.GT:
            if field_value is None:
                return False
            return field_value > criterion.value

        if op == CriterionOperator.LT:
            if field_value is None:
                return False
            return field_value < criterion.value

        if op == CriterionOperator.IN:
            if field_value is None or not isinstance(criterion.value, (list, tuple, set)):
                return False
            return field_value in criterion.value

        if op == CriterionOperator.NOT_IN:
            if field_value is None or not isinstance(criterion.value, (list, tuple, set)):
                return True
            return field_value not in criterion.value

        return False

    def _resolve_field(self, field_path: str, patient: PatientData) -> Any:
        """Resolve dotted path contra PatientData.

        Suporta:
            - patient.age, patient.sex
            - diagnosis.code (retorna lista de codes)
            - gene.id (procura Gene cujo id == value)
            - gene.confidence (Expression.confidence do último current_expression)
            - gene.state (Expression.state)
            - expression.trend, expression.volatility
            - expression.observed_value.data
            - context.context_type (lista de tipos)
        """
        if field_path == "patient.age":
            return patient.age
        if field_path == "patient.sex":
            return patient.sex
        if field_path == "diagnosis.code":
            return list(patient.diagnosis_codes) if patient.diagnosis_codes else None
        # Campos derivados dos Genomes do paciente.
        if field_path.startswith("gene.") or field_path.startswith("expression.") or field_path.startswith("context."):
            return self._resolve_genome_field(field_path, patient)
        # Field genérico em metadata.
        return patient.metadata.get(field_path)

    def _resolve_genome_field(
        self, field_path: str, patient: PatientData
    ) -> Any:
        """Resolve field_path contra Genomes do paciente."""
        # Se é um critério de gene.id, retorna True/False por presença.
        if field_path == "gene.id":
            # Retorna list de gene_ids disponíveis (operador EXISTS/IN).
            ids = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    ids.append(gene.gene_id)
            return ids or None
        if field_path == "gene.confidence":
            # Lista de confidences dos Genes com Expression.
            confs = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    if gene.current_expression:
                        confs.append(gene.current_expression.confidence.value)
            return confs or None
        if field_path == "gene.state":
            states = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    if gene.current_expression:
                        states.append(gene.current_expression.state.value)
            return states or None
        if field_path == "expression.trend":
            trends = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    if gene.current_expression:
                        trends.append(gene.current_expression.trend.value)
            return trends or None
        if field_path == "expression.volatility":
            vols = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    if gene.current_expression:
                        vols.append(gene.current_expression.volatility.value)
            return vols or None
        if field_path == "expression.observed_value.data":
            values = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    if gene.current_expression:
                        values.append(gene.current_expression.observed_value.data)
            return values or None
        if field_path == "context.context_type":
            types = []
            for genome in patient.genomes:
                for gene in genome.genes:
                    for ctx in gene.context:
                        types.append(ctx.context_type)
            return list(set(types)) or None
        return None


def _with_state_hash(cohort: Cohort, state_hash: str) -> Cohort:
    """Reconstroi Cohort com state_hash."""
    import dataclasses

    return dataclasses.replace(cohort, state_hash=state_hash)


# implements:
#   AS-001 §7 — Replay bit-identical
#   ADR-0006 §3 — Pure Domain