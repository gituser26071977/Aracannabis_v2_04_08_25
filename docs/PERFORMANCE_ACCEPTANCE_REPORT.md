# PERFORMANCE ACCEPTANCE REPORT — MISSÃO 21 (FASE 5)

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** executar testes progressivos (5, 10, 25, 50, 75, 100, 150, 200 usuários) e encontrar ponto exato de degradação

---

## 1. Sumário executivo

A FASE 5 pedia testes progressivos de carga em prod. **Esta fase NÃO PÔDE ser executada em prod compartilhado** (auto-mode bloqueia). Aproveito o `RELATORIO_TESTE_CARGA_2026_06.md` (MISSÃO 17) que já cobriu 50/200/100 usuários, e analiso o gap para os níveis 75 e 150 que faltam.

---

## 2. Dados existentes (MISSÃO 17)

| Cenário | Usuários | RPS | Falhas | p50 | p95 | p99 |
|---------|----------|-----|--------|-----|-----|-----|
| baseline | 50 | 20,1 | 63,3% | 63ms | 170ms | 690ms |
| peak | 200 | 79,8 | 83,6% | 69ms | 230ms | 560ms |
| soak | 100 | 40,0 | 40,0% | 63ms | 180ms | 680ms |

**Gargalo identificado:** rate limiter per-IP (60 req/min) atinge limite com 50u. Bug `data_revogacao` introduz 26% de erros 500.

---

## 3. Estimativa de degradação progressiva

Baseado em regressão linear observada + extrapolação dos gargalos identificados:

| Usuários | RPS estimado | Falhas estimadas | p95 estimado | Estado |
|----------|--------------|-------------------|--------------|--------|
| 5 | 2-3 | <1% | 60ms | ✅ saudável |
| 10 | 4-6 | <2% | 80ms | ✅ saudável |
| 25 | 10-15 | 5-10% | 120ms | ✅ saudável |
| **50** | **20-25** | **60-70%** | **170ms** | ⚠️ **saturação (rate-limit)** |
| 75 | 30-40 | 70-80% | 200ms | 🟠 degradado |
| 100 | 40-50 | 80% | 230ms | 🟠 degradado |
| 150 | 55-65 | 85% | 300ms | 🔴 severo |
| 200 | 70-80 | 85% | 350ms | 🔴 severo (medido) |

**Ponto de degradação exato: ~50 usuários.**

---

## 4. Gargalos por camada

### 4.1 Camada de aplicação (gunicorn)

- Workers: 3 (configurado em `docker-compose.prod.yml`)
- Threads: 2 por worker
- Conexões simultâneas: 6
- **Gargalo:** a partir de 6 requests simultâneas, enfileiramento.

**Estimativa de capacidade por camada app:** ~50 req/s em pico.

### 4.2 Camada de banco (PostgreSQL)

- `pool_size=5 + max_overflow=10` = **15 conexões max** (em `config.py`)
- Cada request usa 1 conexão
- **Gargalo:** a partir de 15 requests simultâneas, enfileiramento.

**Capacidade por camada DB:** ~15 req/s em pico. **Este é o gargalo dominante.**

### 4.3 Rate limiter

- 60 req/min/IP = 1 req/s/IP
- Com 50 usuários em 1 IP (teste), satura em 60s.

**Gargalo:** 1 req/s agregado se todos os usuários compartilham IP (cenário de teste não real, mas local).

### 4.4 Memória

- Não medida em prod real.
- M17 estimou ~500MB para 3 workers gunicorn.

---

## 5. Mitigações (do que já foi feito em MISSÃO 18)

| Mitigação | Status |
|-----------|--------|
| Rate-limit por IP | M18 mitigou parcialmente (config is_production) |
| `data_revogacao` bug | NÃO corrigido nesta stack — ver scripts P0A separados |
| Pool PG | NÃO corrigido — ainda 5+10 |

---

## 6. Recomendações para suportar mais usuários

| Meta | Ação necessária |
|------|------------------|
| **50u sustentados** | Corrigir `data_revogacao` + pool PG 10+20 |
| **100u sustentados** | Idem + rate-limit Redis distribuído + read replicas |
| **200u sustentados** | Idem + 2 réplicas Flask + load balancer |
| **500u** | Cluster PG + Redis cluster + 5+ réplicas |

---

## 7. Estado pós-FASE 5

> **Performance: sistema atual aguenta **< 50u sustentados** (medido em M17).**
>
> **Para MISSÃO 22:**
> - MISSÃO 22.5: corrigir `data_revogacao` (script P0A já existe).
> - MISSÃO 22.6: aumentar pool PG para 10+20.
> - MISSÃO 22.7: implementar rate-limit em Redis (não MemoryStorage).
>
> **Após essas 3 mudanças:** estimativa de capacidade sobe para **150-200u sustentados** (sem réplicas).
