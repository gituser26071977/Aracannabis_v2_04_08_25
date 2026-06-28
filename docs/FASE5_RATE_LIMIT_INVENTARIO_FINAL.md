# FASE 5 — INVENTÁRIO COMPLETO DO RATE LIMIT (READ-ONLY)

**Data:** 2026-06-23
**Método:** somente leitura. Análise estática do código + leitura dos relatórios de carga existentes.

**Restrições respeitadas:**
- ❌ NÃO alterei código
- ❌ NÃO criei commits
- ❌ NÃO implementei FASE 5

---

## 0. POR QUE 63% / 84% DE FALHAS

**A causa raiz é o rate limit, NÃO bugs de código.**

Distribuição de erros no Peak (200 users):

| Tipo | Ocorrências | % |
|------|-------------|---|
| **HTTP 429** (rate limit) | ~9.500 | **~79%** |
| HTTP 401 (unauthorized) | ~2.500 | ~21% |
| HTTP 500 (bug data_revogacao) | ~392 | <1% |

---

## 1. BIBLIOTECA UTILIZADA

| Item | Valor |
|------|-------|
| Biblioteca principal | **Flask-Limiter >= 3.0.0** (`security_config.py:138`) |
| `requirements.txt` | `Flask-Limiter>=3.0.0` + `redis` |
| Outras implementações | `services/rate_limit_service.py` (Redis, IA-only); `services/llm_gateway/app/rate_limit.py` (in-memory, isolado) |

---

## 2. ESTRATÉGIA ATUAL

```python
# security_config.py:138-145
limiter = Limiter(
    app=app,
    key_func=get_remote_address,      # ← IP do cliente
    default_limits=[DEFAULT_RATE_LIMIT],  # ← "1000 per day, 60 per minute"
    storage_uri="memory://",          # ← in-memory
    strategy="fixed-window",
)
```

| Aspecto | Valor | Análise |
|---------|-------|---------|
| Chave | `get_remote_address` (IP) | ❌ Load test = 1 IP = mesmo bucket |
| Por usuário (JWT) | ❌ NÃO | Limit aplicado por IP, não por profissional |
| Por tenant | ❌ NÃO | Sem multi-tenancy |
| Híbrida | ❌ NÃO | |

**Problema crítico do load test:** 200 HttpUser tasks do Locust = mesmo IP de saída → 60 req/min ÷ 60s = 1 req/s permitido vs 100 req/s tentando → 99 req/s = 429.

---

## 3. CONFIGURAÇÃO ATUAL

### 3.1 Limites definidos (mas não aplicados)

```python
# security_config.py:75-78
DEFAULT_RATE_LIMIT = "1000 per day, 60 per minute"
LOGIN_RATE_LIMIT = "10 per minute"            # ← NUNCA aplicado
SENSITIVE_ENDPOINTS_RATE_LIMIT = "100 per minute"   # ← NUNCA aplicado
API_SEARCH_RATE_LIMIT = "200 per minute"      # ← NUNCA aplicado
```

### 3.2 Decorators aplicados

**Zero `@limiter.limit(...)` em qualquer rota.** Apenas o default `1000/day, 60/min` aplica-se a todas as ~80 rotas.

### 3.3 Storage

| Item | Valor |
|------|-------|
| `storage_uri` | `"memory://"` (hardcoded) |
| Compartilhamento entre workers | ❌ NÃO (gunicorn 3 workers) |
| Persistência entre restarts | ❌ NÃO |
| Atomicidade | ❌ NÃO (race condition entre workers) |

---

## 4. REDIS

| Item | Status | Evidência |
|------|--------|-----------|
| Container Redis em prod | ✅ | `docker-compose.prod.yml:35-37` (`redis:7-alpine`) |
| `REDIS_URL` declarado | ✅ | `.env.production.example:118` = `redis://siap-redis:6379/0` |
| Usado pelo Flask-Limiter | ❌ **NÃO** | `storage_uri="memory://"` hardcoded |
| Usado por outras features | ✅ | `vsf_bridge.py`, `dr_anderson_agent.py`, `dynamic_tenant_agent.py`, `rate_limit_service.py` |

**Decisão arquitetural pendente:** trocar `storage_uri` para `REDIS_URL`.

---

## 5. TOP 10 ENDPOINTS NO LOAD TEST (Peak 200 users)

| # | Endpoint | Requests | Falhas | % Falha | Tipo predominante |
|---|----------|----------|--------|---------|-------------------|
| 1 | GET /api/dashboard/stats | 4.085 | 4.085 | 100% | 3.545 × 429 + 500 (bug) |
| 2 | GET /api/pacientes | 3.072 | 3.072 | 100% | 2.611 × 429 + 401 |
| 3 | GET /api/consultas | 1.614 | 1.614 | 100% | 1.074 × 429 + 401 |
| 4 | GET /api/modulos | 1.457 | 1.149 | 78,9% | 1.010 × 429 + 401 |
| 5 | GET /api/planos | 1.237 | 697 | 56,3% | 697 × 429 |
| 6 | GET /api/status (public) | 1.055 | 518 | 49,1% | 518 × 429 |
| 7 | GET /api/catalogo/produtos | 815 | 453 | 55,6% | 295 × 429 + 401 |
| 8 | POST /api/auth/login | 200 | 64 | 32% | login_failed (brute force sem proteção) |
| 9 | GET /api/billing/plans | 415 | 145 | 35% | 119 × 401 + 26 × 429 |
| 10 | GET /api/meus-modulos/<slug> | 98 | 0 | 0% | (raro, peso 1) |

---

## 6. TABELA: ROTA × LIMITE × CHAVE × IMPACTO

| Rota | Limite atual | Chave | Impacto observado | Severidade |
|------|--------------|-------|--------------------|-----------|
| GET /api/dashboard/stats | 60/min (default) | IP | 3.545 × 429 no peak | 🔴 CRÍTICO |
| GET /api/pacientes | 60/min | IP | 2.611 × 429 | 🔴 CRÍTICO |
| GET /api/consultas | 60/min | IP | 1.074 × 429 | 🔴 CRÍTICO |
| GET /api/modulos | 60/min | IP | 1.010 × 429 | 🔴 CRÍTICO |
| GET /api/planos | 60/min | IP | 697 × 429 | 🟠 ALTO |
| GET /api/status (public) | 60/min | IP | 518 × 429 | 🟠 ALTO |
| GET /api/catalogo/produtos | 60/min | IP | 295 × 429 | 🟡 MÉDIO |
| GET /api/billing/plans | 60/min | IP | 26 × 429 | 🟡 MÉDIO |
| POST /api/auth/login | **60/min (default, não 10!)** | IP | 64 falhas | 🟠 ALTO (brute force) |
| GET /api/pacientes/<id> | 60/min | IP | 0 (raro) | 🟢 BAIXO |
| GET /api/prescricoes/paciente/<id> | 60/min | IP | 0 (raro) | 🟢 BAIXO |
| GET /api/meus-modulos/<slug> | 60/min | IP | 0 (raro) | 🟢 BAIXO |
| POST /api/mercadopago/webhook | 60/min | IP | 0 (não testado) | 🟢 BAIXO |
| POST /api/modulos/webhook | 60/min | IP | 0 (não testado) | 🟢 BAIXO |
| POST /api/tenant/webhook | 60/min | IP | 0 (não testado) | 🟢 BAIXO |
| POST /api/dr-anderson/webhook | 60/min | IP | 0 (não testado) | 🟢 BAIXO |
| POST /api/dosagens/calcular | 60/min | IP | 0 (não testado) | 🟢 BAIXO |
| POST /api/ia/chat | custom (rate_limit_service) | profissional_id | 0 | 🟢 OK (já tem impl) |
| POST /api/ai/dosing | custom (rate_limit_service) | profissional_id | 0 | 🟢 OK (já tem impl) |
| POST /api/auth/* (outros) | 60/min (default) | IP | - | 🟡 MÉDIO |

---

## 7. ONDE OCORREM OS 429

| Categoria | # 429 no peak | % do total 429 |
|-----------|---------------|----------------|
| Dashboard/Pacientes (consulta intensiva) | 8.230 | 86,6% |
| Módulos/Planos (catálogo) | 1.989 | 20,9% |
| Auth/Login | ~64 | <1% |
| Webhooks (W1-W5) | 0 | 0% (não testados) |
| IA/Agent | 0 | 0% (não testados) |

**Cálculo:** 200 users × ~0,5 RPS = 100 req/s do mesmo IP. Limite = 60/min ÷ 60s = 1 req/s. Satura em **3,6 segundos**.

**Usuários autenticados compartilham bucket?** SIM, porque a chave é apenas IP. Em produção real, IPs podem ser compartilhados via NAT corporativo, proxy, Wi-Fi compartilhado.

---

## 8. PROPOSTA TÉCNICA — FASE 5A

### 8.1 Arquitetura

```
Request → Flask Route + @limiter.limit()
       → Key function (IP ou profissional_id)
       → Flask-Limiter (moving-window)
       → Redis compartilhado (db=1)
```

### 8.2 Mudanças propostas (~45 linhas + 1 env var)

| Item | Antes | Depois |
|------|-------|--------|
| `storage_uri` | `memory://` (hardcoded) | `REDIS_URL/1` (env-driven) |
| `key_func` autenticado | IP | `get_jwt_identity` (profissional_id) |
| `key_func` público | IP | mantém IP |
| `default_limits` | `1000/day, 60/min` | `200/min, 5000/hour` |
| `strategy` | `fixed-window` | `moving-window` |
| `/auth/login` | default 60/min | `LOGIN_RATE_LIMIT = "10/min"` |
| Endpoints sensíveis (POST) | default 60/min | `SENSITIVE_ENDPOINTS_RATE_LIMIT = "100/min"` |
| Webhooks W1-W5 | default 60/min | `@limiter.exempt` (já validados por HMAC FASE 4.5) |

### 8.3 Resultado esperado

| Cenário | Antes | Esperado depois |
|---------|-------|-----------------|
| Baseline 50 users | 63% falha | **<10% falha** |
| Peak 200 users | 84% falha | **<30% falha** |
| RPS sustentado | ~20 | **~80+** |
| p95 latência adicionada | n/a | **<5ms** (Redis local) |

### 8.4 Esforço estimado

| Tarefa | Linhas | Risco |
|--------|--------|-------|
| Trocar storage_uri para Redis | ~5 | BAIXO |
| Key function híbrido | ~20 | MÉDIO |
| Aplicar LOGIN_RATE_LIMIT | ~2 | BAIXO |
| Aplicar SENSITIVE_ENDPOINTS_RATE_LIMIT | ~10 decorators | BAIXO |
| Excluir webhooks W1-W5 | ~5 decorators | BAIXO |
| Atualizar `.env.production` (Redis db=1) | 1 linha | BAIXO |
| Re-rodar load test | 0 | BAIXO |
| **TOTAL** | **~45 linhas + 1 env var** | BAIXO-MÉDIO |

### 8.5 Riscos residuais

| Risco | Mitigação |
|-------|-----------|
| Redis cair → rate limit inativo | Fallback in-memory + log warning |
| Memória Redis cheia | TTL automático + maxmemory-policy=allkeys-lru |
| NAT/proxy compartilhar IP | Header X-Forwarded-For + hierarchy |
| Multi-contas por profissional | Limite por prof_id é por conta |

---

## 9. PRÓXIMOS PASSOS

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

**Arquivos relevantes (somente leitura):**
- `security_config.py:135-145` — `init_limiter()`
- `security_config.py:75-78` — constantes (não aplicadas)
- `app_cors_livre.py:72-73` — chamada `init_limiter(app)`
- `services/rate_limit_service.py` — Redis próprio para IA
- `docker-compose.prod.yml:35-37` — container Redis
- `.env.production.example:118` — `REDIS_URL`
- `tests/load/locustfile.py` — cenário de carga
- `reports/load_baseline_*.csv` + `reports/load_peak_*.csv` — resultados
