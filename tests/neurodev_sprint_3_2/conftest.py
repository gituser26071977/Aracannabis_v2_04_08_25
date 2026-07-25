"""
Fixtures compartilhadas para tests/neurodev_sprint_3_2.

Stack de testes:
    - SQLite in-memory (isolamento total por teste)
    - InMemoryClinicalEventStore (não persiste entre processos)
    - REDACTED (materializa Registry)
    - Application services (ClinicalIdentity/Diagnosis/Phenotype/Intervention/Assessment/Outcome)
"""
from __future__ import annotations

import os
import sys

# Garante que o diretório raiz está no sys.path ANTES de qualquer import
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.clinical.event_store import (
    ClinicalEventPublisher,
    InMemoryClinicalEventStore,
)
from araos.specialties.neurodevelopmental.projections import (
    REDACTED,
    db_models,  # importa para registrar tabelas no Base.metadata
)


@pytest.fixture
def engine():
    """SQLite in-memory compartilhado entre todas as sessões."""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Cria todas as tabelas projection
    db_models.Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    """sessionmaker() bound ao engine in-memory."""
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def event_store() -> InMemoryClinicalEventStore:
    """In-memory Event Store — sequence/hash chain preservados na memória."""
    return InMemoryClinicalEventStore()


@pytest.fixture
def publisher(event_store: InMemoryClinicalEventStore):
    """ClinicalEventPublisher com validação desabilitada (testes unitários)."""
    return ClinicalEventPublisher(store=event_store, validate_payload=False)


@pytest.fixture
def projection(event_store, session_factory):
    """Projection — conectada ao Event Store + session SQLAlchemy."""
    return REDACTED(
        event_store=event_store,
        session_factory=session_factory,
    )
