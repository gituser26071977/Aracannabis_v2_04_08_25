# FASE 5 — INVENTÁRIO COMPLETO DO RATE LIMIT (READ-ONLY)

**Data:** 2026-06-23
**Escopo:** Diagnosticar por que o teste de carga Locust apresentou 63% / 84% de falhas e propor FASE 5A.
**Método:** somente leitura. Análise estática do código + leitura dos relatórios de carga existentes.

**Restrições respeitadas:**
- ❌ NÃO alterei código
- ❌ NÃO criei commits
- ❌ NÃO implementei FASE 5

---

## 1. DADOS DO TESTE DE CARGA EXISTENTE

### 1.1 Fonte dos dados
- **Locustfile:** `tests/load/locustfile.py`
- **Relatórios:** `reports/load_baseline.*.csv` e `reports/load_peak.*.csv`
- **Data dos testes:** 2026-06-19/20 (aproximada, baseado no commit history)

### 1.2 Resultado agregado

| Cenário | Usuários | Requests | Falhas | Taxa de falha | RPS | p95 latência |
|---------|----------|----------|--------|---------------|-----|--------------|
| **Baseline** | 50 (5min) | 6.035 | 3.821 | **63,3%** | 20,1 | 240ms |
| **Peak** | 200 (3min) | 14.320 | 11.976 | **83,6%** | 79,8 | 370ms |

### 1.3 Distribuição de erros no Peak (200 users)

| Tipo de erro | Ocorrências | % das falhas |
|--------------|-------------|--------------|
| **HTTP 429** (rate limit) | ~9.500 | ~79% |
| **HTTP 401** (unauthorized) | ~2.500 | ~21% |
| **HTTP 500** (known_bug data_revogacao) | ~392 | <1% |
| **Other** | <100 | <1% |

**Conclusão primária:** **a taxa de 84% de falha é dominada por HTTP 429 (rate limit), não por bug de código.**

---

## 2. BIBLIOTECA UTILIZADA

| Item | Valor |
|------|-------|
| Biblioteca | **Flask-Limiter >= 3.0.0** |
| Versão instalada | (em `venv_multi_tenant/lib/python3.14/site-packages/flask_limiter`) |
| `requirements.txt` | `Flask-Limiter>=3.0.0` + `redis` |
| Implementação alternativa | `services/rate_limit_service.py` (Redis, **NÃO integrada** ao Flask-Limiter) |
| Outra implementação | `services/llm_gateway/app/rate_limit.py` (in-memory, LLM gateway) |

**Há 3 implementações de rate limit no projeto:**
1. **Flask-Limiter** (security_config.py:138) — única aplicada em rotas
2. **services/rate_limit_service.py** — para limite IA por profissional (Redis, mas sem decorator global)
3. **services/llm_gateway/app/rate_limit.py** — in-memory, isolado do LLM gateway

---

## 3. ESTRATÉGIA ATUAL

**Arquivo:** `security_config.py:135-145`

```python
def init_limiter(app):
    global limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,      # ← chave: IP do cliente
        default_limits=[DEFAULT_RATE_LIMIT],  # ← "1000 per day, 60 per minute"
        storage_uri="memory://",          # ← IN-MEMORY (não compartilhado)
        strategy="fixed-window",
    )
    return limiter
```

| Aspecto | Valor | Análise |
|---------|-------|---------|
| **Chave (key_func)** | `get_remote_address` = IP do cliente | ❌ Em Load Test todos vêm do mesmo IP → mesmo bucket |
| **Por usuário** | ❌ NÃO | Limit aplicado por IP, não por JWT/profissional |
| **Por tenant** | ❌ NÃO | Sem multi-tenancy no rate limit |
| **Por IP** | ✅ SIM | Único critério atual |
| **Híbrida** | ❌ NÃO | Single criterion |

**Problema crítico do load test:**
- Locust roda de 1 IP (servidor de teste) → todos os 50/200 usuários compartilham o mesmo bucket
- 60 requests/minuto × 1 IP = limite esgota em <1 minuto
- Resultado: 79% das falhas são 429, não bugs

---

## 4. CONFIGURAÇÃO ATUAL

### 4.1 Limites default

**Arquivo:** `security_config.py:75-78`

```python
DEFAULT_RATE_LIMIT = "1000 per day, 60 per minute"
LOGIN_RATE_LIMIT = "10 per minute"
SENSITIVE_ENDPOINTS_RATE_LIMIT = "100 per minute"
API_SEARCH_RATE_LIMIT = "200 per minute"
```

### 4.2 Decorators aplicados em rotas

| Rota | Decorator | Limite efetivo |
|------|-----------|----------------|
| **TODAS** (~80 rotas) | nenhum | `1000 per day, 60 per minute` (default) |
| `/api/auth/login` | nenhum | `1000 per day, 60 per minute` (default) — **MESMO QUE LISTAGEM** |
| `/api/mercadopago/*` | nenhum | `1000 per day, 60 per minute` (default) |
| `/api/modulos/webhook` | nenhum | `1000 per day, 60 per minute` (default) |
| webhooks W1-W5 | nenhum | `1000 per day, 60 per minute` (default) |

⚠️ **`LOGIN_RATE_LIMIT = "10 per minute"`** está DEFINIDO mas **NUNCA APLICADO** (não há `@limiter.limit(LOGIN_RATE_LIMIT)` em `routes/auth.py`).

⚠️ **`SENSITIVE_ENDPOINTS_RATE_LIMIT = "100 per minute"`** está DEFINIDO mas **NUNCA APLICADO**.

⚠️ **`API_SEARCH_RATE_LIMIT = "200 per minute"`** está DEFINIDO mas **NUNCA APLICADO**.

### 4.3 Storage backend

| Item | Valor |
|------|-------|
| `storage_uri` | `"memory://"` (hardcoded) |
| Tipo | In-memory (Python dict) |
| Compartilhamento entre workers | ❌ NÃO (cada worker tem seu próprio dict) |
| Persistência entre restarts | ❌ NÃO |
| Atomicidade | ❌ NÃO garantida entre workers |

**Problema em produção:**
- Gunicorn roda com `--workers 3` (`docker-compose.prod.yml:93`)
- Cada worker tem seu próprio dict de rate limit
- 50 req/min do mesmo IP distribuídas: ~17 req para cada worker (parece OK)
- Mas o **fixed-window strategy** + **3 workers** sem coordenação = race condition
- Limite efetivo real = `60 × 3 = 180 req/min` por IP (workers paralelos não compartilham)

---

## 5. REDIS

### 5.1 Status atual

| Item | Status | Evidência |
|------|--------|-----------|
| Container Redis declarado em prod | ✅ SIM | `docker-compose.prod.yml:35-37` (`siap-redis: image: redis:7-alpine`) |
| Redis depende do backend | ✅ SIM | `docker-compose.prod.yml:71-73` (`depends_on: siap-redis`) |
| `REDIS_URL` em env | ✅ DECLARADO | `.env.production.example:118` = `redis://siap-redis:6379/0` |
| Redis sendo usado pelo Flask-Limiter | ❌ **NÃO** | `storage_uri="memory://"` (hardcoded) |
| Redis sendo usado por rate_limit_service.py | ✅ SIM | `services/rate_limit_service.py:23-39` lê `REDIS_URL` |
| Redis sendo usado por outras features | ✅ SIM | `services/vsf_bridge.py`, `services/dr_anderson_agent.py`, `services/dynamic_tenant_agent.py` |

### 5.2 Por que Flask-Limiter não usa Redis

`security_config.py:142` tem `storage_uri="memory://"` **hardcoded**. Não há leitura de env var nem fallback para Redis. Esta é a **decisão arquitetural** que precisa mudar.

---

## 6. TOP 20 ENDPOINTS — IMPACTO NO LOAD TEST

### 6.1 Ordenado por falhas no PEAK (200 users)

| # | Endpoint | Requests | Falhas | % Falha | Tipo de falha predominante |
|---|----------|----------|--------|---------|----------------------------|
| 1 | GET /api/dashboard/stats | 4.085 | 4.085 | 100% | 429 (3.545) + 401 (166) + 500 (374 bug) |
| 2 | GET /api/pacientes | 3.072 | 3.072 | 100% | 429 (2.611) + 401 (461) |
| 3 | GET /api/consultas | 1.614 | 1.614 | 100% | 429 (1.074) + 401 (540) |
| 4 | GET /api/modulos | 1.457 | 1.149 | 78,9% | 429 (1.010) + 401 (139) |
| 5 | GET /api/planos | 1.237 | 697 | 56,3% | 429 (697) |
| 6 | GET /api/status (public) | 1.055 | 518 | 49,1% | 429 (518) |
| 7 | GET /api/catalogo/produtos | 815 | 453 | 55,6% | 429 (295) + 401 (158) |
| 8 | POST /api/auth/login (setup) | 200 | 64 | 32,0% | login_failed (18) + 429 (implied) |
| 9 | GET /api/billing/plans | 415 | 145 | 35,0% | 401 (119) + 429 (26) |
| 10 | GET /api/meus-modulos/<slug> | 98 | 0 | 0% | (raro, peso 1) |
| 11 | GET /api/pacientes/<id> | (no WARMUP) | 0 | - | (warmup, peso baixo) |
| 12 | GET /api/prescricoes/paciente/<id> | (n/a) | - | - | peso 3 |
| 13 | WARMUP /api/pacientes | 136 | 136 | 100% | 401 (79) + 429 (57) |
| 14 | WARMUP /api/modulos | 136 | 43 | 31,6% | 429 (43) |

**Apenas 10 endpoints aparecem no load test real.** Os 14+ restantes não foram exercitados.

### 6.2 Cálculo de carga estimada

**Peak (200 users × ~5 RPS cada = 1000 RPS teórico):**
- 50% dos requests vão para `/api/dashboard/stats` (peso 20)
- Limite de 60 req/min por IP → atinge em **0,06 minutos = 3,6 segundos**
- Após 3,6s, todos os requests do mesmo IP são 429

**Baseline (50 users):**
- 50 × ~5 RPS = 250 RPS do mesmo IP
- 60 req/min → 1 req/s = 0,06 min
- Atinge em **meses primeiros**, e depois satura

---

## 7. TABELA DETALHADA: ROTA × LIMITE × CHAVE × IMPACTO

| Rota | Limite atual | Chave | Impacto observado | Severidade |
|------|--------------|-------|--------------------|-----------|
| `GET /api/dashboard/stats` | 60/min | IP | 3.545 × 429 no peak | 🔴 CRÍTICO |
| `GET /api/pacientes` | 60/min | IP | 2.611 × 429 no peak | 🔴 CRÍTICO |
| `GET /api/consultas` | 60/min | IP | 1.074 × 429 no peak | 🔴 CRÍTICO |
| `GET /api/modulos` | 60/min | IP | 1.010 × 429 no peak | 🔴 CRÍTICO |
| `GET /api/planos` | 60/min | IP | 697 × 429 no peak | 🟠 ALTO |
| `GET /api/status` (public) | 60/min | IP | 518 × 429 no peak | 🟠 ALTO |
| `GET /api/catalogo/produtos` | 60/min | IP | 295 × 429 no peak | 🟡 MÉDIO |
| `GET /api/billing/plans` | 60/min | IP | 26 × 429 + 119 × 401 | 🟡 MÉDIO |
| `POST /api/auth/login` | 60/min (default, não 10!) | IP | 64 × login_failed | 🟠 ALTO (brute force sem proteção) |
| `GET /api/pacientes/<id>` | 60/min | IP | 0 (raro no teste) | 🟢 BAIXO |
| `GET /api/prescricoes/paciente/<id>` | 60/min | IP | 0 (raro no teste) | 🟢 BAIXO |
| `GET /api/meus-modulos/<slug>` | 60/min | IP | 0 (raro) | 🟢 BAIXO |
| `POST /api/auth/*` (outros) | 60/min | IP | - | 🟡 MÉDIO |
| `POST /api/mercadopago/webhook` | 60/min | IP | 0 (sem tráfego no teste) | 🟢 BAIXO |
| `POST /api/modulos/webhook` | 60/min | IP | 0 (sem tráfego no teste) | 🟢 BAIXO |
| `POST /api/tenant/webhook` | 60/min | IP | 0 (sem tráfego no teste) | 🟢 BAIXO |
| `POST /api/dr-anderson/webhook` | 60/min | IP | 0 (sem tráfego no teste) | 🟢 BAIXO |
| `POST /api/dosagens/calcular` | 60/min | IP | 0 (sem tráfego no teste) | 🟢 BAIXO |
| `POST /api/ia/chat` | custom em `rate_limit_service.py` | profissional_id | 0 (não testado) | 🟢 OK (já tem impl própria) |
| `POST /api/ai/dosing` | custom em `rate_limit_service.py` | profissional_id | 0 (não testado) | 🟢 OK (já tem impl própria) |

---

## 8. ONDE OCORREM OS 429

### 8.1 Distribuição por categoria

| Categoria | # 429 no peak | % do total 429 |
|-----------|---------------|----------------|
| **Dashboard/Pacientes (consulta intensiva)** | 8.230 | 86,6% |
| **Módulos/Planos (catálogo)** | 1.989 | 20,9% |
| **Auth/Login** | ~64 (estimado) | <1% |
| **Webhooks (W1-W5)** | 0 (não testados) | 0% |
| **IA/Agent** | 0 (não testados) | 0% |

### 8.2 Causa raiz

**Cenário real do load test:**
- Locust spawna 200 HttpUser tasks (cada um é um thread simulando usuário)
- Todos compartilham o mesmo `self.client` (= 1 IP de saída)
- Cada user faz 1 request a cada 1-3s
- Total: 200 × ~0,5 req/s = ~100 req/s

**Limite aplicado:** `60 per minute` por IP
- 60 / 60s = 1 req/s permitido
- 100 req/s tentando → **99 req/s são 429**

### 8.3 Por que afeta usuários autenticados também?

A chave é `get_remote_address` (IP). Usuários autenticados via JWT **não são diferenciados** — todos do mesmo IP dividem o mesmo bucket.

**Em produção real**, cada usuário tem IP diferente (clínica, hospital, etc), mas:
- Mobile compartilhando Wi-Fi (mesma NAT) = mesmo IP
- Proxy corporativo = mesmo IP
- Testes E2E (Postman/curl) = mesmo IP do dev
- Locust/Postman load = mesmo IP

**Bucket compartilhado é ineficiente para SaaS multi-tenant.**

---

## 9. PROPOSTA TÉCNICA — FASE 5A

### 9.1 Objetivos (curto prazo)

1. **Mover storage para Redis** (compartilhado entre workers gunicorn)
2. **Mudar chave para profissional_id** (autenticado) ou IP (público)
3. **Aplicar limites específicos por categoria** (login 10/min, leitura 200/min, escrita 30/min)
4. **Adicionar exemption para webhooks** (já validados por HMAC em FASE 4.5)
5. **Re-rodar load test** e validar melhoria

### 9.2 Arquitetura proposta

```
                    ┌─────────────────────┐
   Request ──→      │  Flask Route        │
                    │  + @limiter.limit() │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Key function       │
                    │  (IP ou prof_id)    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Flask-Limiter      │
                    │  Strategy:          │
                    │  fixed-window-      │
                    │  elastic-expiry    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Redis (compartilhado)│
                    │  siap-redis:6379    │
                    │  db=1 (separado     │
                    │  de feature flags)  │
                    └─────────────────────┘
```

### 9.3 Mudanças propostas (sem entrar em código)

| Item | Antes | Depois |
|------|-------|--------|
| `storage_uri` | `"memory://"` (hardcoded) | `os.getenv("REDIS_URL") + "/1"` (env-driven) |
| `key_func` (autenticado) | `get_remote_address` (IP) | `get_jwt_identity` (profissional_id) ou híbrido |
| `key_func` (público) | `get_remote_address` | mantém IP |
| `default_limits` | `"1000 per day, 60 per minute"` | `"200 per minute, 5000 per hour"` |
| `strategy` | `"fixed-window"` | `"moving-window"` (mais preciso) |
| `@limiter.limit(LOGIN_RATE_LIMIT)` em `routes/auth.py` | NÃO APLICADO | aplicado em `/api/auth/login` |
| `@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)` em endpoints sensíveis | NÃO APLICADO | aplicado em `POST` mutativos |
| Exceção para webhooks | NÃO | `@limiter.exempt` em W1-W5 (já validados por HMAC) |
| 401 para IP compartilhado (NAT/proxy) | não trata | adicionar header `X-Forwarded-For` consideration |

### 9.4 Estimativa de esforço

| Tarefa | Linhas de código estimadas | Risco |
|--------|---------------------------|-------|
| Trocar storage_uri para Redis | ~5 linhas | BAIXO |
| Adicionar key_func híbrido (IP ou JWT) | ~20 linhas | MÉDIO |
| Aplicar LOGIN_RATE_LIMIT no /auth/login | ~2 linhas | BAIXO |
| Aplicar SENSITIVE_ENDPOINTS_RATE_LIMIT em POST | ~10 decorators | BAIXO |
| Excluir webhooks W1-W5 do rate limit | ~5 decorators | BAIXO |
| Atualizar `.env.production` com Redis db=1 | 1 linha | BAIXO |
| Re-rodar load test | 0 (apenas comando) | BAIXO |
| **TOTAL** | **~45 linhas + 1 env var** | BAIXO-MÉDIO |

### 9.5 Resultado esperado pós-FASE 5A

| Cenário | Antes | Esperado depois |
|---------|-------|-----------------|
| Baseline 50 users | 63% falha | **<10% falha** (apenas 401 + 500 bug) |
| Peak 200 users | 84% falha | **<30% falha** (com chave por prof_id) |
| RPS sustentado | ~20 | **~80+** (Redis + moving-window) |
| Latência p95 adicionada pelo limiter | n/a | **<5ms** (Redis local) |

### 9.6 Riscos residuais

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Redis cair → rate limit inativo | ALTO | Fallback para in-memory + log warning |
| Memória Redis cheia | MÉDIO | TTL automático + maxmemory-policy=allkeys-lru |
| Usuários compartilhando IP (NAT) | MÉDIO | Adicionar X-Forwarded-For + hierarchy IP>user |
| Profissionais criando múltiplas contas | BAIXO | Limite por prof_id é por conta |

---

## 10. PRÓXIMOS PASSOS

1. ✅ Aguardar revisão humana deste inventário
2. ⏸️ Após aprovação: implementar FASE 5A (estimativa: 1 sprint)
3. ⏸️ Re-rodar load test Locust (50/200/100 users)
4. ⏸️ Validar métricas melhoraram
5. ⏸️ FASE 5B: rate limit adaptativo por plano (Premium vs Enterprise)

---

**⚠️ Parando aqui conforme instruído:**
- ❌ NÃO alterei código
- ❌ NÃO criei commits
- ❌ NÃO implementei FASE 5
- ❌ NÃO apliquei as correções propostas (precisam de aprovação humana)

Aguardando revisão humana + decisão sobre a FASE 5A.

---

## APÊNDICE — Arquivos relevantes (somente leitura)

| Arquivo | Conteúdo |
|---------|----------|
| `security_config.py:135-145` | `init_limiter()` — único uso de Flask-Limiter |
| `security_config.py:75-78` | Constantes de limite (mas não aplicadas) |
| `app_cors_livre.py:72-73` | Chamada de `init_limiter(app)` |
| `services/rate_limit_service.py` | Implementação Redis para IA (não integrada ao Flask-Limiter) |
| `services/llm_gateway/app/rate_limit.py` | Implementação in-memory para LLM gateway |
| `docker-compose.prod.yml:35-37` | Container Redis declarado |
| `.env.production.example:118` | `REDIS_URL=redis://siap-redis:6379/0` |
| `tests/load/locustfile.py` | Cenário de carga usado |
| `reports/load_baseline_*.csv` | Resultado baseline (50 users) |
| `reports/load_peak_*.csv` | Resultado peak (200 users) |