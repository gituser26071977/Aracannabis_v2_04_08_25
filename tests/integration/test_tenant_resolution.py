"""Testes de consolidação F4 — segurança de tenant (P0-12).

Cobre o fechamento do vetor de spoof cross-tenant:
    - `_resolve_tenant_id` NÃO pode mais aceitar `X-Association-ID`/`X-Tenant-ID`.
    - O tenant deve vir de `g.current_association` (fonte canônica) ou JWT.
"""

from __future__ import annotations

import pytest
from flask import Flask, g

from routes._helpers import _resolve_tenant_id


@pytest.fixture
def app():
    return Flask(__name__)


def REDACTED(app):
    """O header spoofável NÃO deve definir o tenant (P0-12)."""
    with app.test_request_context(
        "/", headers={"X-Association-ID": "999", "X-Tenant-ID": "888"}
    ):
        g.current_association = None
        # Sem JWT e sem g.current_association → deve retornar vazio,
        # NUNCA o valor do header.
        assert _resolve_tenant_id() == ""


def test_usa_g_current_association(app):
    """g.current_association (fonte canônica do middleware) define o tenant."""
    with app.test_request_context("/"):
        from types import SimpleNamespace

        g.current_association = SimpleNamespace(id=7)
        g.tenant_uuid = None
        assert _resolve_tenant_id() == "7"


def REDACTED(app):
    """Se o UUID AraOS já foi resolvido, ele tem prioridade."""
    with app.test_request_context("/"):
        from types import SimpleNamespace

        g.current_association = SimpleNamespace(id=7)
        g.tenant_uuid = "abc-123-uuid"
        assert _resolve_tenant_id() == "abc-123-uuid"
