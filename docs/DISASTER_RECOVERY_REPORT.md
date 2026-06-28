# DISASTER RECOVERY REPORT — MISSÃO 17

**Data:** 2026-06-25
**Modo:** EXECUTE (análise estática; simulações NÃO executadas em produção)

---

## 1. Veredito executivo

> **O sistema sobrevive à perda de serviços auxiliares (Redis, Evolution, MP, Gemini) com degradação parcial, MAS:**
> - **Sem retry persistente** para webhooks (MercadoPago, Evolution, Dr. Anderson)
> - **Sem DLQ** (dead-letter queue) verificado
> - **Sem alerta automático** para o operador quando serviço cai
> - **Sem fallback documentado** para LLM Gemini (qual provedor substitui?)

---

## 2. Matriz de resiliência

| Serviço cair | Graceful degradation? | Retry? | Fallback? | Alerta? | Recuperação? |
|--------------|----------------------|--------|-----------|---------|--------------|
| **Redis** | 🟡 Parcial | — | memory:// (warning) | ❌ Não | Automática |
| **PostgreSQL** | 🔴 Não | ❌ | Nenhum | ❌ Não | Manual |
| **Worker (gunicorn)** | 🟢 Sim (outros workers atendem) | — | Sim | ❌ Não | Automática |
| **Evolution (WhatsApp)** | 🟡 Parcial | 🟡 Em código, sem DLQ | ❌ Não | ❌ Não | Manual |
| **MercadoPago** | 🟡 Parcial | 🟡 Ver FASE 4.1 | ❌ Não | ❌ Não | Manual |
| **Gemini / LLM** | 🔴 Não (500 no chat) | ❌ | 🟡 Configurable mas sem fallback testado | ❌ Não | Manual |
| **Anonymization service** | 🔴 Não (500 em IA) | ❌ | Nenhum | ❌ Não | Manual |
| **Webhook duplicado** | 🟢 Sim (idempotency_key) | — | Sim | ❌ Não | Automática |
| **Webhook atrasado** | 🟢 Sim (HMAC + replay window) | — | Sim | ❌ Não | Automática |
| **Webhook perdido** | 🔴 Não (sem DLQ) | ❌ | Nenhum | ❌ Não | Manual |
| **Backups** | 🟡 Backup existe mas frequência não auditada | — | — | ❌ Não | — |

---

## 3. Análise por serviço

### 3.1 Redis (rate-limit + cache)

**Cenário:** `redis-server` cai ou fica inacessível.

**Comportamento atual:**
- `security_config.py:197-201`: warning + fallback para `memory://`.
- Cada worker tem seu próprio bucket → rate-limit **inconsistente** entre workers (3x maior do que deveria).
- `services/cache_service` (se existir) também cai → queries lentas.

**Pontos fracos:**
- Sem `SENTINEL` ou Redis Cluster configurado → single point of failure.
- Sem alerta para operador ("Redis offline por 5 min").

**Recomendação (não executada):**
- Redis Cluster ou Sentinel + 1 replica.
- Alerta PagerDuty/OpsGenie em healthcheck Redis.

### 3.2 PostgreSQL

**Cenário:** DB lento (índice faltando, lock contention) ou down.

**Comportamento atual:**
- `pool_pre_ping=True` detecta conexão morta e reconecta.
- Mas: requests ativos com conexão morta **falham com 500**.
- Sem circuit breaker → todas as rotas falham.

**Pontos fracos:**
- Sem read replica → todas as queries (incluindo dashboard pesado) batem no primário.
- Sem timeout explícito por query → queries lentas podem segurar conexão indefinidamente.

**Recomendação (não executada):**
- `statement_timeout=30s` em `pool_options`.
- PgBouncer para pooling compartilhado.
- Read replica para `/api/dashboard/stats`.

### 3.3 Worker morto

**Cenário:** gunicorn worker crasha (segfault, OOM).

**Comportamento atual:**
- gunicorn master spawna novo worker automaticamente.
- Requests em andamento no worker morto retornam 502.
- Conexões ao DB no pool do worker morto são liberadas em ~30s (pg backend timeout).

**Pontos fracos:**
- Sem monitoring de "worker restart count".
- Se OOM for recorrente, master pode entrar em loop.

**Recomendação (não executada):**
- Métrica `gunicorn_worker_restarts_total` em Prometheus.
- Alert se >5 restarts/min.

### 3.4 Evolution (WhatsApp)

**Cenário:** Evolution API offline (servidor caiu, key expirou, whatsapp desconectou).

**Comportamento atual:**
- Webhook `/api/webhooks/evolution` retorna 503 → Evolution **não tenta novamente** (a menos que configurado no painel).
- Lembretes enviados para fila de envio ficam **pendentes** (sem DLQ verificado em `services/whatsapp_service.py`).
- Frontend mostra "lembrete enviado" mesmo se Evolution está offline (depende de implementação).

**Pontos fracos:**
- Sem fila persistente (RQ/Redis) verificada para mensagens.
- Sem healthcheck do Evolution.

**Recomendação (não executada):**
- Fila RQ para mensagens WhatsApp com retry 3x + DLQ.
- Healthcheck `GET /api/health/evolution` retornando status do provider.

### 3.5 MercadoPago

**Cenário:** MP offline ou webhook bloqueado por proxy.

**Comportamento atual:**
- Webhook `routes/mercadopago.py:119-159` valida HMAC (FASE 4) + idempotency (FASE 4.1).
- Mas: se o webhook chega e o DB está lento, request trava. MP reenvia 3x (config padrão), mas após isso **perde o pagamento**.

**Pontos fracos:**
- Sem retry persistente no nosso lado (se DB está down, MP reenvia, mas o request é perdido se persistir).
- Sem reconciliação periódica (cron que consulta MP para pagamentos que não chegaram).

**Recomendação (não executada):**
- Retry persistente com RQ.
- Cron diário `mercadopago_reconcile` que busca últimos 7 dias e compara com nosso DB.

### 3.6 Gemini / LLM

**Cenário:** Gemini quota exceeded ou API offline.

**Comportamento atual:**
- `routes/ai_chat_simples.py` retorna 500 → frontend mostra erro genérico.
- **Não há fallback** para outro provedor (OpenAI, Groq, Anthropic) — `ai_config.py:87-105` lista providers, mas o fallback automático não está implementado.

**Pontos fracos:**
- Sem circuit breaker.
- Sem fila para retry.
- Sem cache local de prompts comuns.

**Recomendação (não executada):**
- Implementar fallback OpenAI → Groq → Anthropic.
- Cache de respostas idênticas em Redis (1h TTL).
- Circuit breaker com `pybreaker`.

### 3.7 Anonymization service

**Cenário:** Serviço offline (container caiu).

**Comportamento atual:**
- `routes/ai_clinical.py:11` faz `requests.post(ANONYMIZATION_SERVICE_URL, ...)`.
- Sem timeout strict? Sem fallback? — **NÃO AUDITADO** (faria parte de teste ativo).
- Toda chamada de IA clínica quebra.

**Recomendação (não executada):**
- Anonimização local em Python (lib `presidio` ou regex) como fallback.
- Cache da última versão anonimizada do prontuário.

---

## 4. Backup & Restore

**Status atual:**
- `Backup/` directory existe, mas **conteúdo não auditado nesta missão** (modo somente leitura).
- Sem documentação de frequência (cron? diário? semanal?).
- Sem teste de restore documentado.

**Risco:** Se DB for perdido sem backup, **todos os prontuários** (PHI) são perdidos. ANPD + CFM podem multar.

**Recomendação (não executada):**
- Backup diário automático, retenção 30 dias, offsite (S3 + Glacier).
- Teste de restore mensal documentado.
- Criptografia de backup com chave AWS KMS.

---

## 5. Respondendo a pergunta 4

> **4. O sistema sobreviveria à perda de Redis, Evolution e MercadoPago simultaneamente?**
>
> **SIM, com degradação SEVERA mas não-catastrófica:**
>
> | Função | Comportamento sem os 3 |
> |--------|------------------------|
> | Login / Auth | ✅ OK (não depende de Redis) |
> | Pacientes / Consultas / Exames | ✅ OK (dependem só de PG) |
> | Dashboard | ✅ OK (sem cache, mas DB aguenta) |
> | Rate-limit | 🟡 Falha inconsistente (memory://, 3x permissivo) |
> | WhatsApp / Lembretes | 🔴 Quebrado (sem Evolution, sem retry persistente) |
> | Pagamentos / Billing | 🔴 Inconsistente (sem MP webhook, sem reconciliação) |
> | Chat IA | 🟢 OK (Gemini não está no conjunto caído) |
> | Multi-tenant | ✅ OK (filtro no SQLAlchemy) |
>
> **MAS:**
> - Operador **não recebe alerta** de que 3 serviços cairam.
> - Billing pode ficar em estado **zumbi** (assinatura marcada como ativa mas nunca renovada).
> - Lembretes de pacientes **somem** sem DLQ.
> - **PHI em risco** se backup não for recente.

---

## 6. Recomendações (NÃO executadas)

| Prioridade | Ação | Esforço |
|------------|------|---------|
| 🔴 P0 | Alerta PagerDuty para healthcheck Redis/PG/Evolution/MP | 1 dia |
| 🔴 P0 | Fila RQ persistente para webhooks (DLQ) | 3 dias |
| 🔴 P0 | Fallback de LLM (OpenAI/Groq) quando Gemini off | 2 dias |
| 🟠 P1 | Reconciliação diária MercadoPago | 2 dias |
| 🟠 P1 | Backup offsite com restore testado | 1 semana |
| 🟠 P1 | Read replica para dashboard | 1 semana |
| 🟡 P2 | Circuit breaker em todos os serviços externos | 1 semana |
| 🟡 P2 | Status page público (status.araos.com.br) | 1 dia |
