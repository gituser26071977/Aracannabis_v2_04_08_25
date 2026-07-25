"""
ClinicalGenome — Projection (read-model, derivado).

Sprint 4.4 — Clinical Knowledge Engine v1.0.

NATUREZA:
    ClinicalGenome NÃO é Aggregate Root.
    ClinicalGenome NÃO possui estado próprio persistente.
    ClinicalGenome é exclusivamente:
        - Projection
        - Read Model
        - derivado do histórico de ClinicalGene Events

INVARIANTES:
    - Toda reconstrução ocorre via replay de eventos.
    - Replay bit-identical: mesmos eventos → mesmo state_hash (SHA-256).
    - ClinicalGenome contém apenas referências e resultados derivados —
      nunca persiste estado próprio.

Composição:
    - 1+ ClinicalGenes (reconstruídos por ReplayEngine)
    - tuple[CorrelationResult] (gerados por CorrelationEngine)
    - tuple[ClinicalHypothesis] (gerados por HypothesisEngine)
    - KnowledgeGraph | None (gerado por KnowledgeGraphBuilder)
    - InferenceExplanation que documenta a proveniência do genome

Padrão: AS-001 §6 (ClinicalGene) + AS-002 (ClinicalExpression).
        Domain puro: zero SQL/HTTP/ORM.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...genome.domain.events import DomainEvent
from ...genome.application import ReplayEngine
from ...timeline.domain.window import TimeWindow


# ============================================================================
# GenomeState — enum de estado agregado
# ============================================================================


class GenomeState(str, Enum):
    """Estado agregado do ClinicalGenome — derivado dos Genes constituintes."""

    UNKNOWN = "unknown"               # nenhum Gene com Expression
    PARTIAL = "partial"               # ≥1 Gene com Expression mas < total
    COMPLETE = "complete"             # todos os Genes com Expression CANONICAL
    DIVERGENT = "divergent"           # Genes em estados contraditórios
    HISTORICAL = "historical"         # apenas Expressions HISTORICAL (não ativas)


# ============================================================================
# ClinicalGenome — frozen dataclass
# ============================================================================


@dataclass(frozen=True)
class ClinicalGenome:
    """Projeção read-model integrada de um paciente em determinado instante.

    ClinicalGenome é SEMPRE derivado. Não é fonte de verdade.
    Para reconstruir, use ``ClinicalGenomeBuilder.build_from_events``.
    """

    genome_id: str
    tenant_id: str
    patient_id: str
    window: TimeWindow
    genes: tuple[ClinicalGene, ...]
    correlation_results: tuple[Any, ...] = ()   # tuple[CorrelationResult] — late import
    hypotheses: tuple[Any, ...] = ()            # tuple[ClinicalHypothesis] — late import
    graph_snapshot_id: str | None = None
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state_hash: str = ""

    def __post_init__(self) -> None:
        if not self.genome_id:
            raise ValueError("ClinicalGenome.genome_id obrigatório")
        if not self.tenant_id:
            raise ValueError("ClinicalGenome.tenant_id obrigatório")
        if not self.patient_id:
            raise ValueError("ClinicalGenome.patient_id obrigatório")
        if not self.genes:
            raise ValueError(
                "ClinicalGenome deve conter ao menos 1 ClinicalGene (projeção vazia não é válida)"
            )
        # Verificação de tenant consistency.
        tenant_ids = {g.tenant_id for g in self.genes}
        if len(tenant_ids) > 1:
            raise ValueError(
                f"ClinicalGenome mistura tenants: {tenant_ids} — multi-tenancy violation"
            )
        patient_ids = {g.patient_id for g in self.genes}
        if len(patient_ids) > 1:
            raise ValueError(
                f"ClinicalGenome mistura pacientes: {patient_ids} — deve ser 1 paciente"
            )

    def validate_state_hash(self) -> None:
        """Sprint 4.4.5 — Hardening: state_hash MUST ser SHA-256 preenchido.

        Validado apenas em pontos de produção (build_*) — permite
        construção transitória interna (research.py) sem quebrar.
        """
        if not self.state_hash:
            raise ValueError(
                "ClinicalGenome.state_hash MUST ser preenchido após construção "
                "— use build_from_genes / build_from_events"
            )
        if len(self.state_hash) != 64:
            raise ValueError(
                f"ClinicalGenome.state_hash deve ser SHA-256 hex (64 chars), "
                f"recebido {len(self.state_hash)}"
            )

    # REDACTED
    # Identidade canônica
    # REDACTED

    @property
    def urn(self) -> str:
        return (
            f"urn:araos:genome:{self.tenant_id}:{self.patient_id}:"
            f"{self.window.start.isoformat()}:{self.window.end.isoformat()}"
        )

    # REDACTED
    # Estado agregado
    # REDACTED

    def current_state(self) -> GenomeState:
        """Estado agregado derivado dos ExpressionStates dos Genes."""
        states: list[str] = []
        for gene in self.genes:
            current = gene.current_expression
            if current is None:
                states.append("unknown")
            else:
                states.append(current.state.value)
        counts = Counter(states)
        if not counts:
            return GenomeState.UNKNOWN
        # Divergent: Genes em estados contraditórios (UNKNOWN + CANONICAL).
        if "canonical" in counts and "unavailable" in counts:
            return GenomeState.DIVERGENT
        if "canonical" in counts and "unknown" in counts:
            return GenomeState.DIVERGENT
        if counts.get("canonical", 0) == len(self.genes):
            return GenomeState.COMPLETE
        if "canonical" not in counts and "historical" in counts:
            return GenomeState.HISTORICAL
        if "unknown" in counts and len(counts) == 1:
            return GenomeState.UNKNOWN
        return GenomeState.PARTIAL

    def has_correlations(self) -> bool:
        return len(self.correlation_results) > 0

    def has_hypotheses(self) -> bool:
        return len(self.hypotheses) > 0

    def has_graph(self) -> bool:
        return self.graph_snapshot_id is not None

    # REDACTED
    # Convenience accessors
    # REDACTED

    def gene_ids(self) -> tuple[str, ...]:
        return tuple(g.gene_id for g in self.genes)

    def gene(self, gene_id: str) -> ClinicalGene | None:
        for g in self.genes:
            if g.gene_id == gene_id:
                return g
        return None

    def all_event_ids(self) -> tuple[str, ...]:
        """Coleta todos os event_ids conhecidos do genome (audit chain)."""
        events: set[str] = set()
        for gene in self.genes:
            for entry in gene.history:
                events.add(entry.event_id)
        return tuple(sorted(events))

    # REDACTED
    # Canonical JSON (para state_hash + replay determinístico)
    # REDACTED

    def to_canonical_dict(self) -> dict[str, Any]:
        """Serializa o genome para dict canônico (ordem determinística).

        Invariante de replay: o canonical dict inclui apenas o estado
        clínico (Genes + window + derivações), NÃO o timestamp de
        construção, nem genome_id auto-gerado — isso garante que
        duas reconstruções a partir dos mesmos eventos produzem
        o mesmo state_hash (SHA-256 byte-idêntico).
        """
        return {
            "type": "ClinicalGenome",
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "window": {
                "start": self.window.start.isoformat(),
                "end": self.window.end.isoformat(),
                "label": self.window.label,
            },
            "genes": [
                {
                    "gene_id": g.gene_id,
                    "version": g.version,
                    "status": g.status,
                    "current_state": g.current_state().value if g.current_state() else None,
                    "confidence": (
                        g.current_expression.confidence.value
                        if g.current_expression
                        else 0.0
                    ),
                }
                for g in sorted(self.genes, key=lambda x: x.gene_id)
            ],
            "correlation_count": len(self.correlation_results),
            "hypothesis_count": len(self.hypotheses),
            "graph_snapshot_id": self.graph_snapshot_id,
        }

    def compute_state_hash(self) -> str:
        """SHA-256 do estado serializado canonicamente.

        Bit-equivalente para o mesmo estado — replay determinístico.
        """
        canonical = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ============================================================================
# ClinicalGenomeBuilder — função pura de construção
# ============================================================================


class ClinicalGenomeBuilder:
    """Construtor puro de ClinicalGenome.

    Não persiste estado. Cada chamada ``build_*`` produz um novo genome
    derivado. Para reprodutibilidade, use sempre ``build_from_events``
    (passa pelo ReplayEngine) e forneça timestamps fixos.
    """

    def __init__(
        self,
        *,
        replay_engine: ReplayEngine | None = None,
    ) -> None:
        self._replay_engine = replay_engine or ReplayEngine()

    def build_from_genes(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        window: TimeWindow,
        genes: Sequence[ClinicalGene],
        correlation_results: Sequence[Any] = (),
        hypotheses: Sequence[Any] = (),
        graph_snapshot_id: str | None = None,
        built_at: datetime | None = None,
    ) -> ClinicalGenome:
        """Constrói genome a partir de Genes já reconstruídos.

        Para replay determinístico, prefira ``build_from_events``.
        """
        genome = ClinicalGenome(
            genome_id=_new_genome_id(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            window=window,
            genes=tuple(genes),
            correlation_results=tuple(correlation_results),
            hypotheses=tuple(hypotheses),
            graph_snapshot_id=graph_snapshot_id,
            built_at=built_at or datetime.now(timezone.utc),
        )
        # Preenche state_hash pós-construção (frozen dataclass).
        return _with_state_hash(genome, genome.compute_state_hash())

    def build_from_events(
        self,
        *,
        tenant_id: str,
        patient_id: str,
        window: TimeWindow,
        events_by_gene: Mapping[str, Sequence[DomainEvent]],
        correlation_results: Sequence[Any] = (),
        hypotheses: Sequence[Any] = (),
        graph_snapshot_id: str | None = None,
        built_at: datetime | None = None,
    ) -> ClinicalGenome:
        """Constrói genome REPLAYANDO eventos de cada Gene.

        Esta é a porta de entrada canônica para garantir
        reprodutibilidade bit-identical.
        """
        genes: list[ClinicalGene] = []
        for gene_id, events in events_by_gene.items():
            if not events:
                raise ValueError(
                    f"events_by_gene['{gene_id}'] está vazio — Gene sem eventos"
                )
            # ReplayEngine.replay é determinístico por sequence ASC.
            gene = self._replay_engine.replay(events)
            genes.append(gene)
        return self.build_from_genes(
            tenant_id=tenant_id,
            patient_id=patient_id,
            window=window,
            genes=genes,
            correlation_results=correlation_results,
            hypotheses=hypotheses,
            graph_snapshot_id=graph_snapshot_id,
            built_at=built_at,
        )


# ============================================================================
# Helper
# ============================================================================


def _new_genome_id() -> str:
    return f"genome_{uuid.uuid4().hex[:12]}"


def _with_state_hash(
    genome: ClinicalGenome, state_hash: str
) -> ClinicalGenome:
    """Reconstroi ClinicalGenome com state_hash calculado (frozen dataclass)."""
    import dataclasses

    return dataclasses.replace(genome, state_hash=state_hash)


# ============================================================================
# Convenience function
# ============================================================================


def build_clinical_genome(
    *,
    tenant_id: str,
    patient_id: str,
    window: TimeWindow,
    genes: Sequence[ClinicalGene],
    correlation_results: Sequence[Any] = (),
    hypotheses: Sequence[Any] = (),
    graph_snapshot_id: str | None = None,
) -> ClinicalGenome:
    """Atalho para construir ClinicalGenome a partir de Genes."""
    return ClinicalGenomeBuilder().build_from_genes(
        tenant_id=tenant_id,
        patient_id=patient_id,
        window=window,
        genes=genes,
        correlation_results=correlation_results,
        hypotheses=hypotheses,
        graph_snapshot_id=graph_snapshot_id,
    )


# implements:
#   AS-001-REQ-0009 — Replay bit-identical
#   AS-001-REQ-0016 — Bitemporalidade (window obrigatória)
#   AS-001-REQ-0017 — Multi-tenancy estrito (tenant_id enforced)
#   ADR-0006 §3 — Pure Domain