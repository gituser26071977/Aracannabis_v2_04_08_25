"""Testes da listagem de conselhos (profissionais de saúde agnósticos).

Valida que o sistema suporta múltiplas classes profissionais: médico,
psicólogo, enfermeiro, nutricionista, fisioterapeuta, fonoaudiólogo.
"""

from __future__ import annotations

import pytest

from config import TestingConfig
from app_cors_livre import create_app


@pytest.fixture
def client():
    app = create_app(TestingConfig)
    return app.test_client()


class TestListarConselhos:
    def test_endpoint_publico(self, client):
        r = client.get("/api/cadastro_profissionais/conselhos")
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["success"] is True
        conselhos = {c["tipo"]: c for c in body["conselhos"]}

        # Profissões de saúde suportadas
        assert conselhos["CRM"]["profissao"] == "Médico"
        assert conselhos["CRP"]["profissao"] == "Psicólogo"
        assert conselhos["COREN"]["profissao"] == "Enfermeiro"
        assert conselhos["CRN"]["profissao"] == "Nutricionista"
        assert conselhos["CREFITO"]["profissao"] == "Fisioterapeuta"
        assert conselhos["CRFa"]["profissao"] == "Fonoaudiólogo"

    def test_todos_sao_profissional(self, client):
        r = client.get("/api/cadastro_profissionais/conselhos")
        conselhos = r.get_json()["conselhos"]
        for c in conselhos:
            if c["tipo"] != "NONE":
                assert c["role"] == "profissional", c["tipo"]


class TestValidarConselhos:
    def test_crfa_fono(self):
        from services.conselho_validator import validar_conselho

        r = validar_conselho("12345", "SE", "CRFa")
        assert r["valido"] is True
        assert r["profissao"] == "Fonoaudiólogo"

    def test_crp_psicologo(self):
        from services.conselho_validator import validar_conselho

        r = validar_conselho("12/34567", "SP", "CRP")
        assert r["valido"] is True
        assert r["profissao"] == "Psicólogo"

    def test_coren_enfermeiro(self):
        from services.conselho_validator import validar_conselho

        r = validar_conselho("SP123456", "SP", "COREN")
        assert r["valido"] is True
        assert r["profissao"] == "Enfermeiro"
