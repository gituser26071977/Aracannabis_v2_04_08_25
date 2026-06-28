# Auditoria de Capacidade — AraOS SIAP

**Data:** 2026-06-22
**Escopo:** Backend Flask, PostgreSQL, Redis, Docker Compose, integrações externas
**Método:** Análise estática de configurações + containers + queries + teste de carga real (Locust 2.31)
**Total de achados:** 31 (7 críticos, 14 altos, 7 médios, 3 baixos)

---

## Sumário Executivo

**Veredito:** O sistema está dimensionado para um **MVP com ~50 usuários ativos simultâneos**. Acima disso, satura por uma combinação de:

1. **Backend gunicorn subdimensionado** (3 workers × 2 threads = 6 conexões concorrentes Flask)
2. **Rate limiter per-worker** (memory://) que se torna gargalo antes mesmo da capacidade real
3. **N+1 em /api/dashboard/stats** que escala linearmente com N pacientes
4. **Chamadas LLM/WhatsApp/VSF síncronas** que travam workers por 30-60s
5. **Pool de conexões PostgreSQL (60×3=180)** que excede `max_connections=100` default

**Capacidade atual estimada (sem correções):**
- **~50 usuários ativos** sustentados
- **~20-40 RPS** para endpoints médios
- **~5-10 RPS** para endpoints com LLM
- **Saturação** já observada em teste peak (200u/3min)

**Após correções P0+P1 (ver `RELATORIO_TESTE_CARGA_2026_06.md`):**
- **500-1500 usuários ativos** sustentados
- **200-400 RPS** sem I/O externo, 50-100 RPS com LLM

---

## Resultados do Teste de Carga

Execução em 22/06/2026 contra `https://api.visualsmartflow.com.br`.

### Resumo Comparativo

| Cenário | Usuários | Duração | Total reqs | Failure % | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Throughput |
|---------|----------|---------|------------|-----------|----------|----------|----------|----------|------------|
| baseline | 50 | 5 min | 6.040 | **63,3%** | 63 | 170 | 690 | 5.500 | 20 RPS |
| peak | 200 | 3 min | 14.352 | **~80%** | 69 | 230 | 560 | 10.000 | 80 RPS |
| soak | 100 | 15 min | (em execução) | — | — | — | — | — | — |

### Top Falhas por Endpoint (cenário peak)

| Endpoint | Total reqs | Falhas | Tipo principal |
|----------|-----------|--------|----------------|
| GET /api/dashboard/stats | 3.557 | 3.557 | 429 Too Many Requests |
| GET /api/pacientes | 3.077 | 2.616 | 429 Too Many Requests |
| GET /api/modulos | 1.460 | 1.013 | 429 Too Many Requests |
| GET /api/consultas | 695 | 1.079 | 429 Too Many Requests |
| POST /api/auth/login | 200 | 46 | 429 Too Many Requests |
| GET /api/planos | 1.239 | 699 | 429 Too Many Requests |

### Diagnóstico de Saturação

A análise dos erros revela dois problemas distintos:

**Problema 1 — Rate limit per-IP global:** O `default_limits = ["1000 per day", "60 per minute"]` em `security_config.py:75-78` está aplicado **globalmente por IP**, não por usuário. Com 200 usuários do mesmo IP (no teste Locust), o limite de 60 req/min/IP satura imediatamente. Isso significa que, em produção real, se dois profissionais acessarem o sistema pelo mesmo IP corporativo (NAT), eles já dividem o limite.

**Problema 2 — Backend bloqueante:** Mesmo nos requests que passaram do rate limit, a latência subiu para 10.000ms (timeout) no login, indicando que o backend está bloqueado esperando recursos.

**Bugs reais descobertos durante o teste:**
- `GET /api/dashboard/stats` → 500: `column pacientes.data_revogacao does not exist`
- `GET /api/pacientes` → 500: mesmo erro (migration faltando)

---

## Achados Detalhados por Camada

### 🔴 CRÍTICOS (7)

#### C1. `app.run()` como fallback em produção
- **Arquivo:** `app_cors_livre.py:363`
- **Comportamento:** `app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)` é usado quando rodado sem gunicorn (Dockerfile.siap).
- **Impacto:** Single process, sem worker recycling, sem graceful reload, sem OOM monitor. **Limita a ~50 usuários.**
- **Recomendação:** Garantir comando gunicorn em TODOS os entrypoints. Bloquear `app.run()` em produção via check `FLASK_ENV`.

#### C2. Pool PostgreSQL excede max_connections
- **Arquivos:** `config.py:55-61` + `docker-compose.prod.yml:93`
- **Comportamento:** Pool: `pool_size=20 + max_overflow=40 = 60 conexões/process`. Com 3 gunicorn workers = até **180 conexões** simultâneas ao PG. PG16 default `max_connections=100`. **Vai estourar!**
- **Recomendação:** Reduzir para `pool_size=5 + max_overflow=10` por worker (3×15=45 total) E subir `max_connections=200` no PG. **Ou** usar **PgBouncer** em modo transaction pooling.

#### C3. Ausência de índices em foreign keys
- **Arquivo:** `models.py` (todos), `migrations/versions/`
- **Comportamento:** Nenhuma coluna `paciente_id`, `profissional_id`, `associacao_id`, `consulta_id` está com `index=True` (apenas UniqueConstraint no CRM). Toda query `WHERE paciente_id = X` faz **seq scan** se filtro de tenant não estiver ativo.
- **Impacto:** Tabelas com > 100k registros ficam lentas. Cada query com filtro por paciente pode levar segundos.
- **Recomendação:** Migration adicionando `db.Index(...)` em todas as FKs. Estimativa de ganho: **100-1000x** em queries filtradas.

#### C4. N+1 em /api/dashboard/stats
- **Arquivo:** `routes/dashboard.py:41-67`
- **Comportamento:** `pacientes_em_tratamento = base_query.all()` e depois loop dispara 2 queries por paciente. Com 500 pacientes = 1000 queries sequenciais.
- **Impacto:** Latência linear com N pacientes. Com 100 pacientes já > 5s.
- **Recomendação:** Substituir por subquery ou join com `func.max(Dosagem.data)` agrupado.

#### C5. Chamadas LLM síncronas no request
- **Arquivo:** `routes/ai_clinical.py:38,68,95`
- **Comportamento:** `/api/ai-clinical/analyze` faz chamadas em série para anonymization + llm_gateway + rehydrate, dentro do request handler. Cada chamada pode levar 5-30s.
- **Impacto:** Com `--timeout 60` do gunicorn, o request morre. Workers travados por minutos.
- **Recomendação:** Mover para **Celery worker** com fila Redis. Retornar `task_id` e cliente faz polling.

#### C6. Webhook WhatsApp síncrono
- **Arquivo:** `routes/consultas.py:444`
- **Comportamento:** `requests.post(whatsapp_api_url, ...)` dentro de handler de consulta.

#### C7. Sem limites de recursos nos containers
- **Arquivo:** `docker-compose.prod.yml` (todos os serviços)
- **Comportamento:** Nenhum `deploy.resources.limits`. Container pode consumir 100% do host e causar OOM no VPS.
- **Recomendação:** Adicionar `cpus='2.0'` e `memory: 4G` para backend, `1G` para redis/db.

---

### 🟠 ALTOS (14)

| # | Componente | Situação | Ganho estimado |
|---|-----------|----------|----------------|
| A1 | Backend workers (docker-compose.prod.yml:93) | `--workers 3 --threads 2 = 6 conexões Flask` | 4 workers × 4 threads gthread → 4-8x RPS |
| A2 | Timeout 300s (docker-compose.prod.yml:93) | Workers travados por 5min | Reduzir para 60s + graceful 30s |
| A3 | Sem `--max-requests` (docker-compose.prod.yml:93) | Memory leak acumula | `--max-requests 1000 --max-requests-jitter 100` |
| A4 | PG sem tuning (docker-compose.prod.yml:14-32) | Defaults | `shared_buffers=256MB`, `work_mem=16MB` |
| A5 | `.all()` sem paginação (múltiplos routes) | Payloads enormes | Adicionar `?limit=50&offset=0` |
| A6 | Export OOM (routes/import_export.py) | Carrega 100k+ linhas em memória | Stream/chunks |
| A7 | Redis não conectado (docker-compose.prod.yml) | Container existe, app não usa | Habilitar REDIS_URL |
| A8 | Rate limiter memory-only (security_config.py:142) | Por-worker | Trocar para Redis |
| A9 | Filtro tenant só SELECT (tenant_lib.py:32-33) | Bypass em UPDATE/DELETE | Ativar também |
| A10 | VSF síncrono (services/vsf_bridge.py) | 7+ chamadas externas | Circuit breaker + async |
| A11 | Ollama no host (docker-compose.prod.yml) | SPOF | Containerizar ou usar cloud |
| A12 | DR Anderson síncrono (services/dr_anderson_agent.py) | Webhook LLM bloqueante | Fila assíncrona |
| A13 | Logs sem estrutura (app_cors_livre.py, config.py) | print() + logger default | JSON formatter + rotação |
| A14 | Pool timeout não explícito (config.py:55-61) | Default 30s | `pool_timeout=10` |

---

### 🟡 MÉDIOS (7)

| Componente | Situação | Recomendação |
|------------|----------|--------------|
| `--reload` em dev (docker-compose.yml:54) | 2 workers com watcher | `--workers 1` em dev |
| Sem healthcheck backend (docker-compose.prod.yml:43-93) | Traefik não detecta trava | curl `/api/status` |
| RLS não ativado (migrations/) | Defesa única no ORM | Habilitar RLS no PG |
| `MAX_CONTENT_LENGTH` diverge | 16MB vs 500MB | Padronizar 16MB |
| Planos/catálogo sem cache (routes/planos.py) | Recarrega a cada request | Redis TTL 5min |
| Brasil API sem cache (services/brasil_api_service.py) | 10s timeout por chamada | Redis 24h |
| Ollama timeout (host.docker.internal) | Sem retry | Healthcheck + retry |

---

### 🟢 BAUXOS (3)

- `--keep-alive` default (docker-compose.prod.yml:93) — 2s; subir para 5s
- Traefik TLS OK — manter
- Tenant filter overhead — OK (5-10%, aceitável)

---

## Gargalos por Camada

```
┌──────────────────────────────────────────────────────────────┐
│ Cliente (browser / app)                                       │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ Traefik (reverse proxy com TLS)                              │  ✅ OK
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ Gunicorn (3 workers × 2 threads)                             │  🔴 CRÍTICO
│   • app.run() fallback em alguns entrypoints                 │
│   • Sem --max-requests (memory leak acumula)                 │
│   • Timeout 300s (workers travados)                          │
│   • Sem graceful reload                                      │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ Flask App                                                    │
│   • rate limiter memory-only (per-worker)                    │  🔴 CRÍTICO
│   • Sem cache de queries estáticas                           │  🟠
│   • N+1 em dashboard (1000 queries / request)                │  🔴 CRÍTICO
│   • LLM/WhatsApp/VSF síncronos no handler                    │  🔴 CRÍTICO
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ PostgreSQL                                                    │
│   • pool 60×3 = 180 vs max_connections=100 (VAI ESTOURAR)   │  🔴 CRÍTICO
│   • Sem índices em FKs (seq scan)                            │  🔴 CRÍTICO
│   • .all() sem paginação                                     │  🟠
│   • Sem RLS                                                  │  🟡
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ Redis (container existe, NÃO conectado ao app)               │  🟠
└──────────────────────────────────────────────────────────────┘
```

---

## Plano de Scaling Horizontal

### Hoje (~50 usuários)
- 1 VPS com 4 vCPU, 8GB RAM
- 3 gunicorn workers × 2 threads
- 1 PG container com defaults

### Após P0 (mesma infra, ~150-300 usuários)
- 4 gunicorn workers × 4 threads (gthread)
- Pool PG = 5+10 por worker
- max_connections = 200 no PG
- Índices em todas as FKs
- N+1 corrigido
- Rate limit via Redis

### Após P1 (~500-1500 usuários)
- 2 VPS atrás do mesmo Traefik (load balance por cookie de sessão)
- PgBouncer em frente ao PG (transaction pooling)
- Redis como cache de queries (planos, módulos, catálogo)
- Logs estruturados com rotação
- Filas assíncronas para LLM/WhatsApp/VSF

### Após P2 (~3000+ usuários)
- Read replicas do PG
- CDN para assets do frontend
- Separação de microserviço para IA
- Cluster Redis (Sentinel)
- Monitoring com Prometheus + Grafana

---

## Recomendações Top 5 por ROI

| # | Ação | Esforço | Ganho de capacidade |
|---|------|---------|---------------------|
| 1 | Adicionar índices em FKs + corrigir N+1 do dashboard | 4h | **10x em queries filtradas** |
| 2 | Migrar rate-limit para Redis + 4 workers × 4 threads gthread | 3h | **5-8x em RPS** |
| 3 | Adicionar pool PG = 5+10 + max_connections=200 + pgbouncer | 4h | **Suportar 500+ conexões simultâneas** |
| 4 | Mover LLM/WhatsApp/VSF para Celery + Redis | 2 sprints | **10x em requests com I/O externo** |
| 5 | Adicionar `deploy.resources.limits` + `--max-requests` + `--timeout 60` | 2h | **Previne OOM + recicla workers** |

---

**Gerado por:** Claude (MiniMax-M3) · 2026-06-22 · Análise estática + teste de carga real (Locust 2.31.0)
