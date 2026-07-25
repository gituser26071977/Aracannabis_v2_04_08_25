"""Shared fixtures for Knowledge API (REST) tests — Sprint 4.5 RC1 Gate 2.

This conftest builds a thin Flask app + JWT + knowledge_bp registered,
with a tenant_id-aware `g.current_association` injected via JWT custom
claims. SQLite file-based engine (compatible with the existing
SQLKnowledgeRepository tests).

Pattern reuses the structure of ``tests/intel_sprint_4_2/conftest.py``.

Three things to remember:
- All API responses use the standard envelope (success / data / error / meta).
- ``g.tenant_id`` is populated by ``@tenant_required``.
- Cross-tenant access MUST return 404 (not 403).
"""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

import pytest
from flask import Flask, g
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

# ─────────────────────────────────────────────────────────────────────
# Inject a fake ``routes.auth_decorators`` BEFORE any imports happen.
# The real module imports ``models`` (Profissional, Paciente, ...) which
# triggers SQLAlchemy mapper configuration referencing tables that are
# not present in our test SQL engine. The fake module exposes ONLY
# ``require_permission`` as a transparent pass-through, sufficient for
# REST-shape tests (RBAC depth is covered by dedicated platform tests).
# ─────────────────────────────────────────────────────────────────────
import types
_fake_ad = types.ModuleType("routes.auth_decorators")
from functools import wraps as _wraps

def _noop_require_permission(*perms):
    def decorator(f):
        @_wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator

_fake_ad.require_permission = _noop_require_permission
_fake_ad.require_staff_role = lambda *roles: _noop_require_permission()
sys.modules["routes.auth_decorators"] = _fake_ad

# Re-import conftest from Sprint 4.4 (sane tenant + scenario fixtures).
sys.path.insert(0, str(_HERE.parent / "sprint_4_4"))
from tests.sprint_4_4.conftest import (  # noqa: E402,F401
    scenario_alfa,
    scenario_beta,
    window,
    tenant_a,
    tenant_b,
    patient_a1,
    patient_a2,
    patient_b1,
)


# Reuse the SQLAlchemy ``Base`` for the knowledge tables.
# Importing the SQL models ensures they register with ``Base.metadata``
# BEFORE ``create_all`` runs — otherwise only the tenant tables are
# created and clinical_* tables are missing.
from araos.platform.tenant.models import Base  # noqa: E402
from araos.clinical.knowledge.infrastructure import (  # noqa: E402,F401
    sql as _knowledge_sql,  # registers ClinicalGeneModel, ClinicalGenomeModel, etc.
)


# ─────────────────────────────────────────────────────────────────────
# Engine + session_factory
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def engine(tmp_path):
    """File-based SQLite + StaticPool (knowledge persistence pattern)."""
    db_path = tmp_path / "knowledge_rest_test.db"
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
    """Callable that returns a fresh Session bound to ``engine``."""
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return Session


# ─────────────────────────────────────────────────────────────────────
# Flask app + JWT + blueprint registration
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def app(session_factory, monkeypatch):
    """Thin Flask app — no global middleware, just knowledge_bp + JWT."""
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["JWT_SECRET_KEY"] = "test-secret-rc1-gate-2"
    flask_app.config["REDACTED"] = session_factory
    JWTManager(flask_app)

    # The platform's @require_permission is a no-op for these REST-shape
    # tests (RBAC depth is exercised by dedicated platform tests). The
    # no-op decorator was injected via sys.modules above.

    # Swap knowledge_composition to use the InMemory repository for
    # these tests. The SQL repo has a pre-existing trajectory
    # round-trip bug (Foundation Freeze — not modified here) that
    # breaks pipeline tests. The REST contract is identical regardless
    # of which repo backs it; InMemory is sufficient for shape tests.
    from araos.clinical.knowledge.application import composition as _comp
    from araos.clinical.knowledge.infrastructure.in_memory import (
        InMemoryKnowledgeRepository,
    )
    from contextlib import contextmanager

    # Module-level singleton store keyed by tenant_id, shared between
    # the seeded fixtures and the request handler.
    _shared_repos: dict[str, InMemoryKnowledgeRepository] = {}

    def _get_repo(tenant_id: str) -> InMemoryKnowledgeRepository:
        if tenant_id not in _shared_repos:
            _shared_repos[tenant_id] = InMemoryKnowledgeRepository(tenant_id)
        return _shared_repos[tenant_id]

    @contextmanager
    def _inmem_composition(_session_factory_unused, tenant_id: str):
        repo = _get_repo(tenant_id)
        try:
            yield repo
        finally:
            pass  # nothing to commit/close in memory

    # Expose _get_repo on the conftest module for fixtures to import.
    monkeypatch.setattr(_comp, "knowledge_composition", _inmem_composition)
    import interfaces.rest.v1.knowledge as _knowledge_mod
    monkeypatch.setattr(_knowledge_mod, "knowledge_composition", _inmem_composition)
    # Stash _get_repo on the app for test fixtures.
    flask_app._get_repo = _get_repo

    # Inject tenant middleware simulation:
    @flask_app.before_request
    def _resolve_tenant_from_jwt():
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        try:
            verify_jwt_in_request(optional=True)
        except Exception:
            return None
        identity = get_jwt_identity()
        if identity is None:
            return None
        # JWT additional_claims carry tenant_id; build a stub association.
        from flask_jwt_extended import get_jwt
        claims = get_jwt() or {}
        tenant_raw = claims.get("tenant_id")
        if tenant_raw is None:
            # Try legacy scalar/object identity
            tenant_raw = claims.get("organization_id") or claims.get("tenant")
        if tenant_raw is None and isinstance(identity, str) and ":" in identity:
            # Support "tenant_x:user_y" dev tokens
            tenant_raw = identity.split(":", 1)[0]
        if tenant_raw is None:
            return None
        # Stub association — read-only mapping for `id`
        class _Assoc:
            def __init__(self, tid):
                self.id = tid

        g.current_association = _Assoc(tenant_raw)
        g.user_id = identity
        return None

    # Register knowledge blueprint
    from interfaces.rest.v1 import knowledge_bp
    flask_app.register_blueprint(knowledge_bp)

    # Register knowledge observability hooks
    from interfaces.rest.v1.observability import register_request_hooks
    register_request_hooks(flask_app)

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ─────────────────────────────────────────────────────────────────────
# Auth headers
# ─────────────────────────────────────────────────────────────────────

def _make_auth_headers(app, user_id, tenant_id: str) -> dict:
    """Build a JWT Authorization header for the test app.

    The platform's ``@require_permission`` decorator (used by
    ``routes/auth_decorators.py``) calls ``int(identity)`` to look up
    the Profissional by primary key. Numeric identities are required.
    The ``superadmin`` identity (99) is in ``_ROLE_BYPASS`` and skips
    the Profissional DB lookup, returning the handler immediately.
    """
    with app.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims={"tenant_id": tenant_id, "organization_id": tenant_id},
        )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id}


@pytest.fixture
def auth_headers_alfa(app):
    # Identity "1" must exist as Profissional OR the @require_permission
    # decorator returns 404. We patch this in the app fixture via
    # monkeypatch of _get_profissional_and_subscription — see app fixture.
    return _make_auth_headers(app, 1, "tenant_alfa")


@pytest.fixture
def auth_headers_beta(app):
    return _make_auth_headers(app, 2, "tenant_beta")


@pytest.fixture
def auth_headers_superadmin(app):
    # superadmin role bypasses RBAC — Profesional.query.get(99) is allowed
    # to return None because role check happens before profissional.role access.
    return _make_auth_headers(app, 99, "tenant_alfa")


# ─────────────────────────────────────────────────────────────────────
# Population: pre-seed the tenant with a genome via the pipeline
# ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def populated_alfa(app, session_factory, scenario_alfa):
    """Save scenario_alfa's genes + a derived genome via the SHARED
    InMemory repository (same instance the request handler uses)."""
    from araos.clinical.knowledge.application.knowledge_service import (
        KnowledgeService,
    )

    repo = app._get_repo("tenant_alfa")
    repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
    genome = KnowledgeService().build_genome_from_genes(
        tenant_id="tenant_alfa",
        patient_id=scenario_alfa.patient_id,
        window=scenario_alfa.window,
        genes=scenario_alfa.genes,
    )
    repo.save_genome(genome)
    genome_id = str(genome.genome_id)
    return {"patient_id": scenario_alfa.patient_id, "genome_id": genome_id}


@pytest.fixture
def populated_beta(app, session_factory, scenario_beta):
    from araos.clinical.knowledge.application.knowledge_service import (
        KnowledgeService,
    )

    repo = app._get_repo("tenant_beta")
    repo.save_genes(scenario_beta.patient_id, scenario_beta.genes)
    genome = KnowledgeService().build_genome_from_genes(
        tenant_id="tenant_beta",
        patient_id=scenario_beta.patient_id,
        window=scenario_beta.window,
        genes=scenario_beta.genes,
    )
    repo.save_genome(genome)
    genome_id = str(genome.genome_id)
    return {"patient_id": scenario_beta.patient_id, "genome_id": genome_id}
