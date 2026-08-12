"""Testes do fluxo de dispensa de farmácia (prescrição → estoque).

Reescrito como teste de integração com Flask test client (em memória).
Originalmente era E2E (requests HTTP para localhost:5000) e falhava por
conectar a um servidor que não existe na suíte. Também revelou que os
blueprints `inventory_bp` e `pharmacy_bp` não estavam registrados no app.

Cobre:
    - criar produto (POST /api/produtos)
    - criar item de estoque (POST /api/inventory/)
    - dispensar (POST /api/pharmacy/dispense) e confirmar que o estoque
      diminuiu de 5 para 2
    - estoque insuficiente → 400 (sem dispensar)
"""

from __future__ import annotations

import pytest
import time

from config import TestingConfig
from app_cors_livre import create_app
from models import db, Profissional
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    a = create_app(TestingConfig)
    with a.app_context():
        db.create_all()
    yield a
    with a.app_context():
        db.session.remove()
        db.drop_all()


def _profissional(usuario="admin.dispensa"):
    return Profissional(
        nome=f"Prof {usuario}",
        usuario=usuario,
        email=f"{usuario}@teste.com",
        crm=f"CRM-{usuario.upper()[:4]}",
        uf_crm="SE",
        senha=generate_password_hash("Teste@123456"),
        role="admin",
        perfil_acesso="administrativo",
        status_cadastro="aprovado",
    )


def _criar_associacao_e_admin():
    from association.models import Associacao
    from models_extra import UsuarioAssociacao

    a = Associacao(
        nome="Clinica Dispensa",
        slug="clinica-dispensa",
        cnpj=f"CNPJ-{int(time.time())}",
        ativo=True,
    )
    db.session.add(a)
    db.session.flush()
    p = _profissional()
    db.session.add(p)
    db.session.flush()
    db.session.add(UsuarioAssociacao(
        profissional_id=p.id,
        associacao_id=a.id,
        role="admin",
        status="active",
    ))
    db.session.commit()
    return a.id


def _login(client, usuario="admin.dispensa"):
    r = client.post("/api/auth/login", json={"usuario": usuario, "senha": "Teste@123456"})
    assert r.status_code == 200, r.data
    return {"Authorization": f"Bearer {r.get_json()['access_token']}"}


def _criar_produto(client, headers):
    payload = {
        "nome": f"Test Product {int(time.time())}",
        "tipo": "oleo",
        "concentracao_cbd": 0,
        "concentracao_thc": 0,
        "gotas_por_ml": 30,
        "volume_ml": 30,
    }
    r = client.post("/api/produtos", json=payload, headers=headers)
    assert r.status_code == 201, r.data
    return r.get_json()["produto"]["id"]


def test_prescription_to_dispense_flow(app):
    client = app.test_client()
    with app.app_context():
        _criar_associacao_e_admin()

    headers = _login(client)

    # criar produto
    produto_id = _criar_produto(client, headers)
    assert produto_id

    # criar item de estoque com 5 unidades
    payload = {
        "produto_id": produto_id,
        "quantidade": 5,
        "lote": f"L-{int(time.time())}",
        "localizacao": "Test Depot",
        "validade": None,
    }
    r = client.post("/api/inventory/", json=payload, headers=headers)
    assert r.status_code == 201, r.data
    inv_id = r.get_json()["inventory_item"]["id"]
    assert inv_id

    # dispensar 3 unidades
    dispense_payload = {
        "prescricao_id": None,
        "itens": [{"produto_id": produto_id, "quantidade": 3}],
        "observacoes": "Teste integração",
    }
    r = client.post("/api/pharmacy/dispense", json=dispense_payload, headers=headers)
    assert r.status_code == 201, r.data
    resp = r.get_json()
    assert "pharmacy_dispense" in resp, f"Unexpected response: {resp}"

    # verificar que o estoque diminuiu para 2
    r = client.get("/api/inventory/", headers=headers)
    assert r.status_code == 200, r.data
    items = r.get_json()
    found = False
    for it in items:
        if it.get("produto_id") == produto_id:
            assert it.get("quantidade") == 2, f"Esperado 2, veio {it.get('quantidade')}"
            found = True
    assert found, "Updated inventory item not found"


def REDACTED(app):
    client = app.test_client()
    with app.app_context():
        _criar_associacao_e_admin()

    headers = _login(client)
    produto_id = _criar_produto(client, headers)

    # estoque com 1 unidade
    r = client.post("/api/inventory/", json={
        "produto_id": produto_id,
        "quantidade": 1,
        "lote": "L-1",
        "localizacao": "Test Depot",
        "validade": None,
    }, headers=headers)
    assert r.status_code == 201, r.data

    # tentar dispensar 5 → deve falhar com 400
    r = client.post("/api/pharmacy/dispense", json={
        "prescricao_id": None,
        "itens": [{"produto_id": produto_id, "quantidade": 5}],
        "observacoes": "sem estoque",
    }, headers=headers)
    assert r.status_code == 400, r.data
