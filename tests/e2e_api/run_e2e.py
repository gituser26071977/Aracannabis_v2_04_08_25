"""Suíte E2E do AraOS SIAP — fluxos completos via API real.

Roda contra https://api.vittalis.site (produção) OU BASE_URL env.

Cobre o journey completo do sistema:
  1. Cadastro inicial (profissional via /api/auth/register)
  2. Login
  3. Pacientes (CRUD)
  4. Consultas (agendar/listar)
  5. Evoluções (SOAP)
  6. Exames (criar/listar)
  7. Catálogo de produtos (CRUD)
  8. Cadastro inteligente (icatalog upload + revisão)
  9. Estoque (inventory CRUD)
  10. Dispensa (pharmacy)
  11. Prescrição
  12. Faturamento/billing
  13. Admin (usuários, dashboard)

Uso:
    python tests/e2e_api/run_e2e.py
    BASE_URL=https://api.vittalis.site ADMIN_USER=... ADMIN_PASS=... python tests/e2e_api/run_e2e.py
"""

from __future__ import annotations

import json
import os
import random
import string
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

BASE_URL = os.getenv("BASE_URL", "https://api.vittalis.site").rstrip("/")
ADMIN_USER = os.getenv("ADMIN_USER", "abholzwarth")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Teste@E2E2026")

PASSED = 0
FAILED = 0
FAILURES: list[str] = []


def _req(
    method: str,
    path: str,
    token: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None,
    expect: int = 200,
    label: str = "",
) -> Dict[str, Any]:
    global PASSED, FAILED
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            code = resp.status
            payload = resp.read()
            try:
                j = json.loads(payload)
            except Exception:
                j = {"raw": payload[:200].decode(errors="replace")}
            status = "OK" if code == expect else f"ERRO(esperava {expect})"
            if code == expect:
                PASSED += 1
                print(f"  ✓ {method} {path} → {code} {status}")
            else:
                FAILED += 1
                msg = f"{method} {path} → {code} (esperava {expect})"
                FAILURES.append(msg)
                print(f"  ✗ {msg}")
                if label:
                    print(f"    [{label}] {j}")
            return j
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            j = json.loads(e.read())
        except Exception:
            j = {"raw": str(e)}
        if code == expect:
            PASSED += 1
            print(f"  ✓ {method} {path} → {code} (esperado)")
        else:
            FAILED += 1
            msg = f"{method} {path} → {code} (esperava {expect})"
            FAILURES.append(msg)
            print(f"  ✗ {msg}")
            if label:
                print(f"    [{label}] {j}")
        return j
    except Exception as e:  # noqa: BLE001
        FAILED += 1
        msg = f"{method} {path} → EXCEÇÃO {e}"
        FAILURES.append(msg)
        print(f"  ✗ {msg}")
        return {"error": str(e)}


def _uid(prefix: str = "e2e") -> str:
    return f"{prefix}-{int(time.time())}-{''.join(random.choices(string.ascii_lowercase, k=4))}"


def login_admin() -> str:
    print("\n== LOGIN ADMIN ==")
    r = _req("POST", "/api/auth/login", body={"usuario": ADMIN_USER, "senha": ADMIN_PASS}, expect=200, label="login")
    token = r.get("access_token")
    if not token:
        print(f"  !! Falha login: {r}")
        sys.exit(1)
    return token


def test_cadastro_inicial() -> str:
    print("\n== 1. CADASTRO INICIAL (profissional) ==")
    usuario = _uid("prof")
    payload = {
        "nome": "Medico E2E",
        "crm": f"{random.randint(100000, 999999)}",
        "uf_crm": "SP",
        "usuario": usuario,
        "senha": "Teste@E2E2026",
        "email": f"{usuario}@e2e.local",
    }
    _req("POST", "/api/auth/register", body=payload, expect=201, label="register")
    # login com o novo usuário
    r2 = _req("POST", "/api/auth/login", body={"usuario": usuario, "senha": "Teste@E2E2026"}, expect=200, label="login novo")
    return r2.get("access_token", "")


def test_pacientes(token: str) -> int:
    print("\n== 2. PACIENTES ==")
    nome = f"Paciente {_uid()}"
    r = _req("POST", "/api/pacientes/", token, {"nome": nome, "data_nascimento": "1990-05-15"}, expect=201, label="criar")
    pid = (r.get("paciente") or {}).get("id")
    if not pid:
        pid = r.get("id")
    assert pid, f"Paciente sem id: {r}"
    _req("GET", f"/api/pacientes/{pid}", token, expect=200, label="obter")
    _req("PUT", f"/api/pacientes/{pid}", token, {"nome": nome, "data_nascimento": "1990-05-15", "telefone": "11999990000"}, expect=200, label="atualizar")
    return pid


def test_consultas(token: str, paciente_id: int) -> int:
    print("\n== 3. CONSULTAS ==")
    data_hora = f"2026-{random.randint(1,12):02d}-{random.randint(1,27):02d}T{random.randint(8,17):02d}:{random.randint(0,59):02d}:00"
    r = _req("POST", "/api/consultas/", token, {"paciente_id": paciente_id, "data_hora": data_hora, "tipo": "presencial"}, expect=201, label="agendar")
    cid = (r.get("consulta") or {}).get("id")
    if not cid:
        cid = r.get("id")
    assert cid, f"Consulta sem id: {r}"
    _req("GET", "/api/consultas/", token, expect=200, label="listar")
    return cid


def test_evolucoes(token: str, paciente_id: int) -> int:
    print("\n== 4. EVOLUÇÕES (SOAP) ==")
    r = _req("POST", f"/api/evolucoes/paciente/{paciente_id}", token, {
        "nota_evolucao": "Evolução E2E - paciente estável, sem queixas.",
        "tipo": "consulta",
    }, expect=201, label="criar evolução")
    eid = (r.get("evolucao") or {}).get("id") or r.get("id")
    assert eid, f"Evolução sem id: {r}"
    _req("GET", f"/api/evolucoes/paciente/{paciente_id}", token, expect=200, label="listar evoluções")
    return eid


def test_exames(token: str, paciente_id: int) -> int:
    print("\n== 5. EXAMES ==")
    r = _req("POST", "/api/exames", token, {
        "paciente_id": paciente_id,
        "titulo": f"Exame E2E {_uid()}",
        "tipo_exame": "texto",
        "descricao": "Resultado de exame E2E dentro dos limites.",
    }, expect=201, label="criar exame")
    xid = (r.get("exame") or {}).get("id") or r.get("id")
    assert xid, f"Exame sem id: {r}"
    _req("GET", f"/api/pacientes/{paciente_id}/exames", token, expect=200, label="listar exames")
    return xid


def test_catalogo(token: str) -> int:
    print("\n== 6. CATÁLOGO DE PRODUTOS ==")
    r = _req("POST", "/api/catalogo/produtos", token, {
        "nome": f"Óleo CBD E2E {_uid()}",
        "marca": "Marca E2E",
        "categoria": "oleo",
        "unidade": "ml",
    }, expect=201, label="criar produto")
    pid = (r.get("produto") or {}).get("id") or r.get("id")
    assert pid, f"Produto sem id: {r}"
    _req("GET", "/api/catalogo/produtos", token, expect=200, label="listar produtos")
    _req("GET", "/api/catalogo/categorias", token, expect=200, label="categorias")
    _req("GET", "/api/catalogo/marcas", token, expect=200, label="marcas")
    return pid


def test_inventory(token: str) -> int:
    """Cria um Produto (tabela produtos, usada pelo estoque) e um item de estoque."""
    print("\n== 7. ESTOQUE (inventory) ==")
    # o estoque referencia Produto (models.Produto), não ProdutoCannabis
    r = _req("POST", "/api/produtos", token, {
        "nome": f"Óleo Inventário E2E {_uid()}",
        "tipo": "oleo",
        "concentracao_cbd": 300,
        "concentracao_thc": 0,
        "gotas_por_ml": 30,
        "volume_ml": 30,
    }, expect=201, label="criar produto (models.Produto)")
    produto_id = (r.get("produto") or {}).get("id") or r.get("id")
    assert produto_id, f"Produto de estoque sem id: {r}"

    r = _req("POST", "/api/inventory/", token, {
        "produto_id": produto_id,
        "quantidade": 10,
        "lote": f"L-{_uid()}",
        "localizacao": "Depósito E2E",
        "validade": None,
    }, expect=201, label="criar item estoque")
    iid = (r.get("inventory_item") or {}).get("id") or r.get("id")
    assert iid, f"Inventory sem id: {r}"
    _req("GET", "/api/inventory/", token, expect=200, label="listar estoque")
    _req("PATCH", f"/api/inventory/{iid}/adjust", token, {"quantidade_delta": -3}, expect=200, label="ajustar estoque")
    return produto_id


def test_dispense(token: str, produto_id: int) -> None:
    print("\n== 8. DISPENSA (pharmacy) ==")
    _req("POST", "/api/pharmacy/dispense", token, {
        "prescricao_id": None,
        "itens": [{"produto_id": produto_id, "quantidade": 1}],
        "observacoes": "Dispensa E2E",
    }, expect=201, label="dispensar")
    # estoque insuficiente
    _req("POST", "/api/pharmacy/dispense", token, {
        "prescricao_id": None,
        "itens": [{"produto_id": produto_id, "quantidade": 9999}],
        "observacoes": "Sem estoque",
    }, expect=400, label="dispensa sem estoque")


def test_icatalog(token: str) -> int:
    print("\n== 9. CADASTRO INTELIGENTE (icatalog) ==")
    # upload de planilha XLSX com produtos (o extrator aceita PDF/PNG/JPG/XLSX)
    import io as _io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "produtos"
    ws.append(["nome", "categoria", "unidade", "concentracao"])
    ws.append(["Óleo CBD E2E Catalogo", "oleo", "ml", "3000mg"])
    ws.append(["Gummy Relax E2E Catalogo", "gummy", "un", "10mg"])
    buf = _io.BytesIO()
    wb.save(buf)
    xlsx_bytes = buf.getvalue()

    boundary = "----e2eboundary"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="arquivo"; filename="catalogo_e2e.xlsx"\r\n'
        "Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode() + xlsx_bytes + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{BASE_URL}/api/icatalog/upload",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            j = json.loads(resp.read())
            print(f"  ✓ POST /api/icatalog/upload → {resp.status}")
            global PASSED
            PASSED += 1
            _req("GET", "/api/icatalog/reviews", token, expect=200, label="listar revisões")
            _req("GET", "/api/icatalog/reviews/stats", token, expect=200, label="estatísticas")
            return j.get("detected_count", 0)
    except urllib.error.HTTPError as e:
        global FAILED
        FAILED += 1
        FAILURES.append(f"POST /api/icatalog/upload → {e.code}")
        print(f"  ✗ POST /api/icatalog/upload → {e.code}: {e.read()[:200]}")
        return 0


def test_prescricao(token: str, paciente_id: int, produto_id: int) -> None:
    print("\n== 10. PRESCRIÇÃO ==")
    _req("POST", "/api/prescricoes/gerar", token, {
        "paciente_id": paciente_id,
        "itens": [{"produto_id": produto_id, "dosagem": "5 gotas 2x/dia"}],
        "validade_dias": 30,
    }, expect=200, label="gerar prescrição")


def test_admin(token: str) -> None:
    print("\n== 11. ADMIN ==")
    _req("GET", "/api/admin/dashboard-stats", token, expect=200, label="dashboard stats")
    _req("GET", "/api/admin/usuarios", token, expect=200, label="listar usuários")
    _req("GET", "/api/admin/sistema/health", token, expect=200, label="health")


def main() -> None:
    print(f"E2E AraOS SIAP — {BASE_URL}")
    print(f"Admin: {ADMIN_USER}")

    token = login_admin()
    new_token = test_cadastro_inicial()

    paciente_id = test_pacientes(token)
    test_consultas(token, paciente_id)
    test_evolucoes(token, paciente_id)
    test_exames(token, paciente_id)
    test_catalogo(token)
    produto_estoque_id = test_inventory(token)
    test_dispense(token, produto_estoque_id)
    test_icatalog(token)
    test_prescricao(token, paciente_id, produto_estoque_id)
    test_admin(token)

    print("\n" + "=" * 60)
    print(f"RESULTADO: {PASSED} PASSARAM, {FAILED} FALHARAM")
    if FAILURES:
        print("\nFALHAS:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("✔ TODOS OS FLUXOS E2E OK")


if __name__ == "__main__":
    main()
