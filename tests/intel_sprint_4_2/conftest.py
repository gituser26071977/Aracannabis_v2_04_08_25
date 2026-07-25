"""
conftest.py — fixtures Sprint 4.2 (Clinical Context Engine).

Reuso padrão Sprint 4.1 (tests/intel_sprint_4_1/conftest.py):
    - sys.path injection
    - SQLite in-memory
    - InMemoryClinicalEventStore + ClinicalEventPublisher
    - session_factory
    - JWT mock via string identity + X-Tenant-ID header
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


# ─── Engine + session_factory (Sprint 4.2 tables) ─────────────────


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    from araos.clinical.context.sql import (
        ClinicalContextModel,
        ContextRelationshipModel,
        ProcessedRuleEvaluationModel,
    )
    ClinicalContextModel.metadata.create_all(eng)
    ContextRelationshipModel.metadata.create_all(eng)
    ProcessedRuleEvaluationModel.metadata.create_all(eng)

    # processed_events (Sprint 3.1) para idempotência de projections
    from sqlalchemy import text
    with eng.connect() as conn:
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS processed_events ("
            "id VARCHAR(64) PRIMARY KEY,"
            "tenant_id VARCHAR(36) NOT NULL,"
            "sequence BIGINT NOT NULL,"
            "event_id VARCHAR(64),"
            "event_type VARCHAR(64),"
            "source_module VARCHAR(64),"
            "processed_at DATETIME"
            ")"
        ))
        # active projection table
        conn.execute(text(
            "CREATE TABLE IF NOT EXISTS clinical_contexts_active ("
            "context_id VARCHAR(64) PRIMARY KEY,"
            "tenant_id VARCHAR(36) NOT NULL,"
            "patient_id VARCHAR(64) NOT NULL,"
            "context_type VARCHAR(48),"
            "status VARCHAR(24),"
            "origin VARCHAR(24),"
            "title VARCHAR(255),"
            "start_date DATETIME,"
            "end_date DATETIME,"
            "confidence_score FLOAT,"
            "suggestion_id VARCHAR(64),"
            "updated_at DATETIME"
            ")"
        ))
        conn.commit()
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False)


# ─── Event Store + Publisher ──────────────────────────────────────


@pytest.fixture
def event_store():
    from araos.clinical.event_store import InMemoryClinicalEventStore
    return InMemoryClinicalEventStore()


@pytest.fixture
def publisher(event_store):
    from araos.clinical.event_store import ClinicalEventPublisher
    return ClinicalEventPublisher(store=event_store, validate_payload=False)


# ─── Domain / Application fixtures ────────────────────────────────


@pytest.fixture
def ctx_service(publisher):
    from araos.clinical.context.application import ClinicalContextService
    return ClinicalContextService(event_publisher=publisher)


@pytest.fixture
def rule_engine():
    from araos.clinical.context.application import RuleEngine
    return RuleEngine()


@pytest.fixture
def inmem_query():
    from araos.clinical.context.application import InMemoryClinicalContextQuery
    return InMemoryClinicalContextQuery()


@pytest.fixture
def suggestion_registry():
    from araos.clinical.explainability import InMemoryExplanationRegistry
    return InMemoryExplanationRegistry()


@pytest.fixture
def suggester(rule_engine, suggestion_registry, publisher):
    from araos.clinical.context.application import ContextSuggester
    return ContextSuggester(
        rule_engine=rule_engine,
        explanation_registry=suggestion_registry,
        event_publisher=publisher,
    )


# ─── SQL fixtures ─────────────────────────────────────────────────


@pytest.fixture
def context_repo(session_factory):
    from araos.clinical.context.sql import REDACTED
    return REDACTED(session_factory=session_factory)


@pytest.fixture
def relationship_repo(session_factory):
    from araos.clinical.context.sql import REDACTED
    return REDACTED(session_factory=session_factory)


@pytest.fixture
def sql_query(session_factory):
    from araos.clinical.context.sql import SqlAlchemyClinicalContextQuery
    return SqlAlchemyClinicalContextQuery(session_factory=session_factory)


# ─── Flask app fixture ────────────────────────────────────────────


@pytest.fixture
def app(event_store, suggestion_registry, session_factory, publisher):
    """Flask app minimal com blueprint clinical_context."""
    from flask import Flask
    from flask_jwt_extended import JWTManager

    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret-sprint-4-2"
    flask_app.config["CLINICAL_EVENT_STORE"] = event_store
    flask_app.config["REDACTED"] = session_factory
    flask_app.config["INTELLIGENCE_CONTEXT_PUBLISHER"] = publisher
    flask_app.config["INTELLIGENCE_EXPLANATION_REGISTRY"] = (
        suggestion_registry
    )

    JWTManager(flask_app)

    from routes.clinical_context import clinical_context_bp
    flask_app.register_blueprint(clinical_context_bp)

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def _make_auth_headers(
    app, user_id: str = "test-user", tenant_id: str = "test-tenant",
) -> Dict[str, str]:
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
def auth_headers(app):
    return _make_auth_headers(app)


@pytest.fixture
def auth_headers_other_tenant(app):
    return _make_auth_headers(
        app, user_id="other-user", tenant_id="other-tenant",
    )
