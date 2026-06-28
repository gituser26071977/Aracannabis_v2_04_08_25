# CHAOS_REPORT — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE
**Origem:** M23 FASE 6 — Chaos engineering em staging local

---

## Testes executados

| # | Cenário | Comando | Status |
|---|---------|---------|--------|
| C1 | Redis indisponível | `docker stop siap-redis-staging` | ✅ Executado |
| C2 | Postgres indisponível | `docker stop siap-db-staging` | ✅ Executado |
| C3 | Evolution indisponível | — | ❌ **NÃO COMPROVADO** (serviço não roda em staging local) |
| C4 | Mercado Pago indisponível | — | ❌ **NÃO COMPROVADO** (chamadas externas, não testadas) |
| C5 | OpenAI indisponível | — | ❌ **NÃO COMPROVADO** (chamadas externas, não testadas) |

---

## C1 — Redis indisponível

**Sequência:**
1. Baseline: `/api/health` retorna 503 (já em degraded — bug de REDIS_URL ausente)
2. `docker stop siap-redis-staging` (t = 0)
3. `GET /api/health` (t +3s)
4. `docker start siap-redis-staging` (t +3s)
5. `GET /api/health` (t +8s)

**Resultado:**
| Momento | Status code | Body |
|---------|-------------|------|
| Antes | 503 | `redis: fail: ConnectionError` |
| Durante outage | **500** | `Internal Server Error` (stack trace) |
| Depois (Redis up) | 503 | `redis: fail: ConnectionError` |

**Análise:**
- ⚠️ **Durante outage: 500** (bug). Esperado seria 503 sustentado.
- ❌ **Depois: ainda 503** mesmo com Redis respondendo (`redis-cli ping` → PONG).
- **Causa do "fail: ConnectionError" persistente:** `app_cors_livre.py:186` faz `getattr(cfg, "REDIS_URL", None) or "redis://localhost:6379/0"`. Como `REDIS_URL=None` no config, ele tenta conectar em **localhost** (não em `siap-redis-staging`). Bug de configuração, não bug de chaos.

**Recuperação:** sistema **NÃO recuperou sozinho** após restart do Redis. Necessário restart do backend (mesmo assim continuou falhando porque o bug é no REDIS_URL).

**Perda de dados:** nenhuma observada.

---

## C2 — Postgres indisponível

**Sequência:**
1. Baseline: `/api/health` 503
2. `docker stop siap-db-staging` (t = 0)
3. `GET /api/health` (t +3s)
4. `docker start siap-db-staging` (t +3s)
5. `GET /api/health` (t +8s)

**Resultado:**
| Momento | Status code | Body |
|---------|-------------|------|
| Antes | 503 | degraded |
| Durante outage | **503** | `postgres: fail: OperationalError, redis: fail: ConnectionError` (payload estruturado!) |
| Depois | 503 | degraded (Redis ainda falhando — mesmo bug C1) |

**Análise:**
- ✅ **Comportamento CORRETO**: retorna 503 com payload estruturado mostrando qual dependência está down.
- ✅ **Recuperação**: Postgres recuperou após restart (status `ok` no body).
- ⚠️ Redis ainda broken por causa do BUG-001.

**Retry:** o backend tem `pool_pre_ping=True` (config.py:74) — permite reconectar após restart sem restart do backend.

**Perda de dados:** nenhuma observada (transações curtas, autocommit).

---

## Conclusões

| Comportamento | Status |
|---------------|--------|
| Detecção de falha | ✅ Funciona (503 com payload) |
| Recuperação automática Postgres | ✅ Funciona (pool_pre_ping) |
| Recuperação automática Redis | ❌ **NÃO funciona** se REDIS_URL ausente |
| 500 vs 503 sob falha | ⚠️ Redis outage causou 500 (deveria ser 503) |
| Retry transparente | ✅ Visível no body (`status: degraded`) |
| Perda de dados | ✅ Nenhuma |

## Bugs REAIS encontrados

| # | Bug | Evidência | Severidade |
|---|-----|-----------|------------|
| P1-C1 | `/api/health` retorna 500 sob Redis outage (deveria ser 503) | log stack trace | P1 |
| P1-C2 | `app_cors_livre.py:186` fallback `redis://localhost` quando REDIS_URL ausente | config.get_config().REDIS_URL = None | P1 |
| P3-C3 | `.env.staging.example` sem REDIS_URL | grep → vazio | P3 |

## Serviços externos (NÃO testados)

**C3 (Evolution), C4 (Mercado Pago), C5 (OpenAI):**

NÃO foram testados em staging local porque:
- Evolution é serviço externo (não roda em compose local)
- Mercado Pago é API externa (chamada real requer sandbox token)
- OpenAI é API externa (chamadas reais via litellm)

**Recomendação:** agendar teste de chaos contra esses serviços em staging público (VPS real). NÃO COMPROVADO nesta missão.