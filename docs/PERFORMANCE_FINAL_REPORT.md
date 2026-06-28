# PERFORMANCE FINAL REPORT — MISSÃO 17

**Data:** 2026-06-25
**Modo:** EXECUTE (consolidação de `RELATORIO_TESTE_CARGA_2026_06.md` + auditoria estática)

---

## 1. Resumo executivo

A capacidade do AraOS foi medida em **22/06/2026** via Locust contra o VPS de produção `https://api.visualsmartflow.com.br`. Os resultados **NÃO foram repetidos** nesta missão (modo somente leitura), mas os dados de `RELATORIO_TESTE_CARGA_2026_06.md` são a fonte primária.

> **Capacidade REAL sustentada hoje: < 50 usuários simultâneos.**
> **Capacidade projetada pós-correções P0+P1: 500-1500 usuários.**

---

## 2. Cenários medidos (referência)

| Cenário | Usuários | Ramp-up | Duração | Requests | Falhas | RPS | p95 | p99 |
|---------|----------|---------|---------|----------|--------|-----|-----|-----|
| **baseline** | 50 | 5/s | 5 min | 6.035 | 63,3% | 20,1 | 170ms | 690ms |
| **peak** | 200 | 20/s | 3 min | 14.320 | 83,6% | 79,8 | 230ms | 560ms |
| **soak** | 100 | 10/s | 15 min | 35.968 | 74,5% | 40,0 | 180ms | 680ms |

**Total: 56.323 requests, taxa de falha média 74%** (dominada por 429 rate-limit + 500 do bug `data_revogacao`).

---

## 3. Gargalos identificados (em ordem de severidade)

### 🔴 Gargalo #1 — PostgreSQL: 60 conexões por worker × 3 workers vs max_connections=100

**Arquivo:** `config.py:55-61`
**Evidência:**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),       # 20 base
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "40")),  # +40 overflow
    # 3 workers × 60 = 180 vs max_connections=100 → 80% saturação
}
```

**Impacto:** Com 200 usuários (peak), pool fica saturado, requests bloqueiam até 10s.

### 🔴 Gargalo #2 — Rate limiter global: 60 req/min/IP

**Arquivo:** `security_config.py:107` (FASE 5A já corrigiu para 200/min + Redis)
**Status:** ✅ **CORRIGIDO** (FASE 5A entregue)
**Impacto residual:** Sob Locust com mesmo IP, ainda satura em 200+ usuários.

### 🟠 Gargalo #3 — N+1 em `/api/dashboard/stats`

**Arquivo:** `routes/dashboard.py:41-67`
**Evidência (RELATÓRIO_TESTE_CARGA):** `GET /api/dashboard/stats` tem p99 = 3.100ms, 374+3.557 429 em peak.
**Causa:** Query sem `group_by`/`subquery`, faz 1 round-trip por paciente.

### 🟠 Gargalo #4 — Frontend bundle = 646 kB gzipped

**Arquivo:** `frontend/build/static/js/main.c19367e7.js`
**Causa:** Single-bundle, sem code-splitting. CRA + Material-UI completo.
**Impacto:** First contentful paint (FCP) estimado >3s em 3G.

### 🟠 Gargalo #5 — `routes/ai_chat_simples.py` chamada LLM síncrona

**Arquivo:** `routes/ai_chat_simples.py:189` (`speech_to_text`)
**Evidência:** Sem fila RQ, sem circuit breaker. Bloqueia worker gunicorn por até 60s.
**Impacto:** 1 request LLM pesado paralisa 1 worker (1/3 da capacidade).

### 🟡 Gargalo #6 — `routes/ai_clinical.py` sem cache de prompt

**Arquivo:** `routes/ai_clinical.py`
**Evidência:** Cada chamada anonimiza o paciente de novo.
**Impacto:** +800ms por chamada.

### 🟡 Gargalo #7 — `routes/mercadopago.py:119-159` webhook bloqueante

**Arquivo:** `routes/mercadopago.py`
**Evidência:** Webhook chama DB, envia email, responde MP — tudo síncrono.

### 🟡 Gargalo #8 — `routes/import_export.py:228` lê arquivo inteiro em RAM

**Arquivo:** `routes/import_export.py:228`
**Evidência:** `temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=...)` + lê tudo.
**Impacto:** 1 import de 50MB = 1 worker travado.

### 🟡 Gargalo #9 — Faltam índices em FKs

**Arquivo:** `migrations/` (auditoria)
**Evidência:** Tabelas como `exames.paciente_id`, `consultas.paciente_id`, `evolucoes.paciente_id` sem `db.Index` explícito.
**Impacto:** Cada `WHERE paciente_id = X` faz seq scan.

### 🟡 Gargalo #10 — `routes/dashboard.py:41-67` com `count(*)` em subquery

**Arquivo:** `routes/dashboard.py`
**Impacto:** COUNT() em 1M+ rows sem índice = O(N).

---

## 4. Estimativa de capacidade por carga

| Config | Usuários sustentados | RPS | p95 | Bloqueador |
|--------|---------------------|-----|-----|------------|
| **Atual (medido)** | **< 50** | **80** | **230ms** | Rate-limit + DB pool + N+1 |
| **Após P0 (FASE 5A + data_revogacao)** | 200-300 | 250 | 200ms | DB pool ainda |
| **Após P0+P1 (N+1, índices, RQ)** | 500-800 | 600 | 150ms | Worker count |
| **Após P0+P1+P2 (cache, CDN, read replica)** | 1500-3000 | 1500 | 100ms | Infra |

---

## 5. Respondendo a pergunta 3

> **3. Qual é a capacidade REAL medida?**
> **< 50 usuários simultâneos sustentados, 80 RPS de pico, 230ms p95, 74% de falha sob saturação.**
>
> Medido em 22/06/2026 com Locust 2.31.0 contra `https://api.visualsmartflow.com.br`. Relatório completo: `RELATORIO_TESTE_CARGA_2026_06.md`.

---

## 6. Respondendo a pergunta 6 (parcial)

> **6. O sistema sobreviveria à perda de Redis, Evolution e MercadoPago?**
> Ver `docs/DISASTER_RECOVERY_REPORT.md` para resposta completa.
>
> **Resumo:**
> - **Redis off:** Rate-limit cai para `memory://` (warning em `security_config.py:197-201`). Workers perdem coordenação. Sistema **sobrevive** mas com rate-limit inconsistente.
> - **Evolution off:** Lembretes WhatsApp falham; sistema não tem retry persistente confirmado. **Falha silenciosa** (sem DLQ verificado).
> - **MercadoPago off:** Webhook 503 → billing em estado inconsistente. Sem retry persistente verificado.
> - **Gemini off:** Chat IA 500. Bloqueia UI mas não o resto.

---

## 7. Recomendações (NÃO executadas)

1. **Aplicar P0 do relatório de carga**: índices em FKs, fix `data_revogacao`, N+1 dashboard
2. **Aumentar pool PostgreSQL** para `pool_size=40, max_overflow=80` (3w × 120 = 360 vs 500 max_connections)
3. **Code-splitting no frontend** (React.lazy em páginas)
4. **Fila RQ** para LLM, WhatsApp, MercadoPago
5. **Cache de prompt anonimizado** em Redis
6. **Read replica** para dashboard (consultas pesadas)
7. **CDN** para bundle estático (Cloudflare já tem no domínio, mas falta `cache-control: public, immutable`)
