# SECURITY_AUDIT.md — Login, RBAC, Autenticação e Isolamento

**Data:** 2026-07-22
**Escopo:** read-only — auditoria de segurança sem modificação.
**Fonte:** `.raw-evidence-security.md`, `routes/auth.py`, `routes/patient_auth.py`, `araos/platform/identity/*`, `araos/platform/audit/ledger.py`.

---

## 1. Resumo Executivo

| Categoria | Estado | Severidade |
|---|---|:---:|
| Password hashing | 🟠 PBKDF2-SHA256 100k (bcrypt ausente) | Média |
| Tokens JWT | 🟠 2 sistemas paralelos (Flask + AraOS) | Alta |
| RBAC | 🔴 Catálogo 106, aplicação 0 | Crítica |
| Tenant isolation | 🟠 3 mecanismos divergentes | Alta |
| CSRF | 🟠 Helper existe, 0 aplicação | Alta |
| Audit log | 🟠 AraOS ledger não conectado | Alta |
| MFA | 🔴 Modelo existe, sem OTP/TOTP/recovery | Crítica |
| CORS | 🟢 Config allowlist (sem wildcard) | OK |
| Rate limit | 🟢 Flask-Limiter em auth | OK |
| Header security | 🟢 CSP nonce, HSTS, frame DENY | OK |
| File upload | 🟠 Sem inspeção de conteúdo | Média |
| Secret management | 🔴 SECRET_KEY hardcoded em compose | Crítica |
| SQL injection | 🟢 ORM com binds | OK |
| XSS | 🟢 Escape via React + CSP | OK |

## 2. Camadas de Autenticação

### 2.1 Camada 1 — Flask/SIAP (ativa)

- **Login profissional** (`routes/auth.py:82`):
  - `POST /login` aceita email OU usuario
  - Hash: Werkzeug `pbkdf2:sha256:100000`
  - Token: `flask-jwt-extended` `create_access_token(identity=id, expires_delta=12h)`
  - Claims: `sub, exp, iat, user_type`
  - SEM tenant_id, SEM roles, SEM permissions
  
- **Login paciente** (`routes/patient_auth.py:149`):
  - `POST /login` email
  - Token com `user_type:patient`
  - 12h access, sem refresh

- **Auth decorators** (`routes/auth_decorators.py`):
  - `@require_staff_role`, `@require_roles`, `@require_permission`
  - **ZERO aplicação em produção**

### 2.2 Camada 2 — AraOS Platform (parcialmente integrada)

- **Provider AraOS** (`araos/platform/identity/tokens.py`):
  - HS256 (não RS256)
  - Access (claims ricos) + Refresh 30d (usage-unique)
  - `jti` revocation em memória (`_revoked_jtis: set`)
  - Claims: `sub, tenant_id, org_id, clinic_ids, roles, permissions, actor_type, jti, iat, exp, type, version, email, full_name, plan, delegated_by`

### 2.3 Divergência

| Aspecto | Flask | AraOS Provider |
|---|---|---|
| Algoritmo | HS256 | HS256 |
| Access TTL | 12h | configurável |
| Refresh | SEM | 30d |
| Tenant em claim | NÃO | SIM |
| Roles/perms em claim | NÃO | SIM |
| Revogação | SEM | in-memory only |
| Integração produção | SIM | NÃO |

## 3. JWT Token System

### 3.1 Provider Flask Ativo

```python
# routes/auth.py
access_token = create_access_token(
    identity=str(profissional.id),
    expires_delta=timedelta(hours=12),
    additional_claims={"user_type": "professional"}
)
```

**Problemas:**
- Sem tenant_id (frontend envia X-Association-ID)
- Sem roles (roles vivem em `ProfissionalGrupo` table)
- Sem permissions
- Sem device fingerprint

### 3.2 Provider AraOS (não integrado)

```python
# araos/platform/identity/tokens.py
class AraOSTokenProvider:
    def issue_access(self, actor, ...) -> str:
        claims = {
            "sub": str(actor.id),
            "tenant_id": actor.tenant_id,
            "org_id": actor.org_id,
            "clinic_ids": actor.clinic_ids,
            "roles": [r.name for r in actor.roles],
            "permissions": actor.effective_permissions,
            "actor_type": actor.type,
            "jti": uuid4().hex,
            "iat": now,
            "exp": now + ttl,
            "version": "1",
            "email": actor.email,
            "full_name": actor.full_name,
            "plan": actor.plan,
            "delegated_by": actor.delegated_by,
        }
        return jwt.encode(claims, secret, algorithm="HS256")
```

**Problemas:**
- Revogação em memória: `_revoked_jtis: set = set()  # Em produção: Redis/DB`
- Comentário explícito: substituir por Redis ou DB antes de produção

### 3.3 SECRET_KEY Hardcoded

- `docker-compose.siap.yml`:
  - `SECRET_KEY=SIAP_SECRET_REDACTED` — < 32 chars
- Code aborta em prod se fraco, mas compose de dev/staging ignora

## 4. RBAC

### 4.1 Permission Registry

- **Arquivo:** `araos/platform/identity/permissions.py` (724 linhas)
- **Tipo:** NÃO é `enum.Enum` — é classe com **106 constantes**
- **Cobertura:** 27 prefixos

### 4.2 Decorators Disponíveis (não aplicados)

```python
def require_permission(permission: str):
    """Aplica verificação de permissão em endpoint Flask."""
    # ... (verifica g.current_user.permissions)
    # NOTE: exemplo no docstring apenas
```

| Decorator | Localização | Uso em produção |
|---|---|---|
| `@require_permission` | auth_decorators.py | **0 endpoints** |
| `@require_staff_role` | auth_decorators.py | parcial (few endpoints) |
| `@require_roles(*r)` | auth_decorators.py | parcial |
| `@require_tenant` | platform/tenant/middleware.py | **não usado** |
| `@validate_json` | utils.py | alguns |
| `@log_endpoint` | utils.py | alguns |

### 4.3 Roles Catalogados (12)

`admin`, `physician`, `secretary`, `manager`, `patient`, `agent`, `service_account`, `viewer`, `neuro_physician`, `health_secretary`, `scientific_producer`, `intelligence_curator`

### 4.4 Gap Fundamental

Endpoints Flask realizam verificação manual:
```python
@jwt_required()
def delete_patient(patient_id):
    if not current_user.is_admin:  # manual
        return jsonify({"error": "forbidden"}), 403
```

Sem padronização central.

## 5. Tenant Isolation

### 5.1 Mecanismos Paralelos

| Mecanismo | Arquivo | Comportamento |
|---|---|---|
| Flask middleware | `tenant_middleware.py` | tenant EXCLUSIVO de vínculo do user |
| Helpers Sprint 4 | `routes/_helpers.py` | `X-Association-ID > X-Tenant-ID > JWT` |
| Platform resolver | `araos/platform/tenant/*` | JWT/API key/service account/X-Tenant-ID |
| Filter SQLAlchemy | `tenant_lib.py` | `do_orm_execute` automático |

### 5.2 `@tenant_required` Decorator

- **Não existe** com esse nome
- Existe `@require_tenant` em platform/middleware.py (não aplicado)
- Sprint 4.5 W3.1 propõe criar `interfaces/auth/decorators.py`

### 5.3 `_assert_same_tenant`

- Existe em `araos/clinical/knowledge/infrastructure/repository.py`
- Levanta `PermissionError` se mismatch
- Não é decorator — é assertion no nível do repository

### 5.4 Riscos Identificados

1. Middleware engole exceções (perde contexto de debug)
2. Helpers aceitam header contradizendo middleware
3. Login Flask não emite tenant_id
4. `_helpers.py` tem prioridade header > JWT (potencial cross-tenant via header forgejado)

## 6. Audit Log

### 6.1 AraOS Ledger (central, mas desconectado)

```python
# araos/platform/audit/ledger.py
class AuditEntry:
    actor_id: str
    actor_tenant_id: str
    action: str
    resource: str
    outcome: Outcome
    before_state_hash: str | None
    after_state_hash: str | None
    ip: str | None
    user_agent: str | None
    correlation_id: str
    metadata: dict

class AuditLedger:
    def append(self, entry: AuditEntry) -> None:
        # hash chain SHA-256
        ...
```

**Status:** código pronto, mas **rotas Flask NÃO chamam `audit.append()`**.

### 6.2 LogAtividade Legacy

- Tabela `log_atividade` em `models.py`
- INSERTs manuais espalhados por ~25 rotas (pacientes, consultas, evolucoes, dosagens, lgpd, admin, ai_management)
- Sem hash chain, sem tenant scope explícito

### 6.3 Clinical Event Store

- Hash chain SHA-256
- Tenant-scoped
- Ativo no BC clinical_event_store

## 7. CSRF

### 7.1 Implementação (`security_config.py`)

```python
def generate_csrf_token() -> str:
    return secrets.token_hex(32)

def validate_csrf(request) -> bool:
    token = request.headers.get("X-CSRF-Token")
    if not token or len(token) < 32:
        return False
    return hmac.compare_digest(token, request.cookies.get("csrf_token"))
```

- Custom, não Flask-WTF
- Ignora GET/HEAD/OPTIONS
- Endpoint público: `GET /api/csrf-token`

### 7.2 Aplicação

**ZERO** endpoints produção usam `@csrf_protect`.
- Helper existe em código
- Apenas `tests/security/test_p0_remediation_m18.py` aplica

## 8. CORS

- Origens permitidas: `localhost:3000-3010`, `localhost:5000/5002/5003/5010`, `backend:5002`, `visualsmartflow.com.br`, `araos.visualsmartflow.com.br`, `192.168.0.104:3000/5002`, `127.0.0.1:3000/5002`
- `192.168.0.104:3000` duplicado
- `X-Association-ID` **removido** da allowlist (frontend envia)
- `supports_credentials=True`
- Sem wildcard `*` (positivo)

## 9. Rate Limiting

```python
# app_cors_livre.py
limiter = Limiter(
    key_func=get_jwt_identity_or_anonymous_ip,
    default_limits=["5000 per hour", "200 per minute"],
    storage_uri="memory://",
)
```

- Aplicado em: registro, login, troca senha, recuperação
- IA: `require_ia_rate_limit`
- Redis opcional (prod), fallback memory

## 10. File Upload

- `MAX_CONTENT_LENGTH = 16 MiB`
- Erro 413 handler diz "50MB" (mensagem divergente)
- Extensões: txt, pdf, imagens, doc/docx
- `secure_filename` + allowlist
- **SEM inspeção magic bytes**, **SEM MIME real**, **SEM AV/ClamAV**, **SEM sandbox**

## 11. Headers de Segurança

- CSP: nonce por request, `object-src 'none'`, `frame-ancestors 'none'`, `upgrade-insecure-requests`
- **Problema:** `style-src 'unsafe-inline'` (XSS via CSS)
- Headers: `X-Content-Type-Options nosniff`, `X-Frame-Options DENY`, `X-XSS-Protection`, `HSTS`, `Referrer-Policy`, `Permissions-Policy`
- `add_security_headers` registrado como `after_request` — **não confirmado se ativo**

## 12. SQL Injection

- ORM com `filter_by` + binds + `.where`
- Sem padrão amplo de interpolação direta localizado
- Catalogação **não substitui** revisão linha-a-linha

## 13. Multi-Factor Authentication (MFA)

- Modelo: `mfa_enabled: bool` em `User`
- Evento: `MFA_ENABLED`
- Sem TOTP/OTP/recovery codes
- Sem fluxo de ativação
- Sem verificação em login

## 14. Riscos Priorizados

| # | Risco | Severidade | Evidência |
|---|---|:---:|---|
| 1 | SECRET_KEY hardcoded < 32 chars | 🔴 | docker-compose.siap.yml |
| 2 | RBAC não aplicado | 🔴 | 106 perms × 0 endpoints |
| 3 | Tenant via header contradiz JWT | 🔴 | _helpers.py priority |
| 4 | MFA sem implementação | 🔴 | modelo existe, OTP ausente |
| 5 | Audit central não conectado | 🟠 | rotas usam LogAtividade |
| 6 | CSRF não aplicado | 🟠 | helper sem uso |
| 7 | Refresh token apenas no provider AraOS | 🟠 | paralelo |
| 8 | Revogação JWT in-memory | 🟠 | provider AraOS |
| 9 | Uploads sem inspeção | 🟠 | ClamAV ausente |
| 10 | style-src unsafe-inline | 🟢 | CSP |
| 11 | CORS allowlist com duplicação | 🟢 | 192.168.0.104:3000 |
| 12 | Middleware engole exceções | 🟢 | tenant_middleware.py |

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [BACKEND_AUDIT.md](BACKEND_AUDIT.md)
- [DATABASE_AUDIT.md](DATABASE_AUDIT.md)
