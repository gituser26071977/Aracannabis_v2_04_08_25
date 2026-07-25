"""
KnowledgeRepository — Abstract Base Class.

Sprint 4.5 — Infrastructure Layer (G3 Pre-Wave Governance Gate).

Esta ABC é a **referência canônica** para persistência do Clinical
Knowledge Engine. Tanto InMemory quanto SQLAlchemy devem implementar
este contrato.

Princípios de design (estabilizados em Architecture Freeze v1.0):

    1. **Tenant-bound by construction.**
       `tenant_id` é obrigatório no __init__. Não há método sem escopo.
       Toda entidade recebida tem seu `tenant_id` validado contra o
       tenant do repository. Cross-tenant access levanta erro.

    2. **Composite keys onde aplicável.**
       Genes são keyed por `(tenant_id, patient_id)` (gene só faz
       sentido no contexto do paciente). Outras entidades usam
       `(tenant_id, <entity>_id)`.

    3. **Listagens determinísticas.**
       `list_*` ordena deterministicamente por campos canônicos.
       Nunca confiar em inserção order.

    4. **Load retorna None ou () quando não encontrado.**
       Não levanta KeyError. Não vaza existência (sem 404-distinguishable).

    5. **Sem commit() em repo.**
       Repositórios são session-bound. Apenas UnitOfWork pode comitar.
       SQL impl: nunca chama `session.commit()` nem `session.rollback()`.

    6. **Replay byte-identical preservado.**
       Round-trip entidade → row → entidade MUST produzir mesma
       `to_canonical_dict()` (state_hash idêntico).

Conformidade:

    - Architecture Freeze v1.0 §3 — Mudanças Proibidas: respeitada
      (apenas infra, não domain).
    - ADR-0008 — KnowledgeGraph persistence: respeitada (JSON blob).
    - Foundation Freeze — não modificado.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ...genome.domain.aggregate import ClinicalGene
from ..domain.clinical_genome import ClinicalGenome
from ..domain.cohort import Cohort
from ..domain.correlation import CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis
from ..domain.knowledge_graph import KnowledgeGraph
from ..domain.research import ResearchSession


class KnowledgeRepository(ABC):
    """ABC para persistência do Clinical Knowledge Engine.

    SEMPRE bound a um tenant. Não há construtor default.
    Toda query é tenant-scoped por construção.
    """

    # ==================================================================
    # Construction & tenant validation
    # ==================================================================

    def __init__(self, tenant_id: str) -> None:
        """Construtor ABC.

        Args:
            tenant_id: identificador do tenant (organização).

        Raises:
            ValueError: se tenant_id for None, vazio ou não-string.
        """
        if not isinstance(tenant_id, str):
            raise ValueError(
                f"KnowledgeRepository requer tenant_id str, "
                f"recebido {type(tenant_id).__name__}"
            )
        if not tenant_id:
            raise ValueError("KnowledgeRepository requer tenant_id não-vazio")
        self._tenant_id = tenant_id

    @property
    def tenant_id(self) -> str:
        """Tenant ao qual este repository está bound (imutável)."""
        return self._tenant_id

    def _assert_same_tenant(self, entity_tenant_id: str, entity_kind: str) -> None:
        """Levanta PermissionError se entity.tenant_id != self.tenant_id.

        Cross-tenant access é sempre rejeitado antes de qualquer I/O.
        Garante que bug no caller não resulte em vazamento de dados.
        """
        if entity_tenant_id != self._tenant_id:
            raise PermissionError(
                f"Cross-tenant access denied: "
                f"repo.tenant_id={self._tenant_id!r}, "
                f"entity={entity_kind}.tenant_id={entity_tenant_id!r}"
            )

    # ==================================================================
    # Genes — keyed by (tenant_id, patient_id)
    # ==================================================================

    @abstractmethod
    def save_genes(
        self, patient_id: str, genes: Iterable[ClinicalGene]
    ) -> None:
        """Persiste genes de um paciente.

        Args:
            patient_id: identificador do paciente.
            genes: iterável de ClinicalGene (todos do mesmo tenant/patient).

        Raises:
            PermissionError: se algum gene tiver tenant_id != self.tenant_id.
        """
        ...

    @abstractmethod
    def load_genes(self, patient_id: str) -> tuple[ClinicalGene, ...]:
        """Carrega genes de um paciente.

        Returns:
            Tupla vazia se paciente não existir (NÃO None, NÃO levanta).
        """
        ...

    @abstractmethod
    def list_patient_ids(self) -> tuple[str, ...]:
        """Lista IDs de pacientes com genes salvos.

        Returns:
            Tupla ordenada ASC por patient_id (deterministic).
        """
        ...

    # ==================================================================
    # Genomes — keyed by (tenant_id, genome_id)
    # ==================================================================

    @abstractmethod
    def save_genome(self, genome: ClinicalGenome) -> None:
        """Persiste um ClinicalGenome (projeção).

        Raises:
            PermissionError: se genome.tenant_id != self.tenant_id.
        """
        ...

    @abstractmethod
    def load_genome(self, genome_id: str) -> ClinicalGenome | None:
        """Carrega um ClinicalGenome por genome_id.

        Returns:
            None se não existir (não vaza existência).
        """
        ...

    @abstractmethod
    def list_genomes(self) -> tuple[ClinicalGenome, ...]:
        """Lista ClinicalGenomes do tenant.

        Returns:
            Ordenado por (patient_id ASC, window.start ASC,
            window.end ASC, genome_id ASC). Deterministic.
        """
        ...

    # ==================================================================
    # Correlations — keyed by (tenant_id, correlation_id)
    # ==================================================================

    @abstractmethod
    def save_correlation(self, correlation: CorrelationResult) -> None:
        """Persiste um CorrelationResult.

        Raises:
            PermissionError: se correlation.tenant_id != self.tenant_id.
        """
        ...

    @abstractmethod
    def load_correlation(
        self, correlation_id: str
    ) -> CorrelationResult | None:
        """Carrega CorrelationResult por correlation_id.

        Returns:
            None se não existir.
        """
        ...

    @abstractmethod
    def list_correlations(self) -> tuple[CorrelationResult, ...]:
        """Lista CorrelationResults do tenant.

        Returns:
            Ordenado por (patient_id ASC, correlation_id ASC).
        """
        ...

    # ==================================================================
    # Hypotheses — keyed by (tenant_id, hypothesis_id)
    # ==================================================================

    @abstractmethod
    def save_hypothesis(self, hypothesis: ClinicalHypothesis) -> None:
        """Persiste um ClinicalHypothesis.

        Raises:
            PermissionError: se hypothesis.tenant_id != self.tenant_id.
        """
        ...

    @abstractmethod
    def load_hypothesis(
        self, hypothesis_id: str
    ) -> ClinicalHypothesis | None:
        """Carrega ClinicalHypothesis por hypothesis_id.

        Returns:
            None se não existir.
        """
        ...

    @abstractmethod
    def list_hypotheses(self) -> tuple[ClinicalHypothesis, ...]:
        """Lista ClinicalHypotheses do tenant.

        Returns:
            Ordenado por (patient_id ASC, hypothesis_id ASC).
        """
        ...

    # ==================================================================
    # Cohorts — keyed by (tenant_id, cohort_id)
    # ==================================================================

    @abstractmethod
    def save_cohort(self, cohort: Cohort) -> None:
        """Persiste um Cohort.

        Raises:
            PermissionError: se cohort.tenant_id != self.tenant_id.
        """
        ...

    @abstractmethod
    def load_cohort(self, cohort_id: str) -> Cohort | None:
        """Carrega Cohort por cohort_id.

        Returns:
            None se não existir.
        """
        ...

    @abstractmethod
    def list_cohorts(self) -> tuple[Cohort, ...]:
        """Lista Cohorts do tenant.

        Returns:
            Ordenado por (built_at DESC, cohort_id ASC).
        """
        ...

    # ==================================================================
    # Research sessions — keyed by (tenant_id, session_id)
    # ==================================================================

    @abstractmethod
    def save_session(self, session: ResearchSession) -> None:
        """Persiste uma ResearchSession.

        Raises:
            PermissionError: se session.query.cohort_id (que tem tenant
                implícito) for de outro tenant. Como session não tem
                tenant_id explícito, validação é feita por cohort_id.
        """
        ...

    @abstractmethod
    def load_session(self, session_id: str) -> ResearchSession | None:
        """Carrega ResearchSession por session_id.

        Returns:
            None se não existir.
        """
        ...

    @abstractmethod
    def list_sessions(self) -> tuple[ResearchSession, ...]:
        """Lista ResearchSessions do tenant.

        Returns:
            Ordenado por (started_at DESC, session_id ASC).
        """
        ...

    # ==================================================================
    # Knowledge graphs — keyed by (tenant_id, graph_id)
    # ==================================================================

    @abstractmethod
    def save_graph(self, graph: KnowledgeGraph) -> None:
        """Persiste um KnowledgeGraph (projeção).

        Raises:
            PermissionError: se graph.tenant_id != self.tenant_id.

        Note:
            Conforme ADR-0008 — Opção A (JSON blob). graph_json
            MUST ser o output de to_canonical_dict() com
            sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), default=str.
        """
        ...

    @abstractmethod
    def load_graph(self, graph_id: str) -> KnowledgeGraph | None:
        """Carrega KnowledgeGraph por graph_id.

        Returns:
            None se não existir.
        """
        ...

    @abstractmethod
    def list_graphs(self) -> tuple[KnowledgeGraph, ...]:
        """Lista KnowledgeGraphs do tenant.

        Returns:
            Ordenado por (patient_id ASC, graph_id ASC).
        """
        ...
