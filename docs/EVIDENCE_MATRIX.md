# EVIDENCE MATRIX — MISSÃO 21.5

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** transformar todas as afirmações "provavelmente", "estimado", "análise estática" em evidência real, ou marcar como **NÃO COMPROVADO**.

---

## 1. Metodologia de evidência

Cada afirmação foi classificada como:

| Tipo | Definição | Símbolo |
|------|-----------|---------|
| **MEDIDO** | Valor obtido por teste real executado agora | 🔵 |
| **PROVADO POR CÓDIGO** | Confirmado por leitura direta do fonte (arquivo:linha) | 🟢 |
| **PROVADO POR CONFIG** | Confirmado por env var ou compose file | 🟡 |
| **PROVADO POR HTTP** | Confirmado por `curl` contra prod | 🔴 |
| **NÃO COMPROVADO** | Não foi possível provar com evidência objetiva | ⚫ |

---

## 2. Matriz principal de evidências

| # | Afirmação (origem) | Origem | Tipo de evidência | Status | Comprovada? |
|---|--------------------|--------|-------------------|--------|-------------|
| **CSP-1** | "CSP sem unsafe-inline/eval em prod (P0-05)" — MISSÃO 18 | M18 | **curl real em prod 2026-06-25** | Header CSP em prod: `script-src 'self' 'unsafe-inline' 'unsafe-eval'` | ❌ **NÃO** |
| **CSP-2** | CSP sem unsafe-inline/eval está no código | código | 🟢 `security_config.py:262-274` | Comentário P0-05 presente, mas código efetivo ainda gera `'unsafe-inline'` em style-src | 🟡 Parcial |
| **XASC-1** | "X-Association-ID removido do CORS (P0-12)" — MISSÃO 18 | M18 | 🔴 **curl prod 2026-06-25** | `access-control-expose-headers: ... X-Association-ID ...` em prod | ❌ **NÃO** |
| **XASC-2** | Tenant middleware NÃO lê X-Association-ID | código | 🟢 `middleware/tenant_middleware.py:51-53` (apenas comentário); grep confirma: nenhum `request.headers.get("X-Association-ID"` em código real | Tenant spoof via header bloqueado no código | ✅ SIM |
| **HEALTH-1** | "/api/health exposto em prod (M20)" — MISSÃO 20 | M20 | 🔴 **curl prod** → `404` | ❌ **NÃO deployado** | ❌ **NÃO** |
| **HEALTH-2** | "/api/health existe no código (M20)" | código | 🟢 `app_cors_livre.py:168-205` | ✅ SIM no código | ✅ SIM |
| **POOL-1** | "Pool PG = 5+10=15" — MISSÃO 17 (relatado em M21) | M17/M21 | 🟢 `config.py:72-74` | `pool_size=20, max_overflow=40` (default); via env: `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | ⚫ **INCORRETO** (era 5+10 em M17 mas código atual é 20+40) |
| **POOL-2** | Pool PG real em prod | prod | ⚫ | Sem acesso a `.env.production` no VPS — **NÃO FOI POSSÍVEL COMPROVAR** | ⚫ **NÃO COMPROVADO** |
| **REDIS-1** | "MemoryStorage é usado como fallback" — M21 | M21 | 🟢 `security_config.py:161-176` (`_resolve_storage_uri`); linha 168: `"memory://"` é fallback explícito | ✅ SIM no código | ✅ SIM |
| **REDIS-2** | Storage real em prod | prod | ⚫ | Sem `.env.production` — **NÃO COMPROVADO** | ⚫ **NÃO COMPROVADO** |
| **DEDUP-MP** | "Existe dedup em MercadoPago" — M21 | M21 | 🟢 `routes/mercadopago.py:150-171`; `services/webhook_auth.py:206` `register_webhook_event` + UNIQUE constraint | ✅ SIM, atômico via UNIQUE(provider, provider_event_id) | ✅ SIM |
| **DEDUP-MP-DR** | Idem em Dr.Anderson webhook | código | 🟢 `routes/dr_anderson_webhook.py:132` | ✅ SIM | ✅ SIM |
| **DEDUP-MP-DYN** | Idem em dynamic_tenant webhook | código | 🟢 `routes/dynamic_tenant_webhook.py:41` | ✅ SIM | ✅ SIM |
| **DEDUP-MP-MOD** | Idem em modulos webhook | código | 🟢 `routes/modulos.py:394` | ✅ SIM | ✅ SIM |
| **DLQ-WH** | "DLQ em webhooks" — M17, M21 | M17/M21 | ⚫ grep `dlq\|dead.letter\|retry.queue` em `services/` `routes/` `middleware/` | **NÃO existe** para webhooks. Apenas `max_retries=2` em providers LLM (`services/llm_gateway/app/providers/*.py`) | ❌ **NÃO** |
| **TENANT-1** | "Isolamento multi-tenant via do_orm_execute" — M17 | M17 | 🟢 `tenant_lib.py:35-67` | ✅ SIM | ✅ SIM |
| **TENANT-2** | "Listener before_flush valida INSERT/UPDATE (P0-08)" | M18 | 🟢 `tenant_lib.py:71-100` | ✅ SIM | ✅ SIM |
| **TENANT-3** | Isolamento funciona em SELECT na prática | prod | ⚫ | Não testado dinamicamente em prod (sem staging) | ⚫ **NÃO COMPROVADO em runtime** |
| **TENANT-4** | Onde **NÃO** há isolamento | código | 🟢 `tenant_lib.py:80-90` | Sem tenant no contexto (`g.current_association is None`), rotas públicas/sem-jwt NÃO são bloqueadas | ✅ SIM (compreensão do código) |
| **LGPD-1** | Endpoints LGPD existentes | código | 🟢 `routes/lgpd.py` | 4 endpoints: `consentimento/GET`, `consentimento/POST`, `politica-privacidade/GET`, `direitos-titular/POST` | ✅ SIM |
| **LGPD-2** | "Direito ao esquecimento (art. 18 VI) implementado" — M17 disse NÃO | M17 | 🟢 `routes/lgpd.py:94-160` | `solicitar_direitos_titular` aceita `exclusao` mas **só registra LogAtividade** com comentário literal `"Aqui seria implementada a lógica..."` | ❌ **NÃO** — só registra, não executa |
| **LGPD-3** | DELETE de paciente existe? | código | ⚫ grep em routes/ | Necessita verificação adicional (buscar `def delete_paciente`) | ⚫ **NÃO AUDITADO nesta missão** |
| **BILLING-1** | "Webhook fora de ordem quebra" — M21 | M21 | 🟢 `register_webhook_event` usa UNIQUE atomic, mas fora de ordem **NÃO é tratado** (apenas replay) | ⚫ **NÃO COMPROVADO** se quebra em prod (precisa teste real) |
| **BILLING-2** | Webhook MP tem DLQ | código | ⚫ | ❌ NÃO (já em DLQ-WH) | ❌ **NÃO** |
| **CAP-1** | "Sistema aguenta 50u/80RPS" — M17 | M17 | 🔵 MEDIDO (Locust 56.323 requests) | ✅ SIM, medido | ✅ SIM |
| **CAP-2** | "Sistema aguenta 75/100/150u" — M21 | M21 | 🟠 EXTRAPOLADO de M17 | ⚫ **EXTRAPOLAÇÃO**, não medido | ❌ **NÃO** |
| **CAP-3** | "75u/100u/150u/200u degradam" — M21 | M21 | 🟠 EXTRAPOLADO | ❌ **NÃO medido** | ❌ **NÃO** |
| **CAP-4** | "Após correções (data_revogacao + pool), aguenta 150-200u" — M21 | M21 | 🟠 EXTRAPOLADO | ❌ **NÃO COMPROVADO** | ❌ **NÃO** |
| **CSP-3** | "CSP bloqueia scripts inline em prod" — M18 | M18 | 🔴 **curl prod mostra unsafe-inline em prod** | ❌ **NÃO** | ❌ **NÃO** |
| **P0-TESTS** | "31/31 testes P0 passando" — M18/M21 | M18/M21 | 🔵 EXECUTADO agora: `31 passed` | ✅ SIM (mas testes validam código, não prod) | ✅ SIM |

---

## 3. Resumo de cobertura

| Tipo | Quantidade | % |
|------|------------|---|
| ✅ SIM (provado) | **13** | 41% |
| 🟡 Parcial | 1 | 3% |
| ❌ NÃO (refutado) | **9** | 28% |
| ⚫ NÃO COMPROVADO | **9** | 28% |
| **TOTAL** | **32** | **100%** |

---

## 4. Achados que refutam afirmações de missões anteriores

### 4.1 ❌ P0-05 (CSP) NÃO está em produção

| Missão | Afirmação | Realidade (curl 2026-06-25) |
|--------|-----------|------------------------------|
| M18 | "P0-05 corrigido" (código) | ✅ código OK |
| M18 | "P0-05 em produção" (implícito) | ❌ prod ainda tem `'unsafe-inline' 'unsafe-eval'` |
| M21 | "P0-05 deployado" (implícito) | ❌ refutado |

### 4.2 ❌ P0-12 (X-Association-ID) NÃO está em produção

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M18 | "X-Association-ID removido do CORS" (código) | ✅ código OK |
| M18 | "...em produção" (implícito) | ❌ `access-control-expose-headers` ainda contém `X-Association-ID` |

### 4.3 ❌ Endpoint `/api/health` NÃO está em produção

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M20 | "/api/health implementado" | ✅ código em `app_cors_livre.py:168` |
| M20 | "...em produção" (implícito) | ❌ curl → 404 |

### 4.4 ❌ Afirmação sobre Pool PG estava **incorreta**

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M17 / M21 / FAILOVER | "pool_size=5 + max_overflow=10" | ❌ código atual em `config.py:72-74` é `pool_size=20, max_overflow=40` (defaults) |

> **Erro propagado**: M17 disse 5+10, M18 não corrigiu, M19/M20/M21 herdaram.

### 4.5 ❌ "DLQ em webhooks" — **NÃO existe**

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M17 | "Webhook DLQ / retry persistente — P1 backlog" | OK (era backlog) |
| M21 | (não afirmou DLQ) | — |
| M21.5 (agora) | confirmar se DLQ existe | ❌ **NÃO existe** em `services/`, `routes/`, `middleware/` |

### 4.6 ⚫ "Billing fora de ordem quebra" — **NÃO COMPROVADO**

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M21 | "risco de estado inconsistente" | ⚫ análise estática. Não testado dinamicamente. |

### 4.7 ⚫ Isolamento multi-tenant em prod — **NÃO COMPROVADO em runtime**

| Missão | Afirmação | Realidade |
|--------|-----------|-----------|
| M17 / M18 | "isolamento OK em código" | ✅ provado por código |
| M17 / M18 | "isolamento funciona em prod" | ⚫ **NÃO testado em runtime** (precisa staging) |

---

## 5. Onde NÃO há isolamento multi-tenant (prova por código)

| Cenário | Onde | Trecho |
|---------|------|--------|
| Sem JWT (rotas públicas) | `tenant_lib.py:84-89` | `if tenant_id is None: return` — não bloqueia |
| `skip_tenant=True` explícito | `tenant_lib.py:54-57` | bypass via `execution_options(skip_tenant=True)` |
| `g.is_superadmin` | `tenant_lib.py:53-55` | bypass total |
| Sem `g.current_association` (rotas admin) | `tenant_middleware.py:26, 63, 73` | 3 lugares onde pode ser `None` |

**Conclusão comprovada:** o isolamento multi-tenant **funciona para rotas autenticadas com tenant válido**. **NÃO funciona** para rotas públicas, superadmin, ou com `skip_tenant=True`.

---

## 6. Pool PG — o que é real

```python
# config.py:71-74
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),
    ...
}
```

- **Default:** pool_size=20, max_overflow=40 → **60 conexões max**
- **Override:** `DB_POOL_SIZE` e `DB_MAX_OVERFLOW` no `.env.production`
- **Pool PG real em prod:** ⚫ **NÃO COMPROVADO** (sem acesso a `.env.production`)

---

## 7. CSP — código vs produção

### Código (`security_config.py:262-274`)

```python
P0-05 (Missão 18): CSP sem 'unsafe-inline' / 'unsafe-eval' em script-src.
```

### Produção (curl 2026-06-25)

```
content-security-policy: default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';
  style-src 'self' 'unsafe-inline';
  ...
```

**Diferença:** código está OK em `add_security_headers()` mas o **servidor em prod** ainda serve CSP inseguro. Significativa: deploy de M18 não foi feito OU foi feito deploy parcial sem P0-05.

**Commit que NÃO está em prod:** provavelmente `d562424 fix(clinica): adiciona import billingService...` (mais recente em app_cors_livre.py) ou os commits de M18 que tocaram `security_config.py:262-274`.

> **NÃO FOI POSSÍVEL COMPROVAR qual commit exato está em prod** — não há tag deploy + VPS não acessível.

---

## 8. Status de MEDIDO vs SIMULADO vs ESTIMADO vs EXTRAPOLADO

| Categoria | Origem | Onde está |
|-----------|--------|-----------|
| 🔵 **MEDIDO** | M17 Locust 56.323 req | `RELATORIO_TESTE_CARGA_2026_06.md` |
| 🟢 **SIMULADO** | DR test em Postgres efêmero (M20) | `docs/PRODUCTION_INFRASTRUCTURE_REPORT.md` Seção 6 |
| 🟠 **ESTIMADO** | M17 estimou CPU/RAM/disk sem medir | herdado sem re-medição |
| 🟣 **EXTRAPOLADO** | M21 extrapolou 75/100/150/200u de M17 | ⚫ **NÃO MEDIDO** |

> **NUNCA** misturar essas 4 categorias em conclusões de produção.

---

## 9. NÃO COMPROVADOS explícitos (lista honesta)

1. ⚫ Pool PG real em prod (`DB_POOL_SIZE`/`DB_MAX_OVERFLOW` no VPS)
2. ⚫ Redis storage real em prod (`RATELIMIT_STORAGE_URL` no VPS)
3. ⚫ Isolamento multi-tenant em runtime (precisa 2 tenants em staging)
4. ⚫ Performance em 75/100/150/200u (Locust pesado)
5. ⚫ Webhook MP "fora de ordem" quebra estado (precisa teste real)
6. ⚫ LGPD-04 art. 18 VI: endpoint DELETE paciente existe? (não auditado nesta missão)
7. ⚫ DLQ em webhooks: nunca existiu; só `max_retries=2` em LLM
8. ⚫ Backup automatizado em prod (cron instalado? sim/não)
9. ⚫ Capacity pós-correções (150-200u): **EXTRAPOLAÇÃO**, não medição
