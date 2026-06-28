# FAILOVER REPORT — MISSÃO 21 (FASE 2)

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** simular falha de Redis/PG/Evolution/MP/Worker/Traefik/Cloudflare e medir degradação
**Veredito:** **NÃO PÔDE SER EXECUTADO** — sem staging + sem autorização para chaos em prod

---

## 1. Sumário executivo

A FASE 2 pedia simulação de indisponibilidade de 7 dependências e medição de degradação/recuperação/perda de dados/MTTR. **Esta fase não pôde ser executada** porque:

1. **Staging inexistente** — não há ambiente isolado para chaos test.
2. **Sem janela autorizada** para derrubar Redis/PG em prod.
3. **Cloudflare Tunnel** não está em uso (apenas Let's Encrypt via Traefik).
4. **Auto-mode bloqueia** operações que afetem produção compartilhada.

Foi feita **análise estática** de cada dependência para antecipar comportamento esperado.

---

## 2. Análise estática por dependência

### 2.1 Redis

**Uso no AraOS:**
- Flask-Limiter storage (rate limit)
- Flask-Session backend
- Cache de queries
- Fila RQ (fila assíncrona)

**Comportamento esperado em falha (análise de `app_cors_livre.py`, `security_config.py`):**
- `init_limiter(app)` usa Redis como storage. **Sem Redis:** rate limiter cai em `MemoryStorage` (in-memory), perdendo contadores entre requests.
- **RQ workers:** sem Redis, fila inteira para.
- **Sessões:** usuários logados são deslogados (sessão perdida).

**Degradação:** SIM — sistema continua mas sem rate limit funcional.
**Travamento:** NÃO.
**Perda de dados:** SIM — sessões ativas; jobs em fila RQ.
**Recuperação:** AUTOMÁTICA quando Redis volta (rate limit reseta contadores).

**MTTR estimado:** <5min (restart não necessário).

### 2.2 PostgreSQL

**Uso:** principal.

**Comportamento esperado:**
- `db.session.execute(db.text("SELECT 1"))` levanta `OperationalError`.
- `/api/health` retorna 503.
- **Todas as rotas que dependem de DB retornam 500.**
- Gunicorn workers travam em queries pendentes (timeout 300s).

**Degradação:** SIM — sistema **trava**.
**Travamento:** SIM — após esgotar timeout de cada worker.
**Perda de dados:** SIM em transações in-flight (rollback automático).
**Recuperação:** DEPENDE — após PG voltar, transientes são refeitos.

**MTTR estimado:**
- Restart do PG: 2-5min.
- Restart do backend (workers limpos): 1-3min.
- **Total: 3-8min para estado consistente.**

### 2.3 Evolution (WhatsApp)

**Uso:** envio de mensagens via webhook `/api/whatsapp/send`.

**Comportamento esperado:**
- `services/whatsapp_service.py` faz HTTP POST para Evolution.
- Falha levanta `requests.exceptions.RequestException`.
- Código **deve** capturar e logar (verificar arquivo).
- **Sem retry persistente** (DLQ não implementado — P1 do backlog).

**Degradação:** SIM — mensagens não são enviadas.
**Travamento:** NÃO.
**Perda de dados:** SIM em mensagens pendentes — fila RQ é afetada se Redis também caiu.
**Recuperação:** MANUAL — operador deve reprocessar jobs manualmente.

**MTTR estimado:** 10-60min (incluindo investigação + reprocessamento manual).

### 2.4 Mercado Pago

**Uso:** billing + webhook.

**Comportamento esperado:**
- `routes/mercadopago.py:119-159` valida assinatura HMAC (já corrigido em P0-11).
- Falha no MP durante checkout: usuário vê erro.
- Webhook perdido: pagamento não confirmado (sem DLQ).

**Degradação:** SIM em checkout; webhooks perdidos.
**Travamento:** NÃO.
**Perda de dados:** SIM — pagamentos podem ser perdidos se webhook não chega.
**Recuperação:** MANUAL — operador roda script de reconciliação MP.

**MTTR estimado:** 30-120min (conciliação manual).

### 2.5 Worker (RQ)

**Uso:** jobs assíncronos.

**Comportamento esperado:**
- 1 worker processando (herdado de M17).
- Falha do worker: jobs ficam enfileirados.

**Degradação:** SIM — jobs atrasam.
**Travamento:** NÃO (frontend responde, mas ações demoram).
**Perda de dados:** NÃO (fila persiste em Redis).
**Recuperação:** AUTOMÁTICA — reiniciar worker processa fila.

**MTTR estimado:** 1-3min (restart worker).

### 2.6 Traefik

**Uso:** reverse proxy + TLS.

**Comportamento esperado:**
- Sem Traefik: domínios param de responder.
- Containers Docker continuam rodando (acessíveis via `localhost:5002`).

**Degradação:** SIM — sistema inacessível externamente.
**Travamento:** NÃO do app.
**Perda de dados:** NÃO.
**Recuperação:** AUTOMÁTICA com restart do Traefik (let's Encrypt renewal pode falhar).

**MTTR estimado:** 1-5min (Traefik tem healthcheck).

### 2.7 Cloudflare Tunnel

**Status:** **NÃO UTILIZADO**.

O AraOS usa Traefik + Let's Encrypt diretamente. Cloudflare Tunnel não está no stack.

---

## 3. Matriz consolidada

| Dependência | Degrada? | Trava? | Perde dados? | Duplica? | Recupera sozinho? | MTTR |
|-------------|----------|--------|--------------|----------|-------------------|------|
| Redis | SIM | NÃO | SIM (sessões) | NÃO | SIM (limitado) | <5min |
| PostgreSQL | SIM | **SIM** | SIM (transientes) | NÃO | DEPENDE | 3-8min |
| Evolution | SIM | NÃO | SIM (mensagens) | NÃO | NÃO (manual) | 10-60min |
| Mercado Pago | SIM | NÃO | SIM (pagamentos) | SIM se webhook duplicado | NÃO (manual) | 30-120min |
| Worker (RQ) | SIM | NÃO | NÃO | NÃO | SIM | 1-3min |
| Traefik | SIM | NÃO | NÃO | NÃO | SIM | 1-5min |
| Cloudflare | N/A | N/A | N/A | N/A | N/A | N/A |

---

## 4. Cenários de duplicação de dados

**Apenas MercadoPago pode duplicar** se o webhook chegar duplicado. Análise:

- `verify_webhook_signature` (M18 P0-11) usa `compare_digest` — assinatura válida é confiável.
- `routes/mercadopago.py` deve checar idempotência via `payment_id`. **Não auditado nesta missão** mas é prática padrão.
- Se **não houver dedup**: webhook duplicado gera 2 cobranças no banco.

**Recomendação:** auditar `routes/mercadopago.py:webhook()` para dedup por `data.id`.

---

## 5. Cenários de perda de mensagens

| Serviço | Cenário de perda |
|---------|------------------|
| Webhook MP | Sem DLQ — pagamento pode ser perdido se webhook chegar 30min após timeout do MP |
| WhatsApp (Evolution) | Sem retry persistente — mensagens enfileiradas ficam paradas se Evolution ficar off |
| Email | Idem |

---

## 6. MTTR agregado (cenário pior)

Se **TODAS** as dependências caírem simultaneamente (desastre regional):

| Fase | Tempo |
|------|-------|
| Detectar (sem Prometheus) | 5-30min |
| Diagnosticar | 10-30min |
| Acessar VPS | 1min (SSH) |
| Restart PG | 2-5min |
| Restart Redis | 1min |
| Restart Traefik | 1min |
| Restart workers | 1min |
| Validar | 5-10min |
| **TOTAL** | **30-80min** |

Com Prometheus + Alertmanager (M20 provisionado): detecção cai para <1min. **MTTR total: 15-50min**.

---

## 7. Estado pós-FASE 2

> **Failover NÃO foi executado de fato.**
>
> **Análise estática identifica 3 vulnerabilidades críticas:**
> 1. **PG travando o sistema** — sem circuit breaker.
> 2. **Mensagens WhatsApp sem retry** — perda potencial.
> 3. **Webhook MP sem dedup auditado** — duplicação potencial.
>
> **Recomendação:** MISSÃO 22 = circuit breaker PG + DLQ para webhooks + dedup MP.
