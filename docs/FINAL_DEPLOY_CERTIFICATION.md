# FINAL_DEPLOY_CERTIFICATION — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE
**Origem:** M23 — consolidação de 9 fases de staging + certificação final

---

## Respondendo as 7 perguntas obrigatórias

### 1. O staging foi realmente certificado?

**NÃO.**

- **Provisionamento (FASE 1):** ✅ Containers up (4/4) em 257s
- **Pipeline CI (FASE 2):** ⚠️ **NÃO EXECUTADO** (não há runner GitHub Actions acessível)
- **Playwright (FASE 3):** ❌ **NÃO EXECUTADO** (Playwright não instalado)
- **Lighthouse (FASE 4):** ❌ **NÃO EXECUTADO** (Lighthouse CLI não instalado; staging público inacessível)
- **Carga progressiva (FASE 5):** ✅ EXECUTADO (6 níveis: 5/10/25/50/75/100u)
- **Chaos engineering (FASE 6):** ✅ EXECUTADO (Redis + Postgres down)
- **Disaster Recovery (FASE 7):** ✅ EXECUTADO (Postgres efêmero, restore validado)
- **Observabilidade (FASE 8):** ⚠️ Parcial — `/api/health` testado; Prometheus/Grafana NÃO deployados
- **Smoke completo (FASE 9):** ✅ EXECUTADO (16 endpoints, 10 OK)

**Bloqueadores identificados que impedem certificação:**

| # | Bloqueador | Origem |
|---|------------|--------|
| BUG-001 | REDIS_URL ausente em `.env.staging.example` | FASE 1, 8 |
| BUG-002 | Login espera `email`/`senha`, smoke.sh envia `identifier`/`password` | FASE 1 |
| BUG-003 | gunicorn `--workers 1` no staging | FASE 1 |
| BUG-PERF | LOGIN_RATE_LIMIT=10/min satura com 10 usuários | FASE 5 |
| BUG-CHAOS | `/api/health` retorna 500 sob Redis outage | FASE 6 |
| EXT-001 | Playwright, Lighthouse, GitHub Actions runners, staging público — não acessíveis | FASE 2-4 |

---

### 2. Qual o maior gargalo encontrado?

**RATE-LIMIT NO LOGIN** (`LOGIN_RATE_LIMIT = "10 per minute"` em `security_config.py:108`).

**Evidência objetiva:**
- 5u → 0% falha, throughput 2.68 req/s
- 10u → 40% falha
- 25u → 67% falha
- 50u → 70% falha
- 100u → 87% falha
- CPU durante pico: **0.03%** (sistema não está saturado de recursos — está saturado de **fila do rate-limit**)

**Causa raiz:** Flask-Limiter com fallback `memory://` por processo. Em produção multi-worker o limite multiplica, mas em staging com 1 worker, satura imediato.

**Correção (NÃO aplicada):** configurar `REDIS_URL` em `.env.staging` para Flask-Limiter compartilhar contador entre workers.

---

### 3. Quantos bugs REAIS apareceram?

**5 bugs reais**, todos com evidência objetiva:

| # | Bug | Severidade | Evidência |
|---|-----|------------|-----------|
| BUG-001 | REDIS_URL ausente em `.env.staging.example` | P1 | `config.get_config().REDIS_URL = None` |
| BUG-002 | Login endpoint diverge da documentação smoke | P3 | `routes/auth.py:90` espera `email`/`senha` |
| BUG-003 | gunicorn `--workers 1` em staging | P1 | `docker-compose.staging.yml:75` |
| BUG-004 | `/api/prescricoes/` retorna 404 | P3 | path correto é `/gerar` ou `/paciente/<id>` |
| BUG-005 | `/api/health` retorna 500 sob Redis outage | P1 | stack trace em log |
| BUG-006 | `Load test` em staging local revela falha >50% já em 25u | P1 | `reports/load_m23/load_25_failures.csv` |

---

### 4. Qual a capacidade medida (não extrapolada)?

| Métrica | Valor MEDIDO |
|---------|---------------|
| **Throughput sustentável SEM falha** | **2.68 req/s** (5 usuários simultâneos) |
| p95 com 5u | 39ms |
| p95 com 10u | indisponível (40% falha antes) |
| CPU pico | 0.03% (ocioso) |
| RAM backend | 286MB |
| RAM DB | 26MB |
| RAM Redis | 4MB |

> **NÃO EXTRAPOLADO.** Valores válidos apenas para staging local com workers=1 e REDIS_URL=None.

---

### 5. O sistema suporta 5 médicos reais?

**SIM, com ressalvas.**

Baseado em:
- 5 usuários simultâneos → 0% falha (load_5_stats.csv)
- p95 = 39ms (aceitável)
- Login funciona, pacientes, consultas, billing, LGPD, dashboard — todos retornam 200

**Ressalvas:**
- 1 falha em 16 endpoints (`/api/health` 503 — bug conhecido, não impede operação)
- 4 endpoints retornam 4xx (esperado, webhooks sem assinatura, prescrição/cannabis com payload errado)
- Sem REDIS_URL → rate-limit funciona mas não compartilha entre workers

**Veredito:** para **5 médicos usando em horário comercial (8h/dia, sem pico)**: **SIM**.

---

### 6. O sistema suporta 50 médicos reais?

**NÃO (com configuração atual).**

Evidência:
- 50u → 70% falha (load_50_failures.csv)
- Principal causa: 429 (rate-limit) + 401 (token inválido após login bloqueado)

**O que precisaria mudar:**
- Aumentar `LOGIN_RATE_LIMIT` para ≥60/min (vs 10/min atual)
- Configurar `REDIS_URL` para Flask-Limiter compartilhar entre workers
- Aumentar `--workers` de 1 para 3+ em staging (reflete produção)

**Sem essas mudanças, capacidade de pico é ≤5 médicos.**

---

### 7. O sistema suporta 100 médicos reais?

**NÃO.**

- 100u → 87% falha
- Mesmas causas: rate-limit + token expirado

**Capacidade de pico absoluta: ~5 médicos** com a configuração staging atual.

**Em produção** (workers=3+, REDIS_URL configurado, rate-limit compartilhado), há indicação de que seria melhor — **mas não foi testado nesta missão**.

---

## Decisão final

| Cenário | Veredicto |
|---------|-----------|
| **Staging local** | ❌ NÃO certificado — 5 bugs bloqueadores |
| **Staging público** (URL real com DNS+SSL) | ❌ NÃO provisionado nesta missão |
| **Produção** | ❌ NÃO certificado (depende de staging público certificado) |

## Resumo executivo

> **NÃO É SEGURO FAZER DEPLOY DE 5 MÉDICOS REAIS COM O STAGING ATUAL.**
>
> O sistema suporta tecnicamente login/paciente/consulta/billing/LGPD em ambiente de 5 usuários, mas:
>
> 1. `/api/health` reporta 503 mesmo quando tudo está up (alarme falso)
> 2. Sob carga de 10+ usuários, 40-87% dos requests falham por rate-limit
> 3. Playwright/Lighthouse/pipeline CI não foram executados (ambiente limitado)
> 4. BUG-001 (REDIS_URL ausente) é trivial de corrigir mas impede staging de ser representativo de produção

## Recomendações (NÃO aplicadas)

1. Adicionar `REDIS_URL=redis://siap-redis-staging:6379/0` em `.env.staging.example`
2. Aumentar `--workers` em staging de 1 para 3
3. Aumentar `LOGIN_RATE_LIMIT` de `10 per minute` para `60 per minute`
4. Corrigir `/api/health` para retornar 503 (não 500) sob Redis outage
5. Provisionar staging público (VPS + Traefik + DNS + SSL)
6. Instalar Playwright + Lighthouse em CI
7. Re-executar M23 após correções

## Restrições respeitadas

- ✅ Nenhum backend/frontend/banco/billing/RBAC/auth/LGPD alterado
- ✅ Nenhuma feature nova criada
- ✅ Nenhum commit/push/PR
- ✅ Toda conclusão baseada em evidência objetiva
- ✅ O que não foi possível executar foi marcado como **NÃO COMPROVADO**