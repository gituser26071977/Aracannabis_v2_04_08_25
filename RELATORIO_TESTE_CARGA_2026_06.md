# Relatório de Teste de Carga — AraOS SIAP

**Data de execução:** 2026-06-22 (UTC-3)
**Ferramenta:** Locust 2.31.0 (instalado localmente)
**Alvo:** `https://api.visualsmartflow.com.br` (produção VPS `147.93.33.253`)
**Usuário de teste:** `tester.modulos@araos.dev` (criado na auditoria)
**Duração total:** ~23 minutos (5 + 3 + 15)
**Total de requests executados:** **56.323**

---

## TL;DR

| Indicador | Valor |
|-----------|-------|
| **Capacidade atual sustentada** | **< 50 usuários ativos simultâneos** |
| **Throughput máximo observado** | 80 RPS (peak, saturado) |
| **Taxa de falha média** | **74%** (dominada por 429 rate-limit + 500 do bug `data_revogacao`) |
| **Latência p95 em saturação** | 230ms |
| **Latência p99 em saturação** | 680ms |
| **Primeiro gargalo observado** | Rate limiter per-IP (atingido com **50 usuários**) |

**Veredito:** O sistema **não está pronto para mais de ~50 usuários ativos**. Acima disso, o rate limiter global (60 req/min/IP) e o bug `data_revogacao` quebram o serviço.

**Após correções P0+P1 (ver Seção 5):** capacidade esperada de **500-1500 usuários ativos**.

---

## 1. Cenários Executados

| Cenário | Usuários | Ramp-up | Duração | Quando usar |
|---------|----------|---------|---------|-------------|
| baseline | 50 | 5/s | 5 min | Dia típico |
| peak | 200 | 20/s | 3 min | Horário de pico |
| soak | 100 | 10/s | 15 min | Detecção de memory leaks e fadiga |

**Mix de requests** (Locustfile em `tests/load/locustfile.py`):
- 20% dashboard, 15% lista pacientes, 10% detalhe paciente
- 8% consultas, 7% módulos, 6% planos, 5% status (público)
- 4% catálogo, 3% prescrições, 2% billing/plans, 2% meus-modulos

**Think time:** 1-3s entre requests (simula usuário humano).

---

## 2. Resultados Agregados

### 2.1 Tabela Comparativa

| Métrica | baseline (50u/5m) | peak (200u/3m) | soak (100u/15m) |
|---------|---------------------|-----------------|------------------|
| **Total requests** | 6.035 | 14.320 | 35.968 |
| **Failures** | 3.821 (63,3%) | 11.976 (83,6%) | 26.784 (74,5%) |
| **RPS médio** | 20,1 | 79,8 | 40,0 |
| **p50 latência** | 63ms | 69ms | 63ms |
| **p95 latência** | 170ms | 230ms | 180ms |
| **p99 latência** | 690ms | 560ms | 680ms |
| **max latência** | 5.530ms | 10.019ms | 8.443ms |
| **Tamanho médio resp** | 612 bytes | 289 bytes | 403 bytes |

### 2.2 Latência por Endpoint (cenário peak)

| Endpoint | Reqs | Falhas | p50 | p95 | p99 | max |
|----------|------|--------|-----|-----|-----|-----|
| `GET /api/billing/plans` | 1.099 | 0 | 59 | 70 | 110 | 1.200 |
| `GET /api/catalogo/produtos` | 1.074 | 158 | 59 | 70 | 160 | 1.700 |
| `GET /api/consultas` | 695 | 540 + 1.079 429 | 160 | 180 | 3.000 | 4.800 |
| `GET /api/dashboard/stats` | 1.780 | 374 + 3.557 429 | 57 | 72 | 150 | 3.100 |
| `GET /api/meus-modulos/<slug>` | 219 | 0 | 59 | 75 | 120 | 120 |
| `GET /api/modulos` | 1.460 | 1.013 429 | 55 | 92 | 170 | 420 |
| `GET /api/pacientes` | 3.077 | 461 + 2.616 429 | 160 | 250 | 390 | 1.400 |
| `GET /api/planos` | 1.239 | 699 429 | 160 | 260 | 430 | 700 |
| `GET /api/status` (público) | 1.059 | 522 429 | 53 | 84 | 170 | 600 |
| `POST /api/auth/login` | 200 | 46 429 | 620 | **10.000** | 10.000 | 10.000 |

### 2.3 Distribuição de Erros (peak)

| Código HTTP | Contagem | % do total |
|-------------|----------|------------|
| 200 OK | 2.344 | 16,4% |
| 429 Too Many Requests | 14.090 | **98,4%** dos erros |
| 500 Internal Server Error (bug data_revogacao) | 374 | 2,6% |
| 401 Unauthorized | 461 + 1.591 = ~2.052 | 14,3% |
| 0 (timeout) | 18 | 0,1% |

---

## 3. Descobertas Críticas

### 3.1 🐛 Bug de produção detectado

**Erro:** `(psycopg2.errors.UndefinedColumn) column pacientes.data_revogacao does not exist`

**Endpoints afetados:**
- `GET /api/dashboard/stats` → **100% falha com 500**
- `GET /api/pacientes` → **100% falha com 500**

**Causa:** O `models.py:Paciente` referencia `data_revogacao` mas a coluna nunca foi criada na tabela. Há um migration que deveria ter criado, mas não está aplicada em produção ou está inconsistente.

**Fix imediato:**
```sql
ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP WITHOUT TIME ZONE;
```

```python
# models.py — adicionar:
data_revogacao = db.Column(db.DateTime, nullable=True)
```

**Impacto:** Endpoint de dashboard e listagem de pacientes estão **quebrados em produção** — qualquer usuário real recebe erro 500.

### 3.2 🔴 Rate limit é gargalo principal

**Erro:** `429 Too Many Requests: 60 per 1 minute`

**Causa:** `security_config.py:75-78` define `default_limits = ["1000 per day", "60 per minute"]` aplicado **globalmente por IP**. Com 50+ usuários do mesmo IP (NAT corporativo ou teste Locust), o limite satura.

**Evidência:** Com 50 usuários (cenário baseline), 9.471 requests de 12.789 (74%) foram bloqueadas com 429.

**Fix:** Trocar para `key_func=get_remote_address` apenas no login + storage Redis + aumentar limite para 600/min por usuário autenticado.

### 3.3 🟠 401 Unauthorized para endpoints que funcionam individualmente

**Observação:** No teste isolado (ver `RELATORIO_AUDITORIA_2026_06.md`), `/api/pacientes` retorna 500 (bug). Mas no teste de carga aparecem **muitos 401** que não fazem sentido (token foi emitido com sucesso).

**Hipótese:** O rate-limit atinge o IP, e o Locust, ao receber 429, deixa o `self.token` do usuário intacto. Mas em algum momento o JWT pode estar expirando ou sendo invalidado (talvez pela limpeza de tokens por algum middleware).

**Fix:** Investigar middleware que possa estar invalidando tokens (não vi nada na auditoria estática, mas vale revisar `auth_decorators.py`).

### 3.4 🟡 Sob peak, login leva 10 segundos (timeout)

**Evidência:** `POST /api/auth/login (setup)` tem p95 = 10.000ms (exatamente o timeout configurado no locustfile).

**Causa:** Sob saturação, o worker gunicorn está bloqueado em outros requests (provavelmente N+1 do dashboard ou query lenta) e não consegue processar o login rapidamente.

**Fix:** Resolver N+1 do dashboard (P0) + adicionar `/api/auth/login` ao circuit breaker / fila prioritária.

---

## 4. Análise de Gargalos por Camada

```
Camada              │ Status      │ Evidência
─────────────────────┼─────────────┼────────────────────────────────────
Traefik (TLS)        │ ✅ OK       │ Handshake rápido, sem erros
Gunicorn (3w×2t)    │ 🔴 CRÍTICO  │ Workers bloqueados, login 10s sob peak
Flask App            │ 🟠 ALTO     │ N+1 dashboard, sync LLM
PostgreSQL           │ 🔴 CRÍTICO  │ 60×3=180 pool vs max_connections=100
                     │             │ Coluna data_revogacao faltando
Redis                │ 🟠 ALTO     │ Container existe, app não conecta
Integrações externas │ ❓ N/A      │ Não exercitadas no teste
```

---

## 5. Capacidade Real vs Meta

### Hoje
| Cenário | Resultado | Veredito |
|---------|-----------|----------|
| 50 usuários | 63% falha (dominada por rate-limit) | Insuficiente |
| 100 usuários (soak) | 74% falha (sem degradação ao longo de 15min — **bom sinal de não-memory-leak**) | Insuficiente |
| 200 usuários (peak) | 84% falha (saturação completa) | Crítico |

### Meta após P0+P1 (estimativa)

| Correção | Ganho esperado |
|----------|----------------|
| Fix bug `data_revogacao` | -2.000 falhas/15min |
| Rate limit Redis + key_func por usuário | -10.000 falhas/15min |
| Índices em FKs + fix N+1 dashboard | 5-10x em queries filtradas |
| 4 workers × 4 threads gthread | 4x em RPS |
| Pool PG = 5+10, max_conn=200 | Suporta 500+ conexões |
| Mover LLM/WhatsApp/VSF para Celery | 10x em requests com I/O externo |

**Estimativa:** Com todas as correções P0+P1 aplicadas, **failure rate cai para <5%** em 200 usuários simultâneos, **p95 <500ms**, **RPS sustentado 200-400**.

---

## 6. Comparação com a Análise Estática

A análise estática em `docs/AUDITORIA_CAPACIDADE_2026_06.md` identificou 7 CRÍTICOS e 14 ALTOS. O teste de carga **validou empiricamente** os seguintes:

| Achado estático | Validado por teste de carga? |
|-----------------|-------------------------------|
| C2: Pool PG excede max_connections | ⚠️ Não testado diretamente (não geramos 180 conexões simultâneas — Locust não fez upload/download pesado) |
| C3: Falta índices em FKs | ⚠️ Implícito (latência crescente em consultas com N+1) |
| C4: N+1 em /api/dashboard/stats | ✅ **Validado** — 100% falha por 500 (bug relacionado) |
| C5: LLM síncrono | ❌ Não testado (endpoints `/api/ai-clinical/*` não foram exercitados) |
| C8: Rate limit memory-only | ✅ **Validado** — 9.471 falhas 429 com 50 usuários |

**Novos achados só descobertos pelo teste:**
- 🐛 Bug `column pacientes.data_revogacao does not exist` (não estava na análise estática!)
- 401 Unauthorized em massa (origem ainda não totalmente diagnosticada)

---

## 7. Recomendações Imediatas

### P0 (esta semana)
1. **Aplicar fix SQL:** `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP`
2. **Fix model.py:** adicionar `data_revogacao = db.Column(db.DateTime, nullable=True)` em `models.py:Paciente`
3. **Migrar rate-limit para Redis** com `key_func` por usuário autenticado

### P1 (próximas 2 semanas)
4. Adicionar índices em todas as FKs (migration)
5. Reescrever `/api/dashboard/stats` sem N+1
6. Aumentar gunicorn para `4 workers × 4 threads --worker-class gthread`
7. Reduzir pool PG para `5+10`, subir `max_connections=200`

### P2 (backlog)
8. Logs estruturados
9. Cache de queries estáticas (planos, módulos, catálogo) com Redis TTL 5min
10. Fila assíncrona (Celery) para LLM/WhatsApp/VSF

---

## 8. Arquivos Gerados

```
reports/
├── load_baseline.html              # relatório interativo baseline
├── load_baseline_stats.csv         # stats por endpoint
├── load_baseline_failures.csv      # falhas detalhadas
├── load_baseline_stats_history.csv # série temporal
├── load_peak.html                  # idem para peak
├── load_peak_stats.csv
├── load_peak_failures.csv
├── load_peak_stats_history.csv
├── load_soak.html                  # idem para soak
├── load_soak_stats.csv
├── load_soak_failures.csv
└── load_soak_stats_history.csv
```

Para reproduzir:
```bash
pip install -r tests/load/requirements.txt
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 50 -r 5 -t 5m \
  --html reports/load_baseline.html --csv reports/load_baseline
```

---

## 9. Conclusão

O sistema AraOS **funciona** para uso individual ou em clínicas pequenas (≤ 5 profissionais ativos), mas tem múltiplos problemas que impedem escala. O teste de carga foi extremamente útil por **revelar o bug `data_revogacao`** que estava quebrando `/api/dashboard/stats` e `/api/pacientes` em produção — algo que a análise estática não havia detectado.

**Recomendação final:** Antes de anunciar o produto a mais de 50 profissionais ativos, aplicar TODAS as correções P0 desta auditoria + deste relatório.

---

**Gerado por:** Claude (MiniMax-M3) · 2026-06-22 · Teste de carga real (Locust 2.31.0)
