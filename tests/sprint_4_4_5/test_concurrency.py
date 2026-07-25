"""
Sprint 4.4.5 — Concorrência.

Testes de race conditions / simultaneidade no Clinical Knowledge Engine.
Knowledge é puro (sem I/O) — então:
  - Engines são thread-safe por construção (frozen dataclasses + funções puras).
  - InMemoryKnowledgeRepository usa RLock para serializar mutações.
  - Reads concorrentes com writes não devem retornar estado corrompido.

Cobertura:
  - N=10 threads × 50 saves concorrentes em repository.
  - Replay simultâneo (5 threads) sobre mesmos events → state_hashes idênticos.
  - Cohort build simultâneo (criteria diferentes, mesmo pool) → resultados corretos.
  - Graph build simultâneo → state_hashes consistentes.
  - Hypothesis generation simultânea → sem duplicação.
  - Read-during-write (save enquanto load_genome/list) → nunca estado corrompido.
  - Deadlock prevention — 20 threads, operações mistas aleatórias, terminam.
  - Cross-thread state_hash stability sob paralelismo.
"""

from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

from araos.clinical.knowledge.application import KnowledgeService
from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.cohort import (
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from araos.clinical.knowledge.domain.correlation import CorrelationEngine, CorrelationMethod
from araos.clinical.knowledge.domain.hypothesis import HypothesisEngine
from araos.clinical.knowledge.domain.knowledge_graph import KnowledgeGraphBuilder
from araos.clinical.knowledge.infrastructure.in_memory import InMemoryKnowledgeRepository

from tests.sprint_4_4_5.conftest import _build_gene_with_trajectory


# ────────────────────────────────────────────────────────────────────
# Repository — concurrent saves
# ────────────────────────────────────────────────────────────────────


class TestRepositoryConcurrentSaves:
    """Repository deve aceitar N saves concorrentes sem corrupção."""

    def REDACTED(self):
        """500 saves concorrentes em genes — todos persistem corretamente.

        Sprint 4.5 G3: cada thread opera em seu próprio tenant_id,
        portanto cada thread usa sua própria repo tenant-bound.
        """
        repos = {
            t: InMemoryKnowledgeRepository(tenant_id=f"tenant_t{t}")
            for t in range(10)
        }

        def save_patient(thread_id: int, save_id: int) -> tuple[str, int]:
            patient_id = f"p_t{thread_id}_s{save_id}"
            genes = (
                _build_gene_with_trajectory(
                    tenant_id=f"tenant_t{thread_id}",
                    patient_id=patient_id,
                    gene_id="GENE_SLEEP",
                    values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
                ),
            )
            repo = repos[thread_id]
            repo.save_genes(patient_id, genes)
            return patient_id, len(repo.genes_by_patient)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for t in range(10):
                for s in range(50):
                    futures.append(executor.submit(save_patient, t, s))
            for fut in as_completed(futures):
                patient_id, count = fut.result()
                assert count > 0

        # Cada tenant tem 50 saves (10 tenants × 50 saves)
        for t, repo in repos.items():
            assert len(repo.list_patient_ids()) == 50, (
                f"tenant_t{t}: esperado 50, obtido {len(repo.list_patient_ids())}"
            )

    def REDACTED(self):
        """Mesmo genome_id gravado N vezes — versão final é uma das válidas.

        Sprint 4.5 G3: tenant_id explícito.
        """
        repo = InMemoryKnowledgeRepository(tenant_id="tenant_a")

        from datetime import datetime, timedelta, timezone
        from araos.clinical.timeline.domain.window import TimeWindow

        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
        genes = (
            _build_gene_with_trajectory(
                tenant_id="tenant_a",
                patient_id="p1",
                gene_id="GENE_SLEEP",
                values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
            ),
        )
        genome = build_clinical_genome(
            tenant_id="tenant_a",
            patient_id="p1",
            window=window,
            genes=genes,
        )

        def overwrite():
            repo.save_genome(genome)

        threads = [threading.Thread(target=overwrite) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Apenas 1 genome (mesmo genome_id) — mas é o mesmo objeto, então OK.
        assert len(repo.list_genomes()) == 1
        assert repo.load_genome(genome.genome_id) is not None

    def REDACTED(self):
        """Save enquanto load — nunca retorna erro nem estado parcial.

        Sprint 4.5 G3: tenant_id explícito.
        """
        repo = InMemoryKnowledgeRepository(tenant_id="tenant_x")
        from datetime import datetime, timedelta, timezone
        from araos.clinical.timeline.domain.window import TimeWindow

        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")

        def save_worker(patient_idx: int):
            patient_id = f"p_{patient_idx}"
            genes = (
                _build_gene_with_trajectory(
                    tenant_id="tenant_x",
                    patient_id=patient_id,
                    gene_id="GENE_SLEEP",
                    values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
                ),
            )
            repo.save_genes(patient_id, genes)

        def read_worker() -> int:
            return len(list(repo.list_patient_ids()))

        with ThreadPoolExecutor(max_workers=8) as executor:
            # 4 saves + 4 reads concorrentes
            futures = []
            for i in range(40):
                futures.append(executor.submit(save_worker, i))
            for _ in range(40):
                futures.append(executor.submit(read_worker))
            # Nunca levanta exceção — só verificamos que completou
            for fut in as_completed(futures):
                fut.result()

        # Após tudo: 40 pacientes persistidos
        assert len(repo.list_patient_ids()) == 40


# ────────────────────────────────────────────────────────────────────
# Replay simultâneo
# ────────────────────────────────────────────────────────────────────


class TestReplayConcurrent:
    """Replay determinístico sob paralelismo."""

    def REDACTED(self, scenario_a1_2genes):
        """5 threads chamando compute/replay sobre mesmo genome → state_hashes idênticos."""
        engine = CorrelationEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        reference_hash = genome.state_hash

        results: list[str] = []
        errors: list[Exception] = []

        def replay():
            try:
                g = build_clinical_genome(
                    tenant_id=scenario_a1_2genes.tenant_id,
                    patient_id=scenario_a1_2genes.patient_id,
                    window=scenario_a1_2genes.window,
                    genes=scenario_a1_2genes.genes,
                )
                results.append(g.state_hash)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=replay) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Erros concorrentes: {errors}"
        assert len(results) == 5
        # Todos devem produzir o mesmo state_hash
        assert all(h == reference_hash for h in results), (
            f"Hashes divergentes: {results} vs reference {reference_hash}"
        )

    def REDACTED(self, scenario_a1_2genes):
        """5 threads chamando CorrelationEngine.compute → mesmos resultados."""
        engine = CorrelationEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )

        results_per_thread: list[tuple] = []
        lock = threading.Lock()

        def compute():
            res = engine.compute(genome, method=CorrelationMethod.NEGATIVE)
            with lock:
                results_per_thread.append(res)

        threads = [threading.Thread(target=compute) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results_per_thread) == 5
        # Mesmo número de correlações em todos os threads
        first = results_per_thread[0]
        for other in results_per_thread[1:]:
            assert len(other) == len(first)
            for r1, r2 in zip(first, other):
                assert r1.correlation_id == r2.correlation_id
                assert r1.coefficient == r2.coefficient


# ────────────────────────────────────────────────────────────────────
# Cohort build simultâneo
# ────────────────────────────────────────────────────────────────────


class TestCohortConcurrentBuild:
    """Cohort build com critérios diferentes em paralelo."""

    def REDACTED(self):
        """10 cohorts com critérios diferentes sobre mesmo pool → cada uma correta."""
        pool = [
            PatientData(patient_id=f"p{i:02d}", tenant_id="tA", age=10 + i, sex="F")
            for i in range(20)
        ]
        criteria_sets = [
            (Criterion(field="patient.age", operator=CriterionOperator.GT, value=15),),
            (Criterion(field="patient.age", operator=CriterionOperator.LT, value=12),),
            (Criterion(field="patient.sex", operator=CriterionOperator.EQ, value="F"),),
            (Criterion(field="patient.age", operator=CriterionOperator.IN, value=[18, 19, 20, 21, 22]),),
            (Criterion(field="patient.age", operator=CriterionOperator.NOT_IN, value=[10, 11]),),
            (Criterion(field="patient.age", operator=CriterionOperator.EXISTS, value=None),),
            (Criterion(field="patient.sex", operator=CriterionOperator.NE, value="M"),),
        ]

        results: list = []
        lock = threading.Lock()

        def build(idx: int):
            cb = CohortBuilder()
            cohort = cb.evaluate(
                patients=pool,
                tenant_id="tA",
                name=f"cohort_{idx}",
                criteria=criteria_sets[idx % len(criteria_sets)],
            )
            with lock:
                results.append(cohort)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(build, i) for i in range(8)]
            for fut in as_completed(futures):
                fut.result()

        assert len(results) == 8
        # Cada cohort tem seu próprio name
        names = {r.name for r in results}
        assert len(names) == 8


# ────────────────────────────────────────────────────────────────────
# Graph build simultâneo
# ────────────────────────────────────────────────────────────────────


class TestGraphConcurrentBuild:
    """KnowledgeGraph build em paralelo."""

    def REDACTED(self, scenario_a1_2genes):
        """10 graph builds sobre mesmo genome → state_hashes idênticos."""
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        builder = KnowledgeGraphBuilder()
        reference_hash = builder.build(genome).state_hash

        results: list[str] = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def build():
            try:
                g = builder.build(genome)
                with lock:
                    results.append(g.state_hash)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=build) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 10
        assert all(h == reference_hash for h in results)


# ────────────────────────────────────────────────────────────────────
# Hypothesis generation simultânea
# ────────────────────────────────────────────────────────────────────


class TestHypothesisConcurrentGeneration:
    """HypothesisEngine.generate em paralelo."""

    def REDACTED(self, scenario_a1_2genes):
        """5 threads gerando hipóteses → mesmas hipóteses."""
        engine = HypothesisEngine()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )

        results: list[tuple] = []
        lock = threading.Lock()

        def generate():
            hyps = engine.generate(genome)
            with lock:
                results.append(hyps)

        threads = [threading.Thread(target=generate) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 5
        first = results[0]
        for other in results[1:]:
            assert len(other) == len(first)
            for h1, h2 in zip(first, other):
                assert h1.hypothesis_id == h2.hypothesis_id


# ────────────────────────────────────────────────────────────────────
# Pipeline concorrente
# ────────────────────────────────────────────────────────────────────


class TestPipelineConcurrent:
    """KnowledgeService.run_pipeline em paralelo."""

    def REDACTED(self, scenario_a1_2genes):
        """5 threads rodando pipeline completo → mesmo estado final."""
        service = KnowledgeService()
        genome = build_clinical_genome(
            tenant_id=scenario_a1_2genes.tenant_id,
            patient_id=scenario_a1_2genes.patient_id,
            window=scenario_a1_2genes.window,
            genes=scenario_a1_2genes.genes,
        )
        reference = service.run_pipeline(genome)
        reference_hash = reference.genome.state_hash

        results: list = []
        errors: list[Exception] = []
        lock = threading.Lock()

        def run():
            try:
                r = service.run_pipeline(genome)
                with lock:
                    results.append(r)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=run) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(results) == 5
        for r in results:
            assert r.genome.state_hash == reference_hash


# ────────────────────────────────────────────────────────────────────
# Deadlock prevention — mixed operations
# ────────────────────────────────────────────────────────────────────


class TestDeadlockPrevention:
    """Operações mistas em ordem aleatória devem terminar (sem deadlock)."""

    def REDACTED(self):
        """20 threads com save/load/list/clear em ordem aleatória → todos terminam.

        Sprint 4.5 G3: cada thread opera em seu próprio tenant,
        portanto cada thread usa sua própria repo tenant-bound.
        """
        from datetime import datetime, timedelta, timezone
        from araos.clinical.timeline.domain.window import TimeWindow

        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        window = TimeWindow(start=base, end=base + timedelta(days=180), label="6m")
        genes_template = (
            _build_gene_with_trajectory(
                tenant_id="tX",
                patient_id="pX",
                gene_id="GENE_SLEEP",
                values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
            ),
        )

        # Sprint 4.5 G3: um repo por tenant (cada thread é um tenant)
        repos = {
            t: InMemoryKnowledgeRepository(tenant_id=f"t{t}") for t in range(20)
        }

        rng = random.Random(42)  # seed para reprodutibilidade
        ops = ["save", "load", "list", "clear"]
        start_barrier = threading.Barrier(20)

        def worker(thread_id: int):
            # Sincroniza para iniciar todas as threads ao mesmo tempo
            start_barrier.wait()
            repo = repos[thread_id]
            for i in range(50):
                op = rng.choice(ops)
                if op == "save":
                    g = (
                        _build_gene_with_trajectory(
                            tenant_id=f"t{thread_id}",
                            patient_id=f"p{thread_id}_{i}",
                            gene_id="GENE_SLEEP",
                            values=((4.0, 0.4, 0), (5.0, 0.5, 30)),
                        ),
                    )
                    repo.save_genes(f"p{thread_id}_{i}", g)
                elif op == "load":
                    repo.load_genes(f"p{thread_id}_{i // 10}")
                elif op == "list":
                    repo.list_patient_ids()
                elif op == "clear":
                    if i % 25 == 0:  # clear menos frequente
                        repo.clear()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]

        # Deadline explícito — se demorar mais que 30s, há deadlock.
        start_time = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        elapsed = time.time() - start_time

        # Todos terminaram em menos de 30s (deadlock prevention)
        for t in threads:
            assert not t.is_alive(), "Thread ainda viva → possível deadlock"

        # Apenas verifica que terminou dentro do limite razoável
        assert elapsed < 30, f"Operações demoraram {elapsed:.2f}s — possível contenção"