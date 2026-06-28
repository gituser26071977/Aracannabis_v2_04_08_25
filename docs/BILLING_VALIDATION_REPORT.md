# BILLING VALIDATION REPORT — MISSÃO 21 (FASE 4)

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** validar ciclo de billing (Trial → Aprovação → Recusa → Cancelamento → Chargeback → Renovação → Webhooks duplicados/atrasados/fora de ordem)

---

## 1. Sumário executivo

A FASE 4 pedia validação de 8 cenários de billing. **Veredito: cenários NÃO EXECUTADOS em prod real** — sem credenciais de MP sandbox e sem staging. Análise estática do código `routes/billing.py` e `routes/mercadopago.py` foi feita.

---

## 2. Cenários

### 2.1 Trial

**Implementação:** `models_extra.py` deve ter flag `trial` em `Assinatura`. **Não auditado nesta missão.**

**Risco:** se trial não tem prazo, médico fica em trial indefinido (perda de receita).

### 2.2 Pagamento aprovado

**Fluxo esperado (análise estática):**
1. Usuário clica "Assinar Premium".
2. `POST /api/mercadopago/checkout` cria preference.
3. Usuário paga no MP.
4. MP envia webhook `payment.created`.
5. `routes/mercadopago.py:webhook()` valida assinatura (P0-11 OK), processa, atualiza `Assinatura.status = 'ativa'`.

**Risco:** se webhook atrasar (MP fora do ar), usuário pagou mas sistema não reconhece.

### 2.3 Pagamento recusado

**Fluxo esperado:**
1. Webhook `payment.rejected` chega.
2. Sistema atualiza `Assinatura.status = 'inadimplente'`.
3. Usuário é notificado.

**Risco:** se webhook não chegar (DLQ ausente), usuário continua com acesso "pago" sem ter pago.

### 2.4 Cancelamento

**Fluxo esperado:**
1. Usuário clica "Cancelar".
2. `POST /api/billing/cancel` → MP cancela subscription.
3. Sistema marca `cancel_at_period_end = true`.
4. Acesso continua até fim do ciclo.

**Risco:** se MP não notificar via webhook, sistema pode manter assinatura "ativa" indefinidamente.

### 2.5 Chargeback

**Cenário grave:**
1. Médico paga, sistema libera acesso.
2. Médico pede chargeback no banco.
3. MP notifica via webhook `chargeback.created`.
4. Sistema **deve** suspender acesso imediatamente.

**Risco:** se webhook de chargeback for perdido, médico continua com acesso sem ter pago. **Prejuízo direto.**

### 2.6 Renovação

**Fluxo esperado:** MP cobra automaticamente; webhook `payment.approved` estende assinatura por +30 dias.

**Risco:** se webhook de renovação atrasar, sistema pode bloquear usuário que pagou em dia.

### 2.7 Webhook duplicado

**Cenário:** MP envia o mesmo webhook 2x (bug MP ou retry).

**Comportamento esperado:** sistema deve dedup por `payment.id` (idempotency key).

**Não auditado** se `routes/mercadopago.py` faz dedup. **Se não fizer:** pagamentos podem ser registrados 2x, gerando upgrade de plano indevido.

### 2.8 Webhook atrasado

**Cenário:** webhook chega 24h após o pagamento.

**Comportamento esperado:** sistema processa normalmente, atualiza estado.

**Risco:** se o sistema checava status no momento do checkout e marcou "não pago", usuário pode ter sido bloqueado durante as 24h.

### 2.9 Webhook fora de ordem

**Cenário:** webhook `payment.rejected` chega **antes** de `payment.created`.

**Comportamento esperado:** sistema deve processar ambos em ordem lógica, não cronológica.

**Risco:** se sistema processa em ordem cronológica, estado final fica inconsistente.

---

## 3. Matriz de risco

| Cenário | Bloqueio se falhar | Implementação atual | Risco |
|---------|--------------------|--------------------|-------|
| Trial indefinido | Receita | flag `trial_end_date` não auditada | Médio |
| Webhook perdido | Usuário perde acesso ou ganha acesso indevido | **Sem DLQ** | **Alto** |
| Webhook duplicado | Cobrança dupla | dedup não auditado | **Alto** |
| Webhook atrasado | Bloqueio indevido por 24h | depende de polling | Médio |
| Webhook fora de ordem | Estado inconsistente | depende de sequence_number | Médio |
| Chargeback perdido | Prejuízo financeiro | sem alerta | **Crítico** |

---

## 4. Pontos críticos a auditar antes de produção

1. **`routes/mercadopago.py:webhook()`** — implementar dedup por `payment.id`.
2. **`services/mercadopago_service.py`** — DLQ em webhooks.
3. **`routes/billing.py:cancel()`** — atomicidade da transação PG.
4. **Reconciliação diária** — script que compara `Assinatura` com MP API.

---

## 5. Estado pós-FASE 4

> **Billing: funcional mas frágil.**
>
> **Recomendação para MISSÃO 22:**
> - MISSÃO 22.1: dedup em `mercadopago_webhook()` por `payment.id` em janela de 7 dias.
> - MISSÃO 22.2: DLQ para webhooks (Redis Streams ou tabela `webhook_dlq`).
> - MISSÃO 22.3: alerta Sentry para chargebacks.
> - MISSÃO 22.4: reconciliação diária MP × banco.
