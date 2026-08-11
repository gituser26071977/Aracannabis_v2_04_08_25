"""Testes do endpoint de replay histórico (F2 retrofit).

Valida que `POST /api/replay/historical` exige autenticação e retorna o
resultado do replay para admin.
"""

from __future__ import annotations

import unittest

from config import TestingConfig
from app_cors_livre import create_app
from models import db


class TestHistoricalReplayEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_replay_requires_auth(self):
        resp = self.client.post("/api/replay/historical", json={})
        assert resp.status_code in (401, 403)

    def test_replay_returns_result_shape(self):
        # Autentica como admin (senha conhecida criada no setup)
        from models import Profissional
        from werkzeug.security import generate_password_hash

        with self.app.app_context():
            admin = Profissional(
                nome="Admin Replay",
                usuario="admin.replay",
                senha=generate_password_hash("Admin@123456"),
                role="admin",
                status_cadastro="aprovado",
            )
            db.session.add(admin)
            db.session.commit()

        # login
        login = self.client.post(
            "/api/auth/login",
            json={"usuario": "admin.replay", "senha": "Admin@123456"},
        )
        assert login.status_code == 200, login.data
        token = login.get_json()["access_token"]

        # replay (sem dados históricos → total 0)
        resp = self.client.post(
            "/api/replay/historical",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.data
        body = resp.get_json()
        assert "total" in body
        assert "emitted" in body
        assert "failed" in body


if __name__ == "__main__":
    unittest.main()
