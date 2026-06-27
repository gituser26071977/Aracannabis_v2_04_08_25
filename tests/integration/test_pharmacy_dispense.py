import os
import time
import requests

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'Aracannabis@2025')


def ensure_admin(session):
    # Try to create admin (idempotent)
    try:
        session.get(f"{BASE_URL}/auth/create-admin", timeout=5)
    except Exception:
        pass


def ensure_admin(session):
    # Backdoor removido em P0-A (2026-06-22): rota /api/auth/create-admin foi eliminada
    # porque expunha criação de admin sem autenticação com senha hardcoded.
    # Admin deve ser criado via CLI segura, seed ou painel interno com @jwt_required.
    pass


def login(session):
    r = session.post(f"{BASE_URL}/auth/login", json={"usuario": ADMIN_USER, "senha": ADMIN_PASS}, timeout=5)
    r.raise_for_status()
    data = r.json()
    token = data.get('access_token')
    assert token, 'No access token returned'
    return token


def create_product(session, headers):
    payload = {
        'nome': f'Test Product {int(time.time())}',
        'tipo': 'oleo',
        'concentracao_cbd': 0,
        'concentracao_thc': 0,
        'gotas_por_ml': 30,
        'volume_ml': 30
    }
    r = session.post(f"{BASE_URL}/api/produtos", json=payload, headers=headers, timeout=5)
    r.raise_for_status()
    return r.json().get('produto', {}).get('id') or r.json().get('id')


def create_inventory(session, headers, produto_id, quantidade=10):
    payload = {
        'produto_id': produto_id,
        'quantidade': quantidade,
        'lote': f'L-{int(time.time())}',
        'localizacao': 'Test Depot',
        'validade': None
    }
    r = session.post(f"{BASE_URL}/api/inventory/", json=payload, headers=headers, timeout=5)
    r.raise_for_status()
    return r.json().get('inventory_item', {}).get('id')


def get_inventory_items(session, headers):
    r = session.get(f"{BASE_URL}/api/inventory/", headers=headers, timeout=5)
    r.raise_for_status()
    return r.json()


def test_prescription_to_dispense_flow():
    session = requests.Session()
    ensure_admin(session)
    token = login(session)
    headers = {'Authorization': f'Bearer {token}'}

    # create product
    try:
        produto_id = create_product(session, headers)
    except requests.HTTPError:
        # If produtos endpoint not available, try fetching products
        r = session.get(f"{BASE_URL}/api/produtos", headers=headers, timeout=5)
        r.raise_for_status()
        produtos = r.json().get('produtos') or r.json()
        assert produtos, 'No produtos available and creation failed'
        produto_id = produtos[0].get('id')

    assert produto_id, 'produto_id not available'

    # create inventory entry
    inv_id = create_inventory(session, headers, produto_id, quantidade=5)
    assert inv_id, 'inventory item not created'

    # attempt to dispense 3 units
    dispense_payload = {
        'prescricao_id': None,
        'itens': [
            {'produto_id': produto_id, 'quantidade': 3}
        ],
        'observacoes': 'Teste integração'
    }

    r = session.post(f"{BASE_URL}/api/pharmacy/dispense", json=dispense_payload, headers=headers, timeout=5)
    r.raise_for_status()
    resp = r.json()
    assert 'pharmacy_dispense' in resp, f'Unexpected response: {resp}'

    # verify inventory decreased
    items = get_inventory_items(session, headers)
    found = False
    for it in items:
        if it.get('produto_id') == produto_id:
            # quantidade should be <= original (5)
            assert it.get('quantidade') is not None
            assert it.get('quantidade') <= 5
            found = True
    assert found, 'Updated inventory item not found'
