"""
InMemoryKnowledgeRepository — Sprint 4.4 + Sprint 4.5 (G3).

Armazena em memória (dict):
    - genes_by_patient: dict[(tenant_id, patient_id), tuple[ClinicalGene, ...]]
    - genomes: dict[(tenant_id, genome_id), ClinicalGenome]
    - correlations: dict[(tenant_id, correlation_id), CorrelationResult]
    - hypotheses: dict[(tenant_id, hypothesis_id), ClinicalHypothesis]
    - cohorts: dict[(tenant_id, cohort_id), Cohort]
    - sessions: dict[(tenant_id, session_id), ResearchSession]
    - graphs: dict[(tenant_id, graph_id), KnowledgeGraph]

Thread-safety: RLock protege mutações.

Sprint 4.5: implementa KnowledgeRepository ABC tenant-bound.

PURE INFRASTRUCTURE: zero dependência externa.
"""

from __future__ import annotations

import threading
from typing import Iterable, Mapping

from ...genome.domain.aggregate import ClinicalGene
from ..domain.clinical_genome import ClinicalGenome
from ..domain.cohort import Cohort
from ..domain.correlation import CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis
from ..domain.knowledge_graph import KnowledgeGraph
from ..domain.research import ResearchSession
from .repository import KnowledgeRepository


class InMemoryKnowledgeRepository(KnowledgeRepository):
    """Repositório InMemory para o Clinical Knowledge Engine.

    Inherits KnowledgeRepository (Sprint 4.5 G3).

    Tenant é obrigatório. Default `tenant_id="tenant_test"` é apenas
    conveniência para testes Sprint 4.4/4.4.5 existentes — produção
    deve sempre passar tenant_id explícito.

    Note: não usa @dataclass porque tem __init__ customizado que
    passa tenant_id para ABC. Campos são inicializados diretamente.
    """

    def __init__(self, tenant_id: str = "tenant_test") -> None:
        super().__init__(tenant_id)
        self._lock: threading.RLock = threading.RLock()
        self.genes_by_patient: dict[tuple[str, str], tuple[ClinicalGene, ...]] = {}
        self.genomes: dict[tuple[str, str], ClinicalGenome] = {}
        self.correlations: dict[tuple[str, str], CorrelationResult] = {}
        self.hypotheses: dict[tuple[str, str], ClinicalHypothesis] = {}
        self.sessions: dict[tuple[str, str], ResearchSession] = {}
        self.cohorts: dict[tuple[str, str], Cohort] = {}
        self.graphs: dict[tuple[str, str], KnowledgeGraph] = {}

    # REDACTED
    # Genes
    # REDACTED

    def save_genes(
        self, patient_id: str, genes: Iterable[ClinicalGene]
    ) -> None:
        genes_tuple = tuple(genes)
        for gene in genes_tuple:
            self._assert_same_tenant(gene.tenant_id, "ClinicalGene")
            if gene.patient_id != patient_id:
                raise ValueError(
                    f"ClinicalGene.patient_id={gene.patient_id!r} "
                    f"diverge do save_genes(patient_id={patient_id!r})"
                )
        with self._lock:
            self.genes_by_patient[(self._tenant_id, patient_id)] = genes_tuple

    def load_genes(self, patient_id: str) -> tuple[ClinicalGene, ...]:
        with self._lock:
            return self.genes_by_patient.get(
                (self._tenant_id, patient_id), ()
            )

    def list_patient_ids(self) -> tuple[str, ...]:
        with self._lock:
            scoped = {
                pid
                for (tid, pid) in self.genes_by_patient.keys()
                if tid == self._tenant_id
            }
            return tuple(sorted(scoped))

    # REDACTED
    # Genomes
    # REDACTED

    def save_genome(self, genome: ClinicalGenome) -> None:
        self._assert_same_tenant(genome.tenant_id, "ClinicalGenome")
        with self._lock:
            self.genomes[(self._tenant_id, genome.genome_id)] = genome

    def load_genome(self, genome_id: str) -> ClinicalGenome | None:
        with self._lock:
            return self.genomes.get((self._tenant_id, genome_id))

    def list_genomes(self) -> tuple[ClinicalGenome, ...]:
        with self._lock:
            scoped = [
                g
                for (tid, gid), g in self.genomes.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda g: (
                        g.patient_id,
                        g.window.start,
                        g.window.end,
                        g.genome_id,
                    ),
                )
            )

    # REDACTED
    # Correlations
    # REDACTED

    def save_correlation(self, correlation: CorrelationResult) -> None:
        # CorrelationResult does NOT have tenant_id attribute; tenant
        # boundary is enforced at the ID level (correlation_id is
        # content-derived from tenant_id per Sprint 4.4.5 fix). Caller
        # MUST have constructed correlation via CorrelationEngine which
        # embeds the correct tenant in correlation_id.
        with self._lock:
            self.correlations[
                (self._tenant_id, correlation.correlation_id)
            ] = correlation

    def load_correlation(
        self, correlation_id: str
    ) -> CorrelationResult | None:
        with self._lock:
            return self.correlations.get(
                (self._tenant_id, correlation_id)
            )

    def list_correlations(self) -> tuple[CorrelationResult, ...]:
        with self._lock:
            scoped = [
                c
                for (tid, _), c in self.correlations.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda c: (
                        getattr(c, "patient_id", ""),
                        c.correlation_id,
                    ),
                )
            )

    # REDACTED
    # Hypotheses
    # REDACTED

    def save_hypothesis(self, hypothesis: ClinicalHypothesis) -> None:
        # ClinicalHypothesis does NOT have tenant_id attribute; tenant
        # boundary enforced at ID level (hypothesis_id is content-derived
        # from tenant_id via correlation_ids). Cross-tenant gap
        # registered for ADR (task #197 in Sprint 4.5).
        with self._lock:
            self.hypotheses[
                (self._tenant_id, hypothesis.hypothesis_id)
            ] = hypothesis

    def load_hypothesis(
        self, hypothesis_id: str
    ) -> ClinicalHypothesis | None:
        with self._lock:
            return self.hypotheses.get(
                (self._tenant_id, hypothesis_id)
            )

    def list_hypotheses(self) -> tuple[ClinicalHypothesis, ...]:
        with self._lock:
            scoped = [
                h
                for (tid, _), h in self.hypotheses.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda h: (
                        h.patient_id,
                        h.hypothesis_id,
                    ),
                )
            )

    # REDACTED
    # Sessions (Research)
    # REDACTED

    def save_session(self, session: ResearchSession) -> None:
        # ResearchSession não tem tenant_id explícito; tenant é implícito
        # via cohort_id. Como cohort_id é content-derived por tenant,
        # armazenamos pela chave de tenant + session_id.
        with self._lock:
            self.sessions[(self._tenant_id, session.session_id)] = session

    def load_session(self, session_id: str) -> ResearchSession | None:
        with self._lock:
            return self.sessions.get((self._tenant_id, session_id))

    def list_sessions(self) -> tuple[ResearchSession, ...]:
        with self._lock:
            scoped = [
                s
                for (tid, _), s in self.sessions.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda s: (s.started_at, s.session_id),
                    reverse=False,
                )
            )

    # REDACTED
    # Cohorts
    # REDACTED

    def save_cohort(self, cohort: Cohort) -> None:
        self._assert_same_tenant(cohort.tenant_id, "Cohort")
        with self._lock:
            self.cohorts[(self._tenant_id, cohort.cohort_id)] = cohort

    def load_cohort(self, cohort_id: str) -> Cohort | None:
        with self._lock:
            return self.cohorts.get((self._tenant_id, cohort_id))

    def list_cohorts(self) -> tuple[Cohort, ...]:
        with self._lock:
            scoped = [
                c
                for (tid, _), c in self.cohorts.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda c: (c.built_at, c.cohort_id),
                    reverse=False,
                )
            )

    # REDACTED
    # Graphs
    # REDACTED

    def save_graph(self, graph: KnowledgeGraph) -> None:
        self._assert_same_tenant(graph.tenant_id, "KnowledgeGraph")
        with self._lock:
            self.graphs[(self._tenant_id, graph.graph_id)] = graph

    def load_graph(self, graph_id: str) -> KnowledgeGraph | None:
        with self._lock:
            return self.graphs.get((self._tenant_id, graph_id))

    def list_graphs(self) -> tuple[KnowledgeGraph, ...]:
        with self._lock:
            scoped = [
                g
                for (tid, _), g in self.graphs.items()
                if tid == self._tenant_id
            ]
            return tuple(
                sorted(
                    scoped,
                    key=lambda g: (g.patient_id, g.graph_id),
                )
            )

    # REDACTED
    # Maintenance
    # REDACTED

    def clear(self) -> None:
        """Limpa todos os dados deste tenant. Útil para testes."""
        with self._lock:
            self.genes_by_patient = {
                k: v
                for k, v in self.genes_by_patient.items()
                if k[0] != self._tenant_id
            }
            self.genomes = {
                k: v for k, v in self.genomes.items() if k[0] != self._tenant_id
            }
            self.correlations = {
                k: v
                for k, v in self.correlations.items()
                if k[0] != self._tenant_id
            }
            self.hypotheses = {
                k: v
                for k, v in self.hypotheses.items()
                if k[0] != self._tenant_id
            }
            self.sessions = {
                k: v
                for k, v in self.sessions.items()
                if k[0] != self._tenant_id
            }
            self.cohorts = {
                k: v
                for k, v in self.cohorts.items()
                if k[0] != self._tenant_id
            }
            self.graphs = {
                k: v
                for k, v in self.graphs.items()
                if k[0] != self._tenant_id
            }

    def __len__(self) -> int:
        with self._lock:
            return (
                sum(
                    1
                    for k in self.genes_by_patient
                    if k[0] == self._tenant_id
                )
                + sum(1 for k in self.genomes if k[0] == self._tenant_id)
                + sum(
                    1
                    for k in self.correlations
                    if k[0] == self._tenant_id
                )
                + sum(
                    1
                    for k in self.hypotheses
                    if k[0] == self._tenant_id
                )
                + sum(1 for k in self.sessions if k[0] == self._tenant_id)
                + sum(1 for k in self.cohorts if k[0] == self._tenant_id)
                + sum(1 for k in self.graphs if k[0] == self._tenant_id)
            )

    # REDACTED
    # Classmethod convenience
    # REDACTED

    @classmethod
    def for_testing(cls, tenant_id: str = "tenant_test") -> "InMemoryKnowledgeRepository":
        """Factory explícita para uso em testes."""
        return cls(tenant_id=tenant_id)
