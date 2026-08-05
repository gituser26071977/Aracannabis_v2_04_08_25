"""
Knowledge Composition — Sprint 4.5 W2.1 (RC1 Gate 1).

Context manager para execução transacional do pipeline Knowledge.

Princípio fundamental (do RC1 Engineering Review):

    ``Session + context manager`` JÁ É Unit of Work.

    Não há precedente de UoW no AraOS (grep confirmou). A Session do
    SQLAlchemy 2.0 já garante atomicidade, isolamento, rollback,
    flush. Criar uma classe ``KnowledgeUnitOfWork`` paralela seria
    duplicação pura. Este módulo entrega a MESMA garantia via
    ``@contextmanager`` explícito.

Uso típico:

    with knowledge_composition(session_factory, tenant_id) as repo:
        repo.save_genome(genome)
        repo.save_correlation(corr)
        # commit automático no __exit__ se não houve exceção;
        # rollback automático se houve.

Ou para produção (REST endpoint / CLI):

    with knowledge_composition(session_factory, tenant_id) as repo:
        result = KnowledgeService().run_pipeline(genome)
        repo.save_genome(result.genome)
        repo.save_correlation_batch(result.correlations)
        repo.save_hypothesis_batch(result.hypotheses)
        if result.graph:
            repo.save_graph(result.graph)
        # Commit atômico ao sair do bloco.

Compatibilidade:

    - SQLAlchemy 2.0+ declarativo.
    - PostgreSQL (produção) e SQLite (testes).
    - session_factory: callable que retorna ``sqlalchemy.orm.Session``.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from sqlalchemy.orm import Session

from ..infrastructure.sql import SQLKnowledgeRepository


@contextmanager
def knowledge_composition(
    session_factory: Callable[[], Session],
    tenant_id: str,
) -> Iterator[SQLKnowledgeRepository]:
    """Context manager transacional para SQLKnowledgeRepository.

    Args:
        session_factory: callable que produz uma ``Session``.
            Em Flask-SQLAlchemy: ``lambda: db.session``.
            Em SQLAlchemy puro: ``SessionLocal``.
        tenant_id: identificador do tenant (organização).

    Yields:
        ``SQLKnowledgeRepository`` bound à session da transação.

    Raises:
        Propaga exceção original após rollback.

    Note:
        - Commit no __exit__ se nenhuma exceção.
        - Rollback no __exit__ se exceção.
        - Session sempre é fechada após uso.
    """
    session = session_factory()
    repo = SQLKnowledgeRepository(session, tenant_id)
    try:
        yield repo
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
