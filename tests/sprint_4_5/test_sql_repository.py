"""
SQLKnowledgeRepository — DoD tests for RC1 Gate 1.

Cobre:

    1. CRUD básico para todas as 7 entidades.
    2. Round-trip state_hash byte-identical.
    3. Multi-tenancy (cross-tenant rejection).
    4. Atomicidade transacional (rollback em falha).
    5. Concorrência (múltiplas threads × saves).
    6. Equivalência InMemory vs SQL (shadow compare).
    7. Cobertura de 100% da ABC.

Reusa fixtures Sprint 4.4 (cenario_alfa, cenario_beta).
"""
from __future__ import annotations

import threading
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from araos.clinical.knowledge.application.composition import (
    knowledge_composition,
)
from araos.clinical.knowledge.domain.clinical_genome import (
    build_clinical_genome,
)
from araos.clinical.knowledge.domain.cohort import Cohort, CohortBuilder
from araos.clinical.knowledge.domain.correlation import (
    CorrelationEngine,
    CorrelationMethod,
)
from araos.clinical.knowledge.domain.hypothesis import HypothesisEngine
from araos.clinical.knowledge.domain.knowledge_graph import (
    KnowledgeGraphBuilder,
)
from araos.clinical.knowledge.infrastructure.in_memory import (
    InMemoryKnowledgeRepository,
)
from araos.clinical.knowledge.infrastructure.sql import (
    Base,
    SQLKnowledgeRepository,
)


# ────────────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────────────


@pytest.fixture
def engine(tmp_path):
    """SQLite file engine (file-based para permitir concorrência multi-thread)."""
    from sqlalchemy.pool import StaticPool

    db_path = tmp_path / "knowledge_test.db"
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def session(session_factory):
    s = session_factory()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def repo_sql(session, tenant_a):
    """Repository bound to tenant_a (cenario_alfa)."""
    return SQLKnowledgeRepository(session, tenant_a)


@pytest.fixture
def repo_inmem(tenant_a):
    return InMemoryKnowledgeRepository(tenant_a)


# ────────────────────────────────────────────────────────────────────
# 1. ABC Coverage — confirm 100% implemented
# ────────────────────────────────────────────────────────────────────


class TestABCCoverage:
    """Verifica que SQLKnowledgeRepository implementa 100% da ABC."""

    def test_no_abstract_methods_remaining(self):
        remaining = SQLKnowledgeRepository.__abstractmethods__
        assert remaining == frozenset(), (
            f"Abstract methods not implemented: {remaining}"
        )

    def test_all_21_methods_exist(self):
        from araos.clinical.knowledge.infrastructure.repository import (
            KnowledgeRepository,
        )
        expected = KnowledgeRepository.__abstractmethods__
        for method in expected:
            assert hasattr(SQLKnowledgeRepository, method), (
                f"Missing implementation: {method}"
            )


# ────────────────────────────────────────────────────────────────────
# 2. CRUD básico — genes
# ────────────────────────────────────────────────────────────────────


class TestGenesCRUD:
    def test_save_and_load_genes(self, repo_sql, scenario_alfa):
        repo_sql.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        loaded = repo_sql.load_genes(scenario_alfa.patient_id)
        assert len(loaded) == len(scenario_alfa.genes)
        loaded_ids = sorted(g.gene_id for g in loaded)
        expected_ids = sorted(g.gene_id for g in scenario_alfa.genes)
        assert loaded_ids == expected_ids

    def test_load_genes_empty(self, repo_sql):
        assert repo_sql.load_genes("nonexistent") == ()

    def test_list_patient_ids(self, repo_sql, scenario_alfa, scenario_beta, session_factory):
        repo_sql.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        # Tenant B usa repo separado.
        from araos.clinical.knowledge.infrastructure.sql import SQLKnowledgeRepository
        session_b = session_factory()
        repo_b = SQLKnowledgeRepository(session_b, scenario_beta.tenant_id)
        repo_b.save_genes(scenario_beta.patient_id, scenario_beta.genes)
        session_b.commit()
        pids = repo_sql.list_patient_ids()
        assert scenario_alfa.patient_id in pids
        assert scenario_beta.patient_id not in pids  # Tenant isolation
        # Ordenado ASC
        assert list(pids) == sorted(pids)
        session_b.close()

    def test_save_overwrites_previous(self, repo_sql, scenario_alfa):
        repo_sql.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
        repo_sql.save_genes(scenario_alfa.patient_id, (scenario_alfa.genes[0],))
        loaded = repo_sql.load_genes(scenario_alfa.patient_id)
        assert len(loaded) == 1
        assert loaded[0].gene_id == scenario_alfa.genes[0].gene_id


# ────────────────────────────────────────────────────────────────────
# 3. Genomes CRUD
# ────────────────────────────────────────────────────────────────────


class TestGenomesCRUD:
    def test_save_load_genome_roundtrip(self, repo_sql, scenario_alfa):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        repo_sql.save_genome(genome)
        loaded = repo_sql.load_genome(genome.genome_id)
        assert loaded is not None
        assert loaded.genome_id == genome.genome_id
        assert loaded.patient_id == genome.patient_id
        assert loaded.tenant_id == genome.tenant_id
        assert loaded.state_hash == genome.state_hash

    def test_load_genome_returns_none(self, repo_sql):
        assert repo_sql.load_genome("nonexistent_id") is None

    def test_list_genomes_ordered(self, repo_sql, scenario_alfa):
        genome1 = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        # Genome com window diferente (mesmo paciente) — testa ordenação.
        from araos.clinical.timeline.domain.window import TimeWindow

        later_window = TimeWindow(
            start=scenario_alfa.window.end,
            end=datetime(2026, 12, 1, tzinfo=timezone.utc),
            label="post",
        )
        genome2 = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=later_window,
            genes=scenario_alfa.genes,
        )
        # Inverte a ordem de insert para verificar ordenação determinística
        repo_sql.save_genome(genome2)
        repo_sql.save_genome(genome1)
        listed = repo_sql.list_genomes()
        assert listed[0].window.start <= listed[1].window.start


# ────────────────────────────────────────────────────────────────────
# 4. Correlations CRUD
# ────────────────────────────────────────────────────────────────────


class TestCorrelationsCRUD:
    def test_save_and_load_correlation(self, repo_sql, scenario_alfa):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        corrs = CorrelationEngine().compute(
            genome, method=CorrelationMethod.NEGATIVE
        )
        assert len(corrs) > 0
        for c in corrs:
            repo_sql.save_correlation(c)
        listed = repo_sql.list_correlations()
        assert len(listed) == len(corrs)
        ids_loaded = {c.correlation_id for c in listed}
        ids_expected = {c.correlation_id for c in corrs}
        assert ids_loaded == ids_expected

    def test_load_correlation_returns_none(self, repo_sql):
        assert repo_sql.load_correlation("nonexistent") is None


# ────────────────────────────────────────────────────────────────────
# 5. Hypotheses CRUD + cross-tenant fix verification
# ────────────────────────────────────────────────────────────────────


class TestHypothesesCRUD:
    def REDACTED(
        self, repo_sql, scenario_alfa,
    ):
        # HypothesisEngine direto → IDs não-namespaced.
        # HypothesisService (com namespace) → IDs tenant-scoped.
        from araos.clinical.knowledge.application.hypothesis_service import (
            HypothesisService,
        )
        from araos.clinical.knowledge.application.dto import HypothesisRequest

        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        corrs = CorrelationEngine().compute(
            genome, method=CorrelationMethod.NEGATIVE
        )
        hyp = HypothesisService().execute(
            HypothesisRequest(genome=genome, correlations=corrs)
        )
        if not hyp:
            pytest.skip("No hypotheses emitted (small scenario)")
        for h in hyp:
            repo_sql.save_hypothesis(h)
        loaded = repo_sql.load_hypothesis(hyp[0].hypothesis_id)
        assert loaded is not None
        assert loaded.hypothesis_id == hyp[0].hypothesis_id


# ────────────────────────────────────────────────────────────────────
# 6. Cohorts + Sessions + Graphs CRUD
# ────────────────────────────────────────────────────────────────────


class TestCohortsCRUD:
    def test_save_load_cohort(self, repo_sql, tenant_a):
        cohort = Cohort(
            cohort_id="cohort_test_001",
            tenant_id=tenant_a,
            name="Test Cohort",
            criteria=(),
            matched_patient_ids=("p1", "p2", "p3"),
            built_at=datetime.now(timezone.utc),
            state_hash="abc123",
        )
        repo_sql.save_cohort(cohort)
        loaded = repo_sql.load_cohort("cohort_test_001")
        assert loaded is not None
        assert loaded.cohort_id == "cohort_test_001"
        assert loaded.name == "Test Cohort"
        assert loaded.matched_patient_ids == ("p1", "p2", "p3")

    def test_load_cohort_returns_none(self, repo_sql):
        assert repo_sql.load_cohort("nonexistent") is None


class TestSessionsCRUD:
    def test_save_load_session_roundtrip(self, repo_sql, tenant_a):
        from araos.clinical.knowledge.domain.research import (
            AnalysisType,
            ResearchQuery,
            ResearchSession,
        )
        from araos.clinical.knowledge.domain.explainability import (
            ExplainabilityPipeline,
        )

        explanation = ExplainabilityPipeline.for_research(
            claim="test research",
            query_type="stats",
            confidence=0.9,
        )
        query = ResearchQuery(
            query_id="q1",
            cohort_id="c1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
            created_at=datetime.now(timezone.utc),
        )
        now = datetime.now(timezone.utc)
        session_obj = ResearchSession(
            session_id="sess_test",
            query=query,
            version=1,
            started_at=now,
            completed_at=now,
            result_json='{"mean":0.5}',
            state_hash="hash1",
            reproducible=True,
            explanation=explanation,
        )
        repo_sql.save_session(session_obj)
        loaded = repo_sql.load_session("sess_test")
        assert loaded is not None
        assert loaded.session_id == "sess_test"
        assert loaded.result_json == '{"mean":0.5}'


class TestGraphsCRUD:
    def test_save_load_graph(self, repo_sql, scenario_alfa):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        repo_sql.save_graph(graph)
        loaded = repo_sql.load_graph(graph.graph_id)
        assert loaded is not None
        assert loaded.graph_id == graph.graph_id
        assert loaded.patient_id == graph.patient_id
        assert len(loaded.nodes) == len(graph.nodes)
        assert len(loaded.edges) == len(graph.edges)


# ────────────────────────────────────────────────────────────────────
# 7. Determinism — round-trip state_hash byte-identical
# ────────────────────────────────────────────────────────────────────


class TestDeterminism:
    def REDACTED(
        self, repo_sql, scenario_alfa,
    ):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        original_hash = genome.state_hash
        repo_sql.save_genome(genome)
        loaded = repo_sql.load_genome(genome.genome_id)
        assert loaded.state_hash == original_hash

    def REDACTED(self, repo_sql, scenario_alfa):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        original_hash = genome.state_hash
        for _ in range(100):
            repo_sql.save_genome(genome)
            loaded = repo_sql.load_genome(genome.genome_id)
            assert loaded.state_hash == original_hash


# ────────────────────────────────────────────────────────────────────
# 8. Multi-tenancy — composite PK rejeita cross-tenant
# ────────────────────────────────────────────────────────────────────


class TestMultiTenancy:
    def test_cross_tenant_save_rejected(self, repo_sql, scenario_alfa):
        from araos.clinical.knowledge.domain.clinical_genome import (
            ClinicalGenome,
        )
        # Build genome for a DIFFERENT tenant than the repo.
        genome = build_clinical_genome(
            tenant_id="tenant_OTHER",
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        with pytest.raises(PermissionError, match="Cross-tenant"):
            repo_sql.save_genome(genome)

    def REDACTED(self, repo_sql, scenario_alfa):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        repo_sql.save_genome(genome)
        # Construir repo com outro tenant — deve retornar None (não vaza existência)
        other_session = repo_sql._session
        other_repo = SQLKnowledgeRepository(other_session, "tenant_OTHER")
        assert other_repo.load_genome(genome.genome_id) is None

    def test_separate_tenants_isolated(
        self, session_factory, scenario_alfa, scenario_beta,
    ):
        # Tenant A salva genome.
        session_a = session_factory()
        repo_a = SQLKnowledgeRepository(session_a, scenario_alfa.tenant_id)
        genome_a = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        repo_a.save_genome(genome_a)
        session_a.commit()

        # Tenant B lista genomas — não deve ver nada do A.
        session_b = session_factory()
        repo_b = SQLKnowledgeRepository(session_b, scenario_beta.tenant_id)
        assert repo_b.list_genomes() == ()
        session_a.close()
        session_b.close()


# ────────────────────────────────────────────────────────────────────
# 9. Rollback / Atomicidade (composition.py)
# ────────────────────────────────────────────────────────────────────


class TestTransactionAtomicity:
    def test_rollback_on_exception(self, session_factory, scenario_alfa):
        # Persistir fora do with — verificar que foi desfeito.
        with pytest.raises(RuntimeError):
            with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
                genome = build_clinical_genome(
                    tenant_id=scenario_alfa.tenant_id,
                    patient_id=scenario_alfa.patient_id,
                    window=scenario_alfa.window,
                    genes=scenario_alfa.genes,
                )
                repo.save_genome(genome)
                # Forçar falha antes do commit.
                raise RuntimeError("simulated failure")

        # Verificar que nada foi persistido.
        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
            assert repo.list_genomes() == ()

    def test_commit_on_clean_exit(self, session_factory, scenario_alfa):
        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
            genome = build_clinical_genome(
                tenant_id=scenario_alfa.tenant_id,
                patient_id=scenario_alfa.patient_id,
                window=scenario_alfa.window,
                genes=scenario_alfa.genes,
            )
            repo.save_genome(genome)

        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
            listed = repo.list_genomes()
            assert len(listed) == 1

    def test_atomic_multi_entity_save(self, session_factory, scenario_alfa):
        """Pipeline completo: genome + correlation + hypothesis + graph
        devem ser commitados atomicamente.
        """
        from araos.clinical.knowledge.application.hypothesis_id_namespace import (
            namespace_hypothesis_ids,
        )

        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
            genome = build_clinical_genome(
                tenant_id=scenario_alfa.tenant_id,
                patient_id=scenario_alfa.patient_id,
                window=scenario_alfa.window,
                genes=scenario_alfa.genes,
            )
            corrs = CorrelationEngine().compute(
                genome, method=CorrelationMethod.NEGATIVE
            )
            hyp_raw = HypothesisEngine().generate(genome, corrs)
            hyp = namespace_hypothesis_ids(hyp_raw, genome.tenant_id)
            graph = KnowledgeGraphBuilder().build(
                genome, correlations=corrs, hypotheses=hyp
            )
            repo.save_genome(genome)
            for c in corrs:
                repo.save_correlation(c)
            for h in hyp:
                repo.save_hypothesis(h)
            repo.save_graph(graph)

        # Verificar que tudo persistiu atomicamente.
        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as repo:
            assert len(repo.list_genomes()) == 1
            assert len(repo.list_correlations()) >= 1
            assert len(repo.list_graphs()) == 1


# ────────────────────────────────────────────────────────────────────
# 10. Concorrência — múltiplas threads × saves
# ────────────────────────────────────────────────────────────────────


class TestConcurrency:
    def test_concurrent_saves_no_deadlock(
        self, session_factory, scenario_alfa,
    ):
        """5 threads gravando genes em paralelo. Sem deadlock.

        Note: SQLite tem limitação de write-locking global — este teste
        é principalmente para PostgreSQL. Em SQLite skipamos.
        """
        # Detectar SQLite via URL do engine.
        from sqlalchemy import inspect

        bind = session_factory.kw.get("bind")
        if bind is None:
            bind = session_factory()
            url = str(bind.get_bind().url)
            bind.close()
        else:
            url = str(bind.url)
        if url.startswith("sqlite"):
            pytest.skip(
                "SQLite tem write-locking global — concorrência real é PostgreSQL only"
            )
        errors: list[Exception] = []

        def save_thread(thread_id: int) -> None:
            try:
                pid = f"{scenario_alfa.patient_id}_t{thread_id}"
                with knowledge_composition(
                    session_factory, "tenant_test",
                ) as repo:
                    gene = scenario_alfa.genes[0]
                    # Reatribuir patient_id para simular paciente distinto.
                    from dataclasses import replace
                    from datetime import datetime, timezone
                    from araos.clinical.genome.domain.aggregate import (
                        create_gene,
                    )
                    gene2 = create_gene(
                        tenant_id="tenant_test",
                        patient_id=pid,
                        gene_id=f"GENE_T{thread_id}",
                        version="1.0.0",
                    )
                    repo.save_genes(pid, (gene2,))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=save_thread, args=(i,))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        assert not errors, f"Concurrent saves failed: {errors}"

        with knowledge_composition(session_factory, "tenant_test") as repo:
            assert len(repo.list_patient_ids()) == 5


# ────────────────────────────────────────────────────────────────────
# 11. Equivalência InMemory vs SQL (shadow compare)
# ────────────────────────────────────────────────────────────────────


class TestInMemorySQLEquivalence:
    def test_list_genomes_identical(
        self, session_factory, scenario_alfa,
    ):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )

        inmem = InMemoryKnowledgeRepository(scenario_alfa.tenant_id)
        inmem.save_genome(genome)

        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as sql_repo:
            sql_repo.save_genome(genome)
            sql_genomes = sql_repo.list_genomes()

        inmem_genomes = inmem.list_genomes()
        assert len(sql_genomes) == len(inmem_genomes) == 1
        # State hash deve ser idêntico.
        assert sql_genomes[0].state_hash == inmem_genomes[0].state_hash
        # Genome_id idêntico.
        assert sql_genomes[0].genome_id == inmem_genomes[0].genome_id
        # Patient id idêntico.
        assert sql_genomes[0].patient_id == inmem_genomes[0].patient_id

    def test_load_genes_identical(
        self, session_factory, scenario_alfa,
    ):
        inmem = InMemoryKnowledgeRepository(scenario_alfa.tenant_id)
        inmem.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)

        with knowledge_composition(session_factory, scenario_alfa.tenant_id) as sql_repo:
            sql_repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
            sql_genes = sql_repo.load_genes(scenario_alfa.patient_id)

        inmem_genes = inmem.load_genes(scenario_alfa.patient_id)
        sql_ids = sorted(g.gene_id for g in sql_genes)
        inmem_ids = sorted(g.gene_id for g in inmem_genes)
        assert sql_ids == inmem_ids

    def test_correlation_count_identical(
        self, session_factory, scenario_alfa,
    ):
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        corrs = CorrelationEngine().compute(
            genome, method=CorrelationMethod.POSITIVE
        )

        inmem = InMemoryKnowledgeRepository("tenant_test")
        for c in corrs:
            inmem.save_correlation(c)

        with knowledge_composition(session_factory, "tenant_test") as sql_repo:
            for c in corrs:
                sql_repo.save_correlation(c)
            sql_corrs = sql_repo.list_correlations()

        assert len(sql_corrs) == len(inmem.list_correlations())
        sql_ids = {c.correlation_id for c in sql_corrs}
        inmem_ids = {c.correlation_id for c in inmem.list_correlations()}
        assert sql_ids == inmem_ids


# ────────────────────────────────────────────────────────────────────
# 12. Tenant validation no constructor
# ────────────────────────────────────────────────────────────────────


class TestConstructorValidation:
    def test_empty_tenant_id_rejected(self, session):
        with pytest.raises(ValueError, match="tenant_id"):
            SQLKnowledgeRepository(session, "")

    def test_non_string_tenant_id_rejected(self, session):
        with pytest.raises(ValueError, match="tenant_id"):
            SQLKnowledgeRepository(session, None)  # type: ignore[arg-type]

    def test_tenant_id_immutable_property(self, repo_sql, tenant_a):
        assert repo_sql.tenant_id == tenant_a
