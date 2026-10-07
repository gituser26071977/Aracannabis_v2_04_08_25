"""Fixtures para os testes de rota da triagem psiquiátrica."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from araos.platform.tenant.models import Base
from araos.specialties.neurodevelopmental.db_models import NeuroScaleResponseModel  # noqa: F401


@pytest.fixture
def app():
    application = Flask(__name__)
    application.config["TESTING"] = True
    application.config["JWT_SECRET_KEY"] = "test-secret-key"
    application.config["JWT_VERIFY_SUB"] = False
    JWTManager(application)

    engine = create_engine(
        "sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    fake_models = types.ModuleType("models")
    fake_models.db = MagicMock()
    fake_models.db.session = session
    sys.modules["models"] = fake_models

    from routes.psychiatry import psychiatry_triage_bp
    from routes.psych_triage_public import psych_triage_public_bp

    application.register_blueprint(psychiatry_triage_bp)
    application.register_blueprint(psych_triage_public_bp)

    yield application

    session.close()
    engine.dispose()
    sys.modules.pop("models", None)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_header(app):
    token = create_access_token(identity={"user_id": "actor-1", "tenant_id": "tenant-1"})
    return {"Authorization": f"Bearer {token}"}
