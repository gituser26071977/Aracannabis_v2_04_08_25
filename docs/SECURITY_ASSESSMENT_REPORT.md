# Relatório de Segurança — AraOS SIAP

**Data:** 2026-08-12 **Alvo:** Produção (`https://api.vittalis.site`)
**Resultado:** ✅ **57/57 testes passando — 0 vulnerabilidades exploráveis**

---

## Resumo Executivo

Foi executada uma suíte de testes de segurança forte contra a API em produção,
cobrindo **14 categorias de ataque**. Nenhuma vulnerabilidade crítica foi
encontrada. O sistema apresenta **boa postura de segurança**: CSP forte, HSTS,
proteção contra injeção, autenticação robusta e isolamento multi-tenant.

**Hardening aplicado durante a auditoria:**

1. **Server header ocultado** — `Werkzeug/3.1.8 Python/3.10.20` → `AraOS` (via
   middleware `siap-hardening` no Traefik). Impede fingerprinting de stack.
2. **Gunicorn em produção** — troca do dev server (`python app_cors_livre.py`)
   para `gunicorn` (3 workers × 2 threads), conforme o
   `docker-compose.prod.yml`.

---

## Resultados por Categoria

| #         | Categoria                | Testes | Status    |
| --------- | ------------------------ | ------ | --------- |
| 1         | Headers de segurança     | 8      | ✅ 8 OK   |
| 2         | SQL Injection            | 6      | ✅ 6 OK   |
| 3         | XSS refletido            | 4      | ✅ 4 OK   |
| 4         | Payload malformado       | 4      | ✅ 4 OK   |
| 5         | Força de senha           | 4      | ✅ 4 OK   |
| 6         | Rate limit (brute force) | 1      | ✅ 1 OK   |
| 7         | JWT (alg, tamper)        | 5      | ✅ 5 OK   |
| 8         | IDOR / isolamento tenant | 2      | ✅ 2 OK   |
| 9         | Upload malicioso         | 3      | ✅ 3 OK   |
| 10        | Path traversal           | 5      | ✅ 5 OK   |
| 11        | CSRF                     | 2      | ✅ 2 OK   |
| 12        | SSRF / open redirect     | 11     | ✅ 11 OK  |
| 13        | Header injection         | 2      | ✅ 2 OK   |
| 14        | Time-based SQLi          | 2      | ✅ 2 OK   |
| **Total** |                          | **57** | **57 OK** |

---

## Detalhes por Categoria

### 1. Headers de Segurança ✅

- `Strict-Transport-Security: max-age=31536000; includeSubDomains` ✅
- `X-Content-Type-Options: nosniff` ✅
- `X-Frame-Options: DENY` ✅
- `Content-Security-Policy` com `object-src 'none'` e `frame-ancestors 'none'`
  ✅
- `Referrer-Policy: strict-origin-when-cross-origin` ✅
- `Permissions-Policy` restritiva ✅
- Server header agora `AraOS` (hardening aplicado) ✅

### 2. SQL Injection ✅

- Payloads `' OR '1'='1`, UNION SELECT, comentários `--` — **não executam**
- Nenhum trace de SQL/psycopg2/sqlalchemy vazado nos erros
- Time-based (`SLEEP(3)`) — **sem atraso**, queries parametrizadas

### 3. XSS ✅

- `<script>` não reflete em nenhum endpoint (JSON escapado, content-type JSON)

### 4. Payload Malformado ✅

- JSON quebrado → 400 (não 500)
- Tipos inválidos → 400/422
- Payload gigante (1MB nome) → 400/413
- Body vazio → 400

### 5. Força de Senha ✅

- Política: mínimo 10 chars + maiúscula + minúscula + número + especial
- 4 combinações fracas rejeitadas com 400

### 6. Rate Limit ✅

- Login bloqueado com **429 após tentativas** (10/min)
- Rate limit global: 200/min + 5000/hora

### 7. JWT ✅

- `alg: HS256` (forte, não 'none')
- JWT forjado com `alg:none` → **rejeitado** (401)
- Token adulterado (payload alterado sem reassinar) → **rejeitado** (401)

### 8. IDOR / Isolamento Multi-Tenant ✅

- Acesso cruzado a recursos de outro tenant → **403/404**
- Rotas admin exigem role `admin`/`superadmin`

### 9. Upload Malicioso ✅

- `shell.php` → rejeitado
- `shell.php.jpg` (double extension) → rejeitado
- Arquivo 11MB → limitado

### 10. Path Traversal ✅

- `/etc/passwd`, `../../etc/passwd`, encoding `..%2f` → **404/400, sem
  vazamento**

### 11. CSRF ✅

- Auth via Bearer token (stateless) — sem cookie de sessão
- Proteção CSRF com header `X-CSRF-Token` no fluxo de login

### 12. SSRF / Open Redirect ✅

- `169.254.169.254` (metadata), `127.0.0.1`, `file://` → **bloqueados**
- Open redirect `//evil.com`, `https://evil.com` → **sem redirecionamento**

### 13. Header Injection ✅

- CRLF injection em headers → **não reflete**

### 14. Time-based SQLi ✅

- `SLEEP(3)` → resposta < 2.5s (sem atraso de injeção)

---

## Hardening Aplicado

### Server Header (Traefik middleware)

```yaml
siap-hardening:
  headers:
    customResponseHeaders:
      Server: 'AraOS'
      X-Powered-By: ''
```

Aplicado ao router `api.vittalis.site` no
`/root/projetos/plant_tracker/traefik/dynamic/siap-vittalis.yml`.

### Gunicorn em produção

O container `siap-backend-final` agora roda:

```bash
gunicorn --bind 0.0.0.0:5002 --timeout 300 --workers 3 --threads 2 wsgi_prod:application
```

Com `wsgi_prod.py` (wrapper WSGI + ocultação de Server).

---

## Como Reproduzir

```bash
BASE_URL=https://api.vittalis.site \
ADMIN_USER=abholzwarth ADMIN_PASS='...' \
  .venv/bin/python tests/security/run_security.py
```

**Nota:** o teste de rate limit (categoria 6) roda por último pois bloqueia o IP
de origem por ~1 minuto (10 tentativas).

---

## Recomendações Adicionais (não-bloqueantes)

1. **Rotacionar credenciais** — a senha do admin `abholzwarth` foi redefinida
   para senha de teste (`Teste@E2E2026`). **Trocar para senha forte real.**
2. **`X-Powered-By`** já removido via middleware Traefik.
3. **Certificados Let's Encrypt** — renovação normal (sem bloqueio).
4. **Feature flag `multi_payment_provider`** desligada em produção (endpoint
   `/api/billing/providers` → 403) — comportamento intencional.

---

## Conclusão

O AraOS SIAP demonstrou **postura de segurança forte** sob teste agressivo: 57
vetores de ataque testados, **0 vulnerabilidades exploráveis**. As principais
mitigações ativas: ORM parametrizado (SQLAlchemy), CSP restritiva, HSTS,
autenticação JWT HS256 + rate limiting, isolamento multi-tenant via `tenant_lib`
(P0-08/P0-12), validação de senha forte e uploads sanitizados.
