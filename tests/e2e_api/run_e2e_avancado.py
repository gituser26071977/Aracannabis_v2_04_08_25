"""Suíte E2E Avançada do AraOS SIAP — módulos complementares.

Roda contra https://api.vittalis.site (produção) OU BASE_URL env.

Cobre:
  1. Exames numéricos (chartable)
  2. LGPD (consentimento, solicitação, exportação)
  3. PHQ-9 (depressão)
  4. GAD-7 (ansiedade)
  5. Beck Depression
  6. SNAP-IV (TDAH)
  7. Faturamento (convênios, serviços)
  8. Billing (planos, providers)

Uso:
    python tests/e2e_api/run_e2e_avancado.py
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
            j = json.loads(resp.read())
            if code == expect:
                PASSED += 1
                print(f"  ✓ {method} {path} → {code}")
            else:
                FAILED += 1
                FAILURES.append(f"{method} {path} → {code} (esperava {expect})")
                print(f"  ✗ {method} {path} → {code} (esperava {expect})")
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
            FAILURES.append(f"{method} {path} → {code} (esperava {expect})")
            print(f"  ✗ {method} {path} → {code} (esperava {expect})")
            if label:
                print(f"    [{label}] {j}")
        return j
    except Exception as e:  # noqa: BLE001
        FAILED += 1
        FAILURES.append(f"{method} {path} → EXCEÇÃO {e}")
        print(f"  ✗ {method} {path} → EXCEÇÃO {e}")
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


def criar_paciente(token: str) -> int:
    print("\n== PACIENTE BASE ==")
    r = _req("POST", "/api/pacientes/", token, {
        "nome": f"Paciente Avancado {_uid()}",
        "data_nascimento": "1985-03-10",
    }, expect=201, label="criar paciente")
    pid = (r.get("paciente") or {}).get("id") or r.get("id")
    assert pid, f"Paciente sem id: {r}"
    return pid


def test_exame_numerico(token: str, paciente_id: int) -> None:
    print("\n== 1. EXAME NUMÉRICO (chartable) ==")
    _req("POST", "/api/exames", token, {
        "paciente_id": paciente_id,
        "titulo": "Hemoglobina Glicada E2E",
        "tipo_exame": "numerico",
        "valor": "5.8",
        "unidade": "%",
        "data_exame": "2026-08-01",
    }, expect=201, label="criar exame numérico")
    _req("GET", f"/api/pacientes/{paciente_id}/exames/chartable", token, expect=200, label="chartable")
    _req("GET", f"/api/pacientes/{paciente_id}/exames", token, expect=200, label="listar exames")


def test_lgpd(token: str, paciente_id: int) -> None:
    print("\n== 2. LGPD ==")
    _req("GET", f"/api/lgpd/consentimento/{paciente_id}", token, expect=200, label="status consentimento")
    _req("POST", f"/api/lgpd/consentimento/{paciente_id}", token, {
        "consentimento": True,
    }, expect=200, label="conceder consentimento")
    _req("GET", f"/api/lgpd/exportar/{paciente_id}", token, expect=200, label="exportar dados")


def test_phq9(token: str, paciente_id: int) -> None:
    print("\n== 3. PHQ-9 (depressão) ==")
    payload = {f"q{i}": 1 for i in range(1, 10)}
    payload["paciente_id"] = paciente_id
    r = _req("POST", f"/api/phq9/paciente/{paciente_id}", token, payload, expect=201, label="criar PHQ-9")
    _req("GET", f"/api/phq9/paciente/{paciente_id}", token, expect=200, label="listar PHQ-9")
    _req("GET", f"/api/phq9/paciente/{paciente_id}/ultimo", token, expect=200, label="último PHQ-9")


def test_gad7(token: str, paciente_id: int) -> None:
    print("\n== 4. GAD-7 (ansiedade) ==")
    payload = {f"q{i}": 2 for i in range(1, 8)}
    r = _req("POST", f"/api/gad7/paciente/{paciente_id}", token, payload, expect=201, label="criar GAD-7")
    _req("GET", f"/api/gad7/paciente/{paciente_id}", token, expect=200, label="listar GAD-7")
    _req("GET", f"/api/gad7/paciente/{paciente_id}/ultimo", token, expect=200, label="último GAD-7")


def test_beck(token: str, paciente_id: int) -> None:
    print("\n== 5. BECK DEPRESSION ==")
    payload = {f"item_{i}": 1 for i in range(1, 22)}
    r = _req("POST", f"/api/beck-depression/paciente/{paciente_id}", token, payload, expect=201, label="criar Beck")
    _req("GET", f"/api/beck-depression/paciente/{paciente_id}", token, expect=200, label="listar Beck")


def test_snap_iv(token: str, paciente_id: int) -> None:
    print("\n== 6. SNAP-IV (TDAH) ==")
    payload = {}
    for i in range(1, 10):
        payload[f"desatencao_{i}"] = 1
    for i in range(10, 19):
        payload[f"hiperatividade_{i}"] = 1
    r = _req("POST", f"/api/snap-iv/paciente/{paciente_id}", token, payload, expect=201, label="criar SNAP-IV")
    _req("GET", f"/api/snap-iv/paciente/{paciente_id}", token, expect=200, label="listar SNAP-IV")


def test_faturamento(token: str) -> None:
    print("\n== 7. FATURAMENTO ==")
    _req("GET", "/api/faturamento/convenios", token, expect=200, label="listar convênios")
    r = _req("POST", "/api/faturamento/convenios", token, {
        "nome": f"Convênio E2E {_uid()}",
    }, expect=201, label="criar convênio")
    _req("GET", "/api/faturamento/servicos", token, expect=200, label="listar serviços")


def test_billing(token: str) -> None:
    print("\n== 8. BILLING ==")
    _req("GET", "/api/billing/plans", token, expect=200, label="listar planos")
    _req("GET", "/api/billing/providers", token, expect=403, label="providers (feature flag off)")
    _req("GET", "/api/billing/invoices", token, expect=200, label="listar faturas")


def main() -> None:
    print(f"E2E AVANÇADO AraOS SIAP — {BASE_URL}")

    token = login_admin()
    paciente_id = criar_paciente(token)

    test_exame_numerico(token, paciente_id)
    test_lgpd(token, paciente_id)
    test_phq9(token, paciente_id)
    test_gad7(token, paciente_id)
    test_beck(token, paciente_id)
    test_snap_iv(token, paciente_id)
    test_faturamento(token)
    test_billing(token)

    print("\n" + "=" * 60)
    print(f"RESULTADO: {PASSED} PASSARAM, {FAILED} FALHARAM")
    if FAILURES:
        print("\nFALHAS:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("✔ TODOS OS FLUXOS E2E AVANÇADOS OK")


if __name__ == "__main__":
    main()
