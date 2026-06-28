# PERFORMANCE_EVIDENCE — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE
**Origem:** M23 FASE 5 — Locust progressivo (5/10/25/50/75/100 usuários)

**Ambiente:** staging local (Docker compose v2, 4 containers, gunicorn workers=1 threads=2)

---

## Metodologia

- **Ferramenta:** Locust 2.44.4 (instalado dentro do container `siap-backend-staging`)
- **Duração por teste:** 30 segundos
- **Ramp-up:** 10 usuários/s
- **Endpoints exercitados:**
  - `POST /api/auth/login`
  - `GET /api/pacientes/`
  - `GET /api/consultas/`
  - `GET /api/dashboard/stats`
  - `GET /api/planos/meu-plano`
  - `GET /api/status`

## Resultados agregados

| Usuários | Total reqs | Falhas | Taxa falha | p50 (ms) | p95 (ms) | p99 (ms) | Throughput (req/s) |
|----------|------------|--------|------------|----------|----------|----------|---------------------|
| 5        | 79         | 0      | **0.0%**   | 22       | 39       | 63       | 2.68                |
| 10       | 25         | 10     | **40.0%**  | 69       | —        | 123      | 0.83 (parcial)      |
| 25       | 46         | 31     | **67.4%**  | 39       | —        | 134      | 1.53                |
| 50       | 47         | 33     | **70.2%**  | 35       | —        | 120      | 1.57                |
| 75       | 44         | 32     | **72.7%**  | 28       | —        | 106      | 1.47                |
| 100      | 1373       | 1191   | **86.7%**  | 6        | 32       | 99       | 47.29 (mas 86% 429) |

## Causa raiz das falhas

`load_100_failures.csv`:
```
POST /api/auth/login       CatchResponseError('login: 429')         95
GET  /api/planos/meu-plano HTTPError('401 Client Error: UNAUTHORIZED')  102
GET  /api/planos/meu-plano HTTPError('429 Client Error: TOO MANY REQUESTS') 79
GET  /api/dashboard/stats  HTTPError('429 Client Error: TOO MANY REQUESTS') 82
GET  /api/consultas        HTTPError('429 Client Error: TOO MANY REQUESTS') 137
GET  /api/pacientes        HTTPError('429 Client Error: TOO MANY REQUESTS') 396
GET  /api/dashboard/stats  HTTPError('401 Client Error: UNAUTHORIZED')  95
GET  /api/consultas        HTTPError('401 Client Error: UNAUTHORIZED')  125
```

**Diagnóstico:**
- **429 = rate-limit** ativado. `security_config.py:108`: `LOGIN_RATE_LIMIT = "10 per minute"`.
- **401 = JWT expirou/inválido** após primeiro 429. Como `RATELIMIT_STORAGE_URL` é `None` em staging, Flask-Limiter cai em `memory://` — mas isso é por WORKER, e como há só 1 worker, funciona dentro dele. O 401 surge quando o login é bloqueado (429), o `access_token` não é setado e os GETs subsequentes falham.

## Métricas de recursos (durante pico 100u)

```
NAME                   CPU %     MEM USAGE / LIMIT
siap-backend-staging   0.03%     286.2MiB / 33.11GiB
siap-db-staging        0.62%     25.87MiB / 33.11GiB
siap-redis-staging     0.53%     4.086MiB / 33.11GiB
```

**CPU 0.03% é evidência CRÍTICA:** o sistema **não está saturado de CPU**. Está saturado de **fila de rate-limit**. Aumentar workers não resolve; o gargalo é o limite de 10 logins/min imposto pelo código.

## Conclusão objetiva

| Pergunta | Resposta MEDIDA |
|----------|------------------|
| Sistema aguenta 5 médicos? | **SIM** (0% falha em 5u) |
| Sistema aguenta 10 médicos? | **NÃO** (40% falha já em 10u) |
| Sistema aguenta 25 médicos? | **NÃO** (67% falha) |
| Sistema aguenta 50 médicos? | **NÃO** (70% falha) |
| Sistema aguenta 75 médicos? | **NÃO** (73% falha) |
| Sistema aguenta 100 médicos? | **NÃO** (87% falha) |

## Maior gargalo encontrado

**RATE-LIMIT (LOGIN_RATE_LIMIT = 10/min)** é o gargalo. Não é CPU, RAM, I/O, DB ou Redis. É uma **decisão de código** que limita o login a 10 por minuto **POR WORKER** (memory:// fallback). Em produção multi-worker o limite fica ainda mais permissivo (cada worker tem seu próprio contador), mas em staging com 1 worker satura imediato.

**Comprovação:** 5u → 0 falha, 10u → 40% falha. A linha de quebra está entre 5 e 10 médicos simultâneos fazendo login.

## Bugs REAIS encontrados durante carga

| # | Bug | Evidência | Severidade |
|---|-----|-----------|------------|
| P1-B1 | Rate-limit memory:// falha em multi-worker | 401 após 429 em login | P1 |
| P1-B2 | REDIS_URL ausente em .env.staging | config.get_config().REDIS_URL = None | P1 |
| P3-B3 | Login smoke.sh divergente do endpoint real | `routes/auth.py:90` espera `email`/`senha`, não `identifier`/`password` | P3 |

## CSVs de evidência

- `reports/load_m23/load_5_stats.csv`
- `reports/load_m23/load_10_stats.csv` + `load_10_failures.csv`
- `reports/load_m23/load_25_stats.csv` + `load_25_failures.csv`
- `reports/load_m23/load_50_stats.csv` + `load_50_failures.csv`
- `reports/load_m23/load_75_stats.csv` + `load_75_failures.csv`
- `reports/load_m23/load_100_stats.csv` + `load_100_failures.csv`

## Capacidade medida (NÃO extrapolada)

| Métrica | Valor |
|---------|-------|
| **Throughput sustentável SEM falha** | **2.68 req/s** (5 usuários) |
| Throughput com 50% falha | ~1.5 req/s |
| p95 com 5u | 39ms |
| p95 com 100u | 32ms (mas com 87% falha) |

> **NOTA:** estes números são do staging local (gunicorn workers=1). Em produção com mais workers e REDIS_URL configurado, **NÃO se aplica**. Extrapolações são vedadas por instrução da missão.