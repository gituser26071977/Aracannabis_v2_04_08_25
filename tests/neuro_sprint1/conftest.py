"""Conftest para tests/neuro_sprint1/.

Os testes de rota (test_routes_neuro_scales.py) usam Flask `db.session`
(uma `LocalProxy`) que exige `app.app_context()` para funcionar.

Este conftest nao altera a fixture `app` definida nos testes; ele expoe
um contexto de aplicacao (via `with app.app_context()`) que o pytest
utiliza automaticamente para instanciar a fixture `app` quando ha
`yield` em outro fixture.

Como os testes de rota definem `app` como `@pytest.fixture` (nao
`@pytest.fixture(autouse=True)`), a abordagem correta e garantir
que cada test_request use um app_context. Isso e feito via
`pytest.fixture(autouse=True)` que descobre a fixture `app` e ativa
o context durante o test.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _app_context(request):
    """Ativa app_context() automaticamente quando a fixture `app` existir.

    Tests que definem apenas fixtures domain (sem Flask) ignoram este
    fixture transparentemente.
    """
    if "app" not in request.fixturenames:
        yield
        return

    app = request.getfixturevalue("app")
    with app.app_context():
        yield
