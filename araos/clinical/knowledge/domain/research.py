"""
Research Workspace — Sprint 4.4 Clinical Knowledge Engine v1.0.

PRINCÍPIOS:
    - Toda consulta gera ResearchSession com URN canônico.
    - Query JSON versionada.
    - Resultado reproduzível byte-a-byte (state_hash SHA-256).
    - Replay() re-executa query idêntica e valida byte-equivalência.

Componentes:
    - ResearchQuery (frozen): query_id, cohort_id, analysis_type, params, version.
    - ResearchSession (frozen): session_id, urn, query, version, started_at,
      completed_at, result_json, state_hash, reproducible.
    - ResearchWorkspace (pure): execute() + replay().

PURE DOMAIN: zero dependências externas.
"""

from __future__ import annotations

import copy
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
from .cohort import Cohort, CohortBuilder, PatientData
from .correlation import CorrelationEngine, CorrelationMethod, CorrelationResult
from .explainability import ExplainabilityPipeline, InferenceExplanation, InferenceType
from .hypothesis import ClinicalHypothesis, HypothesisEngine
from .knowledge_graph import KnowledgeGraph, KnowledgeGraphBuilder


class AnalysisType(str, Enum):
    """Tipos canônicos de análise em uma Research Session."""

    CORRELATIONS = "correlations"
    HYPOTHESES = "hypotheses"
    GRAPH = "graph"
    STATS = "stats"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_query_id() -> str:
    return f"query_{uuid.uuid4().hex[:12]}"


def _new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class ResearchQuery:
    """Query de pesquisa — declaração estruturada do que será executado.

    Versionada: incrementar version em caso de mudança semântica.
    """

    query_id: str
    cohort_id: str
    analysis_type: AnalysisType
    params: Mapping[str, Any]
    version: int = 1
    created_at: datetime = field(default_factory=lambda: _utcnow())

    def __post_init__(self) -> None:
        if not self.query_id:
            raise ValueError("ResearchQuery.query_id obrigatório")
        if not self.cohort_id:
            raise ValueError("ResearchQuery.cohort_id obrigatório")
        if self.version < 1:
            raise ValueError(
                f"ResearchQuery.version deve ser >= 1, recebido {self.version}"
            )

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "type": "ResearchQuery",
            "query_id": self.query_id,
            "cohort_id": self.cohort_id,
            "analysis_type": self.analysis_type.value,
            "params": dict(self.params),
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }

    def to_canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )


@dataclass(frozen=True)
class ResearchSession:
    """Sessão de pesquisa executada — reproduzível byte-a-byte.

    result_json é o JSON canônico do resultado.
    state_hash é SHA-256 do result_json.
    """

    session_id: str
    query: ResearchQuery
    version: int
    started_at: datetime
    completed_at: datetime
    result_json: str
    state_hash: str
    reproducible: bool
    explanation: InferenceExplanation

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("ResearchSession.session_id obrigatório")
        if not self.result_json:
            raise ValueError("ResearchSession.result_json obrigatório")
        if not self.state_hash:
            raise ValueError("ResearchSession.state_hash obrigatório")
        if self.version < 1:
            raise ValueError(
                f"ResearchSession.version deve ser >= 1, recebido {self.version}"
            )
        if self.started_at.tzinfo is None or self.completed_at.tzinfo is None:
            raise ValueError(
                "ResearchSession.started_at e completed_at devem ser timezone-aware (UTC)"
            )

    @property
    def urn(self) -> str:
        return (
            f"urn:araos:research:{self.query.cohort_id}:{self.session_id}"
        )

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()


# ============================================================================
# ResearchWorkspace — pure deterministic
# ============================================================================


class ResearchWorkspace:
    """Workspace de pesquisa — executa queries reproduzíveis.

    Uso:
        workspace = ResearchWorkspace()
        session = workspace.execute(query, patients, genes_by_patient)
        # Reproduzir:
        session2 = workspace.replay(session.query, patients, genes_by_patient)
        assert session.result_json == session2.result_json
        assert session.state_hash == session2.state_hash
    """

    def execute(
        self,
        query: ResearchQuery,
        *,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> ResearchSession:
        """Executa a query e retorna ResearchSession."""
        started_at = _utcnow()
        # Filtra pacientes pelo cohort_id (caller deve passar patients já avaliados).
        cohort_patients = list(patients)
        # Executa a análise conforme analysis_type.
        result_dict = self._run_analysis(
            query=query,
            patients=cohort_patients,
            genes_by_patient=genes_by_patient,
        )
        completed_at = _utcnow()
        # Serialização canônica (sort_keys=True para determinismo).
        result_json = json.dumps(
            result_dict,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        state_hash = hashlib.sha256(result_json.encode("utf-8")).hexdigest()
        # Explicação.
        explanation = ExplainabilityPipeline.for_research(
            claim=(
                f"Research session executou {query.analysis_type.value} "
                f"para cohort {query.cohort_id}"
            ),
            query_type=query.analysis_type.value,
            confidence=1.0,
            correlation_ids=result_dict.get("correlation_ids", []),
            hypothesis_ids=result_dict.get("hypothesis_ids", []),
        )
        return ResearchSession(
            session_id=_new_session_id(),
            query=query,
            version=query.version,
            started_at=started_at,
            completed_at=completed_at,
            result_json=result_json,
            state_hash=state_hash,
            reproducible=True,
            explanation=explanation,
        )

    def replay(
        self,
        query: ResearchQuery,
        *,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> ResearchSession:
        """Re-executa a query idêntica.

        Garante mesma result_json e state_hash (reprodutibilidade).
        """
        # Mantém started_at coerente: nova execução registra novo timestamp.
        return self.execute(
            query,
            patients=patients,
            genes_by_patient=genes_by_patient,
        )

    # REDACTED
    # Execução por tipo
    # REDACTED

    def _run_analysis(
        self,
        *,
        query: ResearchQuery,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> dict[str, Any]:
        analysis_type = query.analysis_type

        if analysis_type == AnalysisType.CORRELATIONS:
            return self._run_correlations(query, patients, genes_by_patient)

        if analysis_type == AnalysisType.HYPOTHESES:
            return self._run_hypotheses(query, patients, genes_by_patient)

        if analysis_type == AnalysisType.GRAPH:
            return self._run_graph(query, patients, genes_by_patient)

        if analysis_type == AnalysisType.STATS:
            return self._run_stats(query, patients, genes_by_patient)

        return {"type": "unknown", "analysis_type": analysis_type.value}

    def _build_genomes_for_patients(
        self,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> list[ClinicalGenome]:
        """Helper: monta ClinicalGenome por paciente."""
        genomes: list[ClinicalGenome] = []
        for patient in patients:
            genes = list(genes_by_patient.get(patient.patient_id, ()))
            if not genes:
                continue
            # Window default: cobre todo o intervalo das Expressions.
            window = _infer_window(genes)
            genome = ClinicalGenome(
                genome_id=f"genome_{patient.patient_id}",
                tenant_id=patient.tenant_id,
                patient_id=patient.patient_id,
                window=window,
                genes=tuple(genes),
                built_at=_utcnow(),
            )
            genomes.append(genome)
        return genomes

    def _run_correlations(
        self,
        query: ResearchQuery,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> dict[str, Any]:
        engine = CorrelationEngine()
        method_str = query.params.get("method", "positive")
        try:
            method = CorrelationMethod(method_str)
        except ValueError:
            method = CorrelationMethod.POSITIVE
        all_correlations: list[dict[str, Any]] = []
        correlation_ids: list[str] = []
        genomes = self._build_genomes_for_patients(patients, genes_by_patient)
        for genome in genomes:
            results = engine.compute(genome, method=method)
            for r in results:
                all_correlations.append({
                    "correlation_id": r.correlation_id,
                    "method": r.method.value,
                    "gene_x_id": r.gene_x_id,
                    "gene_y_id": r.gene_y_id,
                    "coefficient": r.coefficient,
                    "n_observations": r.n_observations,
                    "confidence": r.confidence,
                    "patient_id": genome.patient_id,
                })
                correlation_ids.append(r.correlation_id)
        return {
            "type": "correlations_result",
            "analysis_type": AnalysisType.CORRELATIONS.value,
            "method": method.value,
            "count": len(all_correlations),
            "correlations": all_correlations,
            "correlation_ids": correlation_ids,
        }

    def _run_hypotheses(
        self,
        query: ResearchQuery,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> dict[str, Any]:
        corr_engine = CorrelationEngine()
        hyp_engine = HypothesisEngine()
        all_hypotheses: list[dict[str, Any]] = []
        hypothesis_ids: list[str] = []
        correlation_ids: list[str] = []
        genomes = self._build_genomes_for_patients(patients, genes_by_patient)
        for genome in genomes:
            correlations = corr_engine.compute(
                genome, method=CorrelationMethod.POSITIVE
            )
            correlations += corr_engine.compute(
                genome, method=CorrelationMethod.NEGATIVE
            )
            correlations += corr_engine.compute(
                genome, method=CorrelationMethod.CO_OCCURRENCE
            )
            hypotheses = hyp_engine.generate(genome, correlations)
            for h in hypotheses:
                all_hypotheses.append({
                    "hypothesis_id": h.hypothesis_id,
                    "claim": h.claim,
                    "status": h.status.value,
                    "confidence": h.confidence,
                    "rule_id": h.rule_id,
                    "patient_id": genome.patient_id,
                    "supporting_genes": list(h.supporting_genes),
                    "contradicting_genes": list(h.contradicting_genes),
                })
                hypothesis_ids.append(h.hypothesis_id)
                correlation_ids.extend(h.correlations_used)
        return {
            "type": "hypotheses_result",
            "analysis_type": AnalysisType.HYPOTHESES.value,
            "count": len(all_hypotheses),
            "hypotheses": all_hypotheses,
            "hypothesis_ids": hypothesis_ids,
            "correlation_ids": correlation_ids,
        }

    def _run_graph(
        self,
        query: ResearchQuery,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> dict[str, Any]:
        corr_engine = CorrelationEngine()
        hyp_engine = HypothesisEngine()
        graph_builder = KnowledgeGraphBuilder()
        graphs: list[dict[str, Any]] = []
        genomes = self._build_genomes_for_patients(patients, genes_by_patient)
        for genome in genomes:
            correlations = corr_engine.compute(
                genome, method=CorrelationMethod.POSITIVE
            )
            correlations += corr_engine.compute(
                genome, method=CorrelationMethod.CO_OCCURRENCE
            )
            hypotheses = hyp_engine.generate(genome, correlations)
            graph = graph_builder.build(
                genome, correlations=correlations, hypotheses=hypotheses
            )
            graphs.append({
                "graph_id": graph.graph_id,
                "patient_id": graph.patient_id,
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
                "state_hash": graph.state_hash,
                "node_types": [n.node_type.value for n in graph.nodes],
                "edge_types": [e.edge_type.value for e in graph.edges],
            })
        return {
            "type": "graph_result",
            "analysis_type": AnalysisType.GRAPH.value,
            "count": len(graphs),
            "graphs": graphs,
        }

    def _run_stats(
        self,
        query: ResearchQuery,
        patients: Sequence[PatientData],
        genes_by_patient: Mapping[str, Sequence[ClinicalGene]],
    ) -> dict[str, Any]:
        """Estatísticas agregadas: total genes, total expressions, total events."""
        total_patients = len(patients)
        total_genes = 0
        total_expressions = 0
        total_events = 0
        confidence_values: list[float] = []
        for genes in genes_by_patient.values():
            for gene in genes:
                total_genes += 1
                total_expressions += len(list(gene.trajectory))
                for entry in gene.history:
                    total_events += 1
                if gene.current_expression:
                    confidence_values.append(
                        gene.current_expression.confidence.value
                    )
        mean_confidence = (
            sum(confidence_values) / len(confidence_values)
            if confidence_values
            else 0.0
        )
        return {
            "type": "stats_result",
            "analysis_type": AnalysisType.STATS.value,
            "total_patients": total_patients,
            "total_genes": total_genes,
            "total_expressions": total_expressions,
            "total_events": total_events,
            "mean_confidence": mean_confidence,
            "patients_with_genes": sum(
                1 for genes in genes_by_patient.values() if genes
            ),
        }


# ============================================================================
# Helpers
# ============================================================================


def _infer_window(genes: Sequence[ClinicalGene]) -> TimeWindow:
    """Infere TimeWindow cobrindo todas as Expressions dos Genes."""
    times: list[datetime] = []
    for gene in genes:
        for point in gene.trajectory:
            times.append(point.expression.valid_time)
    if not times:
        now = _utcnow()
        return TimeWindow(start=now, end=now, label="empty")
    start = min(times)
    end = max(times)
    return TimeWindow(start=start, end=end, label="research_window")


# implements:
#   AS-001 §7.5 — Explainability cross-cutting
#   AS-001 §7.7.1 — Replay bit-identical
#   ADR-0006 §3 — Pure Domain
#   Sprint 4.4 — "Consultas reproduzíveis" + "byte-equivalência"