"""
conftest.py — fixtures Sprint 4.1 (Timeline + Explainability).

Reuso do padrão Sprint 3.2 (tests/neurodev_sprint_3_2/conftest.py):
- sys.path injection (2 níveis acima → raiz do repo)
- SQLite in-memory
- InMemoryClinicalEventStore + ClinicalEventPublisher
- session_factory
- fixtures para cada componente

Adições Sprint 4.1:
- engine específico para Explainability (tabelas intelligence_*)
- fixture `explanation_registry` (InMemory)
- fixture `app` Flask com blueprints intelligence + JWT mock
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Generator

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.clinical.event_store import (
    ClinicalEventPublisher,
    InMemoryClinicalEventStore,
)
from araos.clinical.explainability import (
    Explanation,
    InMemoryExplanationRegistry,
)
from araos.clinical.explainability.registry import ExplanationRegistry
from araos.clinical.timeline.application.query import InMemoryTimelineQuery
from araos.clinical.timeline.domain.entries import TimelineEntry


# ─── SQLite in-memory + tables Sprint 4.1 ─────────────────────────────


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Importa models (Sprint 4.1) e cria tabelas
    from araos.clinical.explainability.sql import (
        IntelligenceExplanationModel,
        REDACTED,
    )
    IntelligenceExplanationModel.metadata.create_all(eng)
    REDACTED.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False)


# ─── Event Store + Publisher (padrão Sprint 3.2) ──────────────────────


@pytest.fixture
def event_store() -> InMemoryClinicalEventStore:
    return InMemoryClinicalEventStore()


@pytest.fixture
def publisher(event_store) -> ClinicalEventPublisher:
    return ClinicalEventPublisher(store=event_store, validate_payload=False)


@pytest.fixture
def timeline_query(event_store) -> InMemoryTimelineQuery:
    return InMemoryTimelineQuery(event_store=event_store)


# ─── Explainability Registry ─────────────────────────────────────────


@pytest.fixture
def explanation_registry() -> ExplanationRegistry:
    """InMemory registry — para testes que não precisam de DB."""
    return InMemoryExplanationRegistry()


@pytest.fixture
def sql_explanation_registry(session_factory) -> ExplanationRegistry:
    """SQLAlchemy registry — para testes de integração DB."""
    from araos.clinical.explainability.sql import SqlAlchemyExplanationRegistry
    return SqlAlchemyExplanationRegistry(session_factory=session_factory)


# ─── Flask app fixture (JWT mock para testes de API) ─────────────────


@pytest.fixture
def app(event_store, explanation_registry):
    """Flask app minimal com blueprints intelligence_*, JWT mockado."""
    from flask import Flask
    from flask_jwt_extended import JWTManager

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret-sprint-4-1"
    flask_app.config["CLINICAL_EVENT_STORE"] = event_store
    flask_app.config["INTELLIGENCE_EXPLANATION_REGISTRY"] = explanation_registry

    JWTManager(flask_app)

    from routes.intelligence_timeline import intelligence_timeline_bp
    from routes.explainability import explainability_bp
    flask_app.register_blueprint(intelligence_timeline_bp)
    flask_app.register_blueprint(explainability_bp)

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(app) -> Dict[str, str]:
    """JWT + tenant headers para chamadas autenticadas.

    Gera token DENTRO do contexto da app de teste (mesmo JWT_SECRET_KEY),
    evitando mismatch de assinatura quando o test_client valida o token.
    """
    return _make_auth_headers(app)


def _make_auth_headers(app, user_id: str = "test-user",
                      tenant_id: str = "test-tenant") -> Dict[str, str]:
    """Gera JWT (string identity) + X-Tenant-ID.

    flask-jwt-extended ≥4.7 exige identity string. Tenant é propagado via
    header X-Tenant-ID (que _resolve_tenant_id() checa primeiro).
    """
    from flask_jwt_extended import create_access_token

    with app.app_context():
        token = create_access_token(
            identity=user_id,
            additional_claims={
                "tenant_id": tenant_id,
                "organization_id": tenant_id,
            },
        )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id,
    }


@pytest.fixture
def auth_headers(app) -> Dict[str, str]:
    return _make_auth_headers(app)


@pytest.fixture
def auth_headers_other_tenant(app) -> Dict[str, str]:
    """Headers para um tenant diferente — usado em testes de tenant isolation."""
    return _make_auth_headers(
        app, user_id="other-user", tenant_id="other-tenant",
    )


@pytest.fixture
def publisher_app(app, event_store):
    """Publisher configurado dentro do app_context (compat)."""
    return ClinicalEventPublisher(store=event_store, validate_payload=False)