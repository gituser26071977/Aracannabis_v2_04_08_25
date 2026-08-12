"""Suíte de Testes de Segurança — AraOS SIAP (produção).

Testes NÃO-destrutivos contra https://api.vittalis.site (ou BASE_URL env).

Cobre:
  1. Headers de segurança (CSP, HSTS, nosniff, frame, referrer)
  2. SQL Injection (autenticada + não-autenticada)
  3. XSS refletido em parâmetros
  4. Payload malformado (JSON quebrado, tipos errados)
  5. Auth: força de senha, senha fraca, credenciais erradas
  6. Rate limit (brute-force no login)
  7. JWT: alg 'none', token adulterado, claims
  8. IDOR / isolamento multi-tenant (acesso cruzado)
  9. Upload malicioso (extensão perigosa, arquivo grande)
  10. Path traversal
  11. CSRF (POST sem token vs com token)

Uso:
    python tests/security/run_security.py
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

BASE_URL = os.getenv("BASE_URL", "https://api.vittalis.site").rstrip("/")
ADMIN_USER = os.getenv("ADMIN_USER", "abholzwarth")
ADMIN_PASS = os.getenv("ADMIN_PASS", "Teste@E2E2026")

PASSED = 0
FAILED = 0
VULNERABILITIES: list[str] = []
INFO: list[str] = []


def _request(
    method: str,
    path: str,
    token: Optional[str] = None,
    body: Any = None,
    headers_extra: Optional[Dict[str, str]] = None,
    raw_body: Optional[bytes] = None,
    ctype: str = "application/json",
) -> tuple[int, Any, Dict[str, str]]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": ctype}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        headers.update(headers_extra)
    data = raw_body if raw_body is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp_headers: Dict[str, str] = {}
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            for k, v in resp.headers.items():
                resp_headers[k.lower()] = v
            try:
                j = json.loads(payload)
            except Exception:
                j = {"raw": payload[:300].decode(errors="replace")}
            return resp.status, j, resp_headers
    except urllib.error.HTTPError as e:
        try:
            for k, v in e.headers.items():
                resp_headers[k.lower()] = v
            j = json.loads(e.read())
        except Exception:
            j = {"raw": str(e)}
        return e.code, j, resp_headers
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}, resp_headers


def _check(name: str, cond: bool, detail: str = "", severity: str = "") -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✓ {name}")
    else:
        FAILED += 1
        tag = f" [{severity}]" if severity else ""
        print(f"  ✗ {name}{tag}: {detail}")
        VULNERABILITIES.append(f"{name}: {detail}")


def _info(name: str, detail: str = "") -> None:
    INFO.append(f"{name}: {detail}")
    print(f"  ℹ {name}: {detail}")


def login_admin() -> str:
    print("\n== LOGIN ADMIN (setup) ==")
    status, j, _ = _request("POST", "/api/auth/login", body={"usuario": ADMIN_USER, "senha": ADMIN_PASS})
    if status != 200:
        print(f"  !! Falha login: {status} {j}")
        sys.exit(1)
    return j["access_token"]


# REDACTED #
# 1. HEADERS DE SEGURANÇA
# REDACTED #
def test_headers() -> None:
    print("\n== 1. HEADERS DE SEGURANÇA ==")
    _, _, h = _request("GET", "/api/status")
    _check("Strict-Transport-Security", "strict-transport-security" in h, str(h.get("strict-transport-security")), "HIGH")
    _check("X-Content-Type-Options: nosniff", h.get("x-content-type-options", "").lower() == "nosniff", str(h.get("x-content-type-options")), "MEDIUM")
    _check("X-Frame-Options", "x-frame-options" in h and h.get("x-frame-options").upper() in ("DENY", "SAMEORIGIN"), str(h.get("x-frame-options")), "MEDIUM")
    _check("Content-Security-Policy", "content-security-policy" in h, "", "HIGH")
    csp = h.get("content-security-policy", "")
    if csp:
        _check("CSP: object-src none", "object-src 'none'" in csp, "", "MEDIUM")
        _check("CSP: frame-ancestors none", "frame-ancestors 'none'" in csp, "", "MEDIUM")
    _check("Referrer-Policy", "referrer-policy" in h, str(h.get("referrer-policy")), "LOW")
    _check("Permissions-Policy", "permissions-policy" in h, "", "LOW")
    _info("Server header (Werkzeug dev server)", h.get("server", "n/a") + " — dev server exposto em prod")


# REDACTED #
# 2. SQL INJECTION
# REDACTED #
def test_sqli(token: str) -> None:
    print("\n== 2. SQL INJECTION ==")
    targets = [
        ("GET", "/api/pacientes/", {"nome": "' OR '1'='1"}),
        ("GET", "/api/pacientes/", {"busca": "x' OR '1'='1' --"}),
        ("GET", "/api/catalogo/produtos", {"nome": "' OR 1=1--"}),
        ("GET", "/api/consultas/", {"status": "' OR '1'='1' --"}),
        ("GET", "/api/sintomas/", {"nome": "' OR '1'='1"}),
        ("POST", "/api/pacientes/", {"nome": "1' UNION SELECT * FROM profissionais--", "data_nascimento": "1990-01-01"}),
    ]
    for method, path, params in targets:
        if method == "GET":
            qs = urllib.parse.urlencode(params)
            sep = "&" if "?" in path else "?"
            status, j, _ = _request("GET", f"{path}{sep}{qs}", token)
        else:
            status, j, _ = _request("POST", path, token, body=params)
        err = json.dumps(j).lower()
        sqlerr = any(k in err for k in ["syntax error", "psycopg2", "sqlalchemy.exc", "duplicate key", "sqlite3.", "database error", "stack trace"])
        # POST pode retornar 201 (nome salvo literalmente) — não é SQLi;
        # o que indica SQLi é trace de SQL no erro ou vazamento de dados.
        ok = (status in (200, 201, 400, 401, 404, 422)) and not sqlerr
        _check(f"SQLi {params} → {status}", ok, f"SQL error trace: {j}" if sqlerr else f"status {status}", "CRITICAL")


# REDACTED #
# 3. XSS
# REDACTED #
def test_xss(token: str) -> None:
    print("\n== 3. XSS ==")
    xss = "<script>alert(1)</script>"
    endpoints = [
        f"/api/pacientes/?{urllib.parse.urlencode({'nome': xss})}",
        f"/api/consultas/?{urllib.parse.urlencode({'status': xss})}",
        f"/api/catalogo/produtos?{urllib.parse.urlencode({'nome': xss})}",
        f"/api/sintomas/?{urllib.parse.urlencode({'nome': xss})}",
    ]
    for ep in endpoints:
        status, j, _ = _request("GET", ep, token)
        body = json.dumps(j)
        raw_in = "<script>" in body
        if raw_in:
            # verificar se é XSS executável (refletido sem escape) ou apenas eco em JSON
            # JSON não executa script; só é XSS se vier como HTML/texto não escapado
            ctype = ""
            _, _, h2 = _request("GET", ep, token)
            ctype = h2.get("content-type", "")
            is_html = "text/html" in ctype
            _check(f"XSS em {ep.split('?')[0]}", not is_html, "payload refletido em HTML", "HIGH")
        else:
            _check(f"XSS em {ep.split('?')[0]}", True, "", "")


# REDACTED #
# 4. PAYLOAD MALFORMADO
# REDACTED #
def test_malformed(token: str) -> None:
    print("\n== 4. PAYLOAD MALFORMADO ==")
    # JSON quebrado
    status, j, _ = _request("POST", "/api/pacientes/", token, raw_body=b'{"nome": "X",', ctype="application/json")
    _check("JSON quebrado não causa 500", status in (400, 415, 422), f"status {status}: {j}", "MEDIUM")
    # Tipos errados
    status, j, _ = _request("POST", "/api/pacientes/", token, body={"nome": 12345, "data_nascimento": "not-a-date"})
    _check("Tipos inválidos → 400/422", status in (400, 422), f"status {status}: {j}", "MEDIUM")
    # Array gigante
    status, j, _ = _request("POST", "/api/catalogo/produtos", token, body={"nome": "x" * 1000000, "marca": "m"})
    _check("Payload gigante → 400/413", status in (400, 413), f"status {status}", "LOW")
    # Body vazio
    status, j, _ = _request("POST", "/api/pacientes/", token, body=None)
    _check("Body vazio → 400", status == 400, f"status {status}: {j}", "LOW")


# REDACTED #
# 5. AUTH — FORÇA DE SENHA
# REDACTED #
def test_password_strength(token: str) -> None:
    print("\n== 5. AUTH — FORÇA DE SENHA ==")
    usuario = f"sec_{int(time.time())}"
    weak_cases = [
        ("senha123", "só minúsculas+números, <10"),
        ("abcdefghij", "10 minúsculas, sem maiúsc/num/spec"),
        ("SENHA12345", "sem minúscula/especial"),
        ("Senha@2026", "8 chars, <10"),
    ]
    for senha, desc in weak_cases:
        status, j, _ = _request("POST", "/api/auth/register", body={
            "nome": "Teste", "crm": f"{999990 + len(senha)}", "uf_crm": "SP",
            "usuario": usuario, "senha": senha, "email": f"{usuario}@sec.local",
        })
        _check(f"Senha fraca rejeitada ({desc})", status == 400, f"status {status}: {j}", "HIGH")


# REDACTED #
# 6. RATE LIMIT / BRUTE FORCE
# REDACTED #
def test_rate_limit() -> None:
    print("\n== 6. RATE LIMIT (brute-force login) ==")
    limit_hit = False
    for i in range(12):
        status, j, h = _request("POST", "/api/auth/login", body={"usuario": "admin", "senha": f"errada{i}"})
        if status == 429:
            limit_hit = True
            break
        time.sleep(0.2)
    _check("Rate limit 429 após tentativas", limit_hit, "login não bloqueou após 12 tentativas", "HIGH")


# REDACTED #
# 7. JWT
# REDACTED #
def test_jwt() -> None:
    print("\n== 7. JWT ==")
    token = login_admin()
    parts = token.split(".")
    if len(parts) == 3:
        header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
        _check("JWT alg não é 'none'", header.get("alg", "").lower() != "none", f"alg={header.get('alg')}", "CRITICAL")
        _check("JWT alg é HS256 (forte)", header.get("alg") in ("HS256", "RS256", "ES256"), f"alg={header.get('alg')}", "HIGH")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        _info("Claims JWT", str(sorted(payload.keys())))
    # Token com alg=none
    forged = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode() + "." + base64.urlsafe_b64encode(b'{"sub":"1","roles":["admin"]}').rstrip(b"=").decode() + "."
    status, j, _ = _request("GET", "/api/admin/usuarios", token=forged)
    _check("JWT alg=none rejeitado", status in (401, 422), f"status {status}", "CRITICAL")
    # Token adulterado (payload alterado sem reassinar)
    h = parts[0]
    tampered_payload = base64.urlsafe_b64encode(json.dumps({"sub": "1", "roles": ["admin"]}).encode()).rstrip(b"=").decode()
    tampered = f"{h}.{tampered_payload}.{parts[2]}"
    status, j, _ = _request("GET", "/api/admin/usuarios", token=tampered)
    _check("JWT adulterado rejeitado", status in (401, 422), f"status {status}", "CRITICAL")


# REDACTED #
# 8. IDOR / ISOLAMENTO MULTI-TENANT
# REDACTED #
def test_idor(token: str) -> None:
    print("\n== 8. IDOR / ISOLAMENTO TENANT ==")
    # Tentar acessar recurso de outro tenant (associação 1 vs 8)
    # Paciente de outra associação via ID alto / direto
    status, j, _ = _request("GET", "/api/pacientes/1", token)
    # Se retorna 200 com dados de outro tenant, é vazamento
    if status == 200 and isinstance(j, dict) and j.get("paciente"):
        pa = j["paciente"]
        assoc = pa.get("associacao_id")
        _info("Acesso ao paciente id=1", f"associacao_id={assoc}")
        _check("IDOR: paciente de outro tenant bloqueado", assoc == 8, f"acessou paciente de tenant {assoc}", "CRITICAL")
    elif status in (403, 404):
        _check("IDOR: acesso cruzado bloqueado (403/404)", True, f"status {status}", "")
    else:
        _check("IDOR: comportamento seguro", status in (200, 403, 404), f"status {status}", "CRITICAL")
    # Admin dashboard deve ser restrito
    status, j, _ = _request("GET", "/api/admin/usuarios", token)
    _check("Admin rotas exigem role", status in (200, 403), f"status {status}", "HIGH")


# REDACTED #
# 9. UPLOAD MALICIOSO
# REDACTED #
def test_upload(token: str) -> None:
    print("\n== 9. UPLOAD MALICIOSO ==")
    evil = b'<?php system($_GET["cmd"]); ?>'
    boundary = "----secboundary"
    for fname, ctype in [("shell.php", "application/x-php"), ("shell.php.jpg", "image/jpeg")]:
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="arquivo"; filename="{fname}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode() + evil + f"\r\n--{boundary}--\r\n".encode()
        status, j, _ = _request(
            "POST", "/api/icatalog/upload", token,
            raw_body=body, ctype=f"multipart/form-data; boundary={boundary}",
        )
        ok = status in (400, 415, 422)  # deve rejeitar PHP
        _check(f"Upload rejeitado: {fname}", ok, f"status {status}: {j}", "CRITICAL")
    # arquivo gigante (limite de tamanho)
    big = b"0" * (11 * 1024 * 1024)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="arquivo"; filename="big.xlsx"\r\n'
        f"Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n"
    ).encode() + big + f"\r\n--{boundary}--\r\n".encode()
    status, j, _ = _request(
        "POST", "/api/icatalog/upload", token,
        raw_body=body, ctype=f"multipart/form-data; boundary={boundary}",
    )
    _check("Upload gigante (11MB) limitado", status in (400, 413, 422), f"status {status}", "MEDIUM")


# REDACTED #
# 10. PATH TRAVERSAL
# REDACTED #
def test_path_traversal(token: str) -> None:
    print("\n== 10. PATH TRAVERSAL ==")
    payloads = ["/etc/passwd", "../../../../etc/passwd", "..%2f..%2fetc%2fpasswd", "/etc/shadow"]
    for p in payloads:
        encoded = urllib.parse.quote(p, safe="")
        status, j, _ = _request("GET", f"/api/pacientes/foto/{encoded}", token)
        ok = status in (400, 404, 422) or "root:" not in json.dumps(j)
        _check(f"Path traversal {p[:20]!r}", ok, f"status {status}", "CRITICAL")
    encoded2 = urllib.parse.quote("../../../../etc/passwd", safe="")
    status, j, _ = _request("GET", f"/api/exames/arquivos/{encoded2}", token)
    _check("Path traversal exames", "root:" not in json.dumps(j), f"status {status}: vazou /etc/passwd", "CRITICAL")


# REDACTED #
# 11. CSRF
# REDACTED #
def test_csrf(token: str) -> None:
    print("\n== 11. CSRF ==")
    # Verificar se POST sensível funciona sem CSRF token (api stateless = OK em geral,
    # mas se houver sessão de cookie, é risco). Aqui testamos se os headers de CSRF existem.
    _, _, h = _request("GET", "/api/status")
    has_csrf_token = "x-csrf-token" in {k.lower() for k in h.keys()}
    _info("Header CSRF presente na resposta", str(has_csrf_token))
    # O auth usa Bearer (stateless) — CSRF clássico (cookie-based) não se aplica se
    # não houver cookie de sessão. Verificar set-cookie.
    has_cookie = any("set-cookie" in k.lower() for k in h.keys())
    _check("Sem cookie de sessão (auth via Bearer)", not has_cookie, "resposta define cookie de sessão", "MEDIUM")


def test_ssrf_open_redirect(token: str) -> None:
    print("\n== 12. SSRF / OPEN REDIRECT ==")
    # SSRF via parâmetros de URL
    ssrf_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:5432/",
        "http://localhost:5002/api/status",
        "file:///etc/passwd",
    ]
    for t in ssrf_targets:
        encoded = urllib.parse.quote(t, safe="")
        for path in [f"/api/import-export/import?url={encoded}", f"/api/catalogo/atualizacoes-web?url={encoded}"]:
            status, j, _ = _request("GET", path, token)
            body = json.dumps(j)
            leaked = "meta-data" in body or "postgres" in body or "root:" in body
            ok = status in (400, 404, 422) or not leaked
            _check(f"SSRF {path.split('?')[0]} ({t[:25]})", ok, f"status {status}, vazou dados: {leaked}", "CRITICAL")
    # Open redirect — endpoints que redirecionam
    for redir in ["//evil.com", "https://evil.com", "/%2f%2fevil.com"]:
        status, j, h = _request("GET", f"/auth/login?next={urllib.parse.quote(redir, safe='')}", token)
        loc = h.get("location", "")
        _check(f"Open redirect {redir[:20]!r}", "evil.com" not in loc, f"location={loc}", "HIGH")


def test_header_injection(token: str) -> None:
    print("\n== 13. HEADER INJECTION ==")
    evil_headers = {
        "X-Injected": "val\r\nX-Evil: 1",
        "Referer": "http://x.com\r\nX-R: 2",
    }
    for name, val in evil_headers.items():
        status, j, h = _request("GET", "/api/status", token, headers_extra={name: val})
        _check(f"Header injection via {name}", "X-Evil" not in str(h) and "X-R" not in str(h), f"status {status}", "MEDIUM")


def test_timebased_sqli(token: str) -> None:
    print("\n== 14. TIME-BASED SQLi ==")
    # Se a query é interpolada, SLEEP retorna com atraso
    t0 = time.time()
    status, j, _ = _request("GET", "/api/pacientes/?nome=x' OR SLEEP(3)--", token)
    elapsed = time.time() - t0
    _check("Time-based SQLi (SLEEP)", elapsed < 2.5, f"resposta em {elapsed:.1f}s (≥3s indica injeção)", "CRITICAL")
    t0 = time.time()
    status, j, _ = _request("GET", "/api/catalogo/produtos?nome=x' AND SLEEP(3)--", token)
    elapsed = time.time() - t0
    _check("Time-based SQLi catálogo (SLEEP)", elapsed < 2.5, f"resposta em {elapsed:.1f}s", "CRITICAL")


def main() -> None:
    print(f"SECURITY TEST AraOS SIAP — {BASE_URL}")
    token = login_admin()

    test_headers()
    test_sqli(token)
    test_xss(token)
    test_malformed(token)
    test_password_strength(token)
    test_jwt()
    test_idor(token)
    test_upload(token)
    test_path_traversal(token)
    test_csrf(token)
    test_ssrf_open_redirect(token)
    test_header_injection(token)
    test_timebased_sqli(token)
    test_rate_limit()  # último: bloqueia o IP por 1 min

    print("\n" + "=" * 60)
    print(f"RESULTADO: {PASSED} OK, {FAILED} FALHAS")
    if VULNERABILITIES:
        print(f"\n⚠️  VULNERABILIDADES ({len(VULNERABILITIES)}):")
        for v in VULNERABILITIES:
            print(f"  - {v}")
    if INFO:
        print("\nInformações:")
        for i in INFO:
            print(f"  - {i}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
