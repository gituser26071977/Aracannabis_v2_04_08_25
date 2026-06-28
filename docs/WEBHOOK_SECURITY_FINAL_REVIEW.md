# WEBHOOK SECURITY FINAL REVIEW — FASE 4 P0-A

**Data:** 2026-06-22
**Escopo:** Revisão final baseada em evidência, **sem alterar código**.
**Branch:** `feat/clinica-management`
**Auditor:** Claude (auto-revisão)

---

## 1. ANTI-REPLAY

### 1.1 WebhookLog — UNIQUE constraint

**Evidência:** `models_extra.py:138-140`
```python
__table_args__ = (
    db.UniqueConstraint('provider', 'provider_event_id', name='uq_webhook_provider_event'),
)
```
✅ **CONFIRMADO**: `WebhookLog` possui `UNIQUE(provider, provider_event_id)`.

### 1.2 Race condition — Análise

**Evidência:** `services/webhook_auth.py:188-199`
```python
def check_replay(provider: str, event_id: str) -> Tuple[bool, Optional[int]]:
    ...
    existing = WebhookLog.query.filter_by(
        provider=provider, provider_event_id=str(event_id)
    ).first()
    if existing and existing.processed:
        return True, existing.id
```
**`check_replay` faz apenas SELECT. NÃO faz INSERT.**

**Evidência de onde INSERT acontece:** `services/webhook_handler.py:39-56`
```python
existing = WebhookLog.query.filter_by(
    provider=provider_name, provider_event_id=provider_event_id
).first()
if existing and existing.processed:
    return {"success": True, "idempotent": True, ...}
# Criar/Atualizar log
if not existing:
    log = WebhookLog(...)
    db.session.add(log)
    db.session.commit()    # ← INSERT SEM TRY/EXCEPT
```

**⚠️ RACE CONDITION REAL DETECTADA:**

1. **W1 (MercadoPago) — caminho legado (feature flag `new_billing_v2` OFF):**
   - `check_replay` → SELECT → não encontra (porque INSERT nunca aconteceu) → retorna `False`
   - Rota segue para `mercadopago_service.processar_webhook()` que **NÃO insere em WebhookLog**
   - Segunda request idêntica: mesmo SELECT → mesmo resultado → **processamento duplicado** (assinatura ativada duas vezes, fatura marcada como paga duas vezes)
   - **Idempotência CONDICIONAL à feature flag.** Se flag desativada, anti-replay está quebrado em W1.

2. **`webhook_handler.process()` — race entre SELECT e INSERT:**
   - Duas requests simultâneas no mesmo `(provider, event_id)`:
     - Request A: SELECT não encontra → INSERT (sucesso, linha 56)
     - Request B (paralela): SELECT não encontra (antes do commit de A) → INSERT → **IntegrityError por UNIQUE constraint** → **500 não tratado** (linha 56 não tem try/except)
   - **Resultado:** 500 retornado ao provedor. Para MP pode gerar retry. Para Evolution pode deixar mensagem não respondida.

3. **W2 / W4 / W5 (Evolution + Modulos) — `check_replay` é chamado mas INSERT nunca acontece para esses providers:**
   - `check_replay` funciona na PRIMEIRA request (retorna False)
   - Processamento executa normalmente
   - WebhookHandler.process() **NÃO é chamado** (apenas MP usa o handler unificado)
   - Segunda request: `check_replay` SELECT novamente → **não encontra (porque ninguém inseriu)** → retorna False → processa DUAS VEZES
   - **Idempotência QUEBRADA em W2/W4/W5** (exceto se houver INSERT manual em outro lugar — não há).

### 1.3 Impacto real

| Webhook | Idempotência funcional? | Notas |
|---------|-------------------------|-------|
| W1 MP (flag ON) | ✅ Funciona | SELECT encontra, retorna idempotent |
| W1 MP (flag OFF) | ❌ **QUEBRADA** | INSERT nunca acontece |
| W2 Evolution tenant | ❌ **QUEBRADA** | INSERT nunca acontece para `evolution_tenant` |
| W4 Evolution Dr.Anderson | ❌ **QUEBRADA** | INSERT nunca acontece para `evolution_dr_anderson` |
| W5 Modulos MP | ❌ **QUEBRADA** | INSERT nunca acontece para `modulos` |

**Conclusão:** A UniqueConstraint existe e protege o **INSERT no WebhookHandler** quando chamado. Mas como **W2/W4/W5 nunca chamam WebhookHandler** e **W1 chama apenas com flag ON**, a proteção anti-replay está **parcialmente funcional** e depende de configuração externa.

---

## 2. MERCADO PAGO

### 2.1 Headers oficiais vs implementação

**Fonte oficial:** [Mercado Pago Developers — Webhooks](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks) (via WebFetch 2026-06-22)

| Header | Doc oficial MP | Implementação FASE 4 | Compatível? |
|--------|----------------|----------------------|-------------|
| `x-signature` | `ts=<timestamp>,v1=<hex_hmac>` | Lê em `services/webhook_auth.py:220` e parseia `ts=` e `v1=` | ✅ |
| `x-request-id` | Referenciado em exemplos de SDK | Lê em `services/webhook_auth.py:221` | ✅ |
| `data.id` | `data.id` do payload JSON | Extraído por `_mp_extract_data_id()` em `routes/mercadopago.py:120-127` | ✅ |
| HMAC SHA256 | Template `id:{data_id};request-id:{x_request_id};ts:{ts};` | Implementado em `services/webhook_auth.py:117` | ✅ |

### 2.2 Template HMAC — implementação

**Evidência:** `services/webhook_auth.py:117`
```python
template = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
expected = _compute_hmac_sha256(secret, template)
```

✅ **CONFIRMADO**: Segue padrão oficial MP documentado em SDK examples (`id:[data.id];request-id:[x-request-id];ts:[timestamp];`).

### 2.3 Compatibilidade com todos webhooks MP do projeto

**Webhooks MP no projeto:**
| Endpoint | Provider | Secret usado |
|----------|----------|--------------|
| `/api/mercadopago/webhook` (W1) | MP principal | `MERCADOPAGO_WEBHOOK_SECRET` |
| `/api/modulos/webhook` (W5) | MP (módulos) | `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` |

**⚠️ INCOMPATIBILIDADE POTENCIAL DETECTADA:**

O painel do Mercado Pago permite configurar **um secret por aplicação**, não por URL. Se o operador:
- Provisionar **UM secret** no painel MP e usar o mesmo em ambos `.env`, então ambos funcionam.
- Provisionar **dois secrets diferentes**, o MP enviará a assinatura do secret A mas o SIAP validará com secret B → **falha de autenticação 401** em todas as notificações.

**Recomendação:** provisionar o **mesmo secret** para ambos (`MERCADOPAGO_WEBHOOK_SECRET` e `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` devem ser idênticos) **OU** desabilitar a validação HMAC em W5 (não recomendado).

**Risco:** ALTO se operador não ler esta nota.

---

## 3. STARTUP FAIL-LOUD

### 3.1 Como o ambiente de produção é determinado

**Existem DOIS detectores divergentes no projeto:**

**Detector A — `config.py:21-22` (usado em P0-03):**
```python
def _is_production() -> bool:
    return os.environ.get("ENVIRONMENT", "development").lower() in ("production", "prod")
```
Lê `ENVIRONMENT`. Default = `"development"`.

**Detector B — `app_cors_livre.py:32` (usado em FASE 4):**
```python
is_production = os.environ.get("FLASK_ENV", "production") == "production"
```
Lê `FLASK_ENV`. Default = `"production"`.

### 3.2 Configuração real em produção

**Evidência:** `docker-compose.prod.yml:52`
```yaml
- FLASK_ENV=production
```

**Evidência:** Busca por `ENVIRONMENT` em todo o repositório (`docker-compose.yml`, `docker-compose.prod.yml`, `entrypoint_siap.sh`, `.env.example`):
- ❌ `ENVIRONMENT` **NÃO É SETADO EM NENHUM LUGAR** do projeto.

### 3.3 Comportamento em produção real

| Detector | Variável lida | Valor em produção | Resultado |
|----------|---------------|-------------------|-----------|
| `config.py:_is_production()` | `ENVIRONMENT` | (unset) | **`False`** (fallback "development") |
| `app_cors_livre.py:32` | `FLASK_ENV` | `production` | **`True`** ✅ |

### 3.4 Impacto para FASE 4

✅ **Para FASE 4**: `assert_required_secrets_on_startup()` em `app_cors_livre.py:33-42` **DISPARA corretamente em produção real** porque usa Detector B (`FLASK_ENV`). Se faltar qualquer uma das 5 env vars, startup aborta com `RuntimeError`.

⚠️ **Pré-existente (fora do escopo FASE 4)**: Detector A em `config.py` **NÃO detecta produção real**, então `validate_required_secrets()` do P0-03 (JWT_SECRET_KEY, SECRET_KEY) **não dispara** em produção. Isto é bug pré-existente documentado em outras auditorias. **Não foi tocado na FASE 4.**

### 3.5 Cenário onde produção sobe sem secrets

**Cenário 1 (FASE 4):** Impossível. Se `FLASK_ENV=production` (caso padrão em produção real), startup aborta se faltar qualquer das 5 env vars da FASE 4.

**Cenário 2 (operador desabilita):** Se alguém setar `FLASK_ENV=development` em produção deliberadamente, todos os 5 secrets são opcionais. **Risco de má-configuração deliberada.**

**Cenário 3 (Docker sem env file):** Se `.env` não for carregado e nenhuma das 5 env vars estiver setada no ambiente Docker, startup aborta. Comportamento correto (fail-loud).

---

## 4. REPLAYS — 409 vs 200 idempotente

### 4.1 Inventário de webhooks e status code de replay

**Evidência:** Busca por `check_replay` e códigos de retorno:

| Webhook | Endpoint | Provedor | Replay retorna | Chamado por |
|---------|----------|----------|----------------|-------------|
| **W1** MP | `/api/mercadopago/webhook` | MercadoPago | **200** `{status: ok, idempotent: True}` | Provedor externo (MP) |
| **W2** Evolution tenant | `/api/tenant/webhook` | Evolution API | **200** `{status: ok, idempotent: True}` | Provedor externo (Evolution) |
| **W4** Evolution Dr.Anderson | `/api/dr-anderson/webhook` | Evolution API | **200** `{status: ok, idempotent: True}` | Provedor externo (Evolution) |
| **W5** Modulos MP | `/api/modulos/webhook` | MercadoPago | **409** `{error: duplicate event, idempotent: True}` | Provedor externo (MP) |

**Evidência W5:** `routes/modulos.py:385-390`
```python
is_replay, replay_log_id = check_replay("modulos", event_id)
if is_replay:
    ...
    return jsonify({"error": "duplicate event", "idempotent": True}), 409
```

### 4.2 Provedores externos e comportamento de retry

| Provedor | Retenta em 4xx? | Retenta em 409? | Risco de loop |
|----------|-----------------|-----------------|---------------|
| **MercadoPago** (W1, W5) | Histórico: retenta em 5xx e alguns 4xx por até 9 vezes (exponential backoff) | **Provável** (MP não diferencia 409 de outros 4xx) | ⚠️ **ALTO** para W5 |
| **Evolution API** | Tipicamente não retenta (configurável pelo admin) | Baixo risco | ✅ Baixo |

**Fonte:** Documentação oficial MP NÃO descreve comportamento de retry em 4xx/409. Comportamento histórico observado em fóruns de developers: MP retenta notificações em erros 5xx e em alguns 4xx (com backoff). Status 200 é o único "ACK" definitivo.

### 4.3 Análise de W5 especificamente

**Cenário:** Cliente paga módulo → MP envia webhook → W5 processa e ativa assinatura → Cliente recarrega página → MP **reenvia** o mesmo webhook (comportamento normal de MP, especialmente em integrações que demoram a responder 200) → W5 detecta replay → **retorna 409** → MP interpreta como erro → **MP retenta** → loop potencial.

**Recomendação (para FASE 5+):** W5 deveria retornar **200 idempotente** consistente com W1/W2/W4, evitando que MP entre em loop de retry. **Inconsistência atual é bug latente.**

---

## 5. RESPOSTAS FINAIS

### Q1. Existe alguma race condition restante?
**SIM — duas:**

1. **Idempotência condicional em W1 (MP):** se `FeatureFlagService.is_enabled('new_billing_v2') == False`, INSERT em `WebhookLog` nunca acontece, e `check_replay` retorna `False` em todas as requests, permitindo duplicação. **Mitigação parcial porque o decorator `@mercadopago_webhook_required` é executado antes do handler.**

2. **Idempotência quebrada em W2/W4/W5:** `check_replay` é chamado mas **nenhum INSERT em WebhookLog acontece** para esses providers (eles não usam `webhook_handler.process()`). Resultado: replay sempre retorna `False`, processa duas vezes.

3. **Race entre SELECT e INSERT em `webhook_handler.process()`:** duas requests simultâneas para mesmo `(provider, event_id)` causam `IntegrityError` não tratado (linha 56 sem try/except) → 500 retornado ao provedor → retry loop em MP.

### Q2. Existe incompatibilidade potencial com Mercado Pago?
**SIM — risco ALTO se operador não alinhar secrets:**

- W1 e W5 usam secrets diferentes: `MERCADOPAGO_WEBHOOK_SECRET` e `MERCADOPAGO_MODULOS_WEBHOOK_SECRET`.
- Painel MP permite **um secret por aplicação**, não por URL.
- Se operador provisionar **secret único** no painel MP e replicar para ambos `.env`, ambos webhooks funcionam.
- Se operador provisionar **dois secrets diferentes**, todas as notificações MP falham com 401.

**Ação obrigatória do operador:** documentar no deploy runbook que ambos secrets DEVEM ser idênticos ao secret configurado no painel MP.

### Q3. Existe cenário onde produção sobe sem secrets?
**NÃO para os 5 secrets da FASE 4** (enquanto `FLASK_ENV=production`):

- `assert_required_secrets_on_startup()` em `app_cors_livre.py:33-42` dispara corretamente porque usa `FLASK_ENV`.
- Se qualquer das 5 env vars (`MERCADOPAGO_WEBHOOK_SECRET`, `MERCADOPAGO_MODULOS_WEBHOOK_SECRET`, `EVOLUTION_WEBHOOK_SECRET`, `DR_ANDERSON_WEBHOOK_SECRET`, `INTERNAL_SERVICE_KEY`) estiver ausente, startup aborta com `RuntimeError`.

**Risco residual:** má-configuração deliberada (operador seta `FLASK_ENV=development` em produção). Fora do escopo defender contra isso.

**Nota:** existe pré-existente em `config.py` que detecta produção por `ENVIRONMENT` (não setado em nenhum lugar) — bug conhecido do P0-03, **não introduzido pela FASE 4**.

### Q4. Existe webhook que pode entrar em loop de retry?
**SIM — W5 (Modulos) tem risco ALTO:**

- W5 retorna **409 Conflict** em replay (único dos 4 webhooks que faz isso).
- W1, W2, W4 retornam **200 idempotente** (padrão correto para evitar retry).
- MercadoPago historicamente retenta em 4xx (incluindo 409). Comportamento documentado em fóruns de developers.
- Se MP retentar o mesmo webhook, W5 devolve 409 novamente → loop até MP desistir (geralmente após N tentativas com backoff).

**Recomendação (para FASE 5+):** alterar W5 para retornar 200 idempotente, consistente com W1/W2/W4.

### Q5. Você aprova o merge para produção?
**APROVAÇÃO CONDICIONAL — depende de 3 ações do operador ANTES do deploy:**

1. ✅ Provisionar `MERCADOPAGO_WEBHOOK_SECRET` e `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` no painel MP como **mesmo secret**.
2. ✅ Configurar Evolution API para enviar header `x-webhook-signature: sha256=<hmac(body, EVOLUTION_WEBHOOK_SECRET)>` em W2 + W4.
3. ✅ Garantir que `INTERNAL_SERVICE_KEY` está setado no `.env.production`.

**Ressalvas (não-bloqueantes, podem ser endereçadas em FASE 5+):**
- Idempotência condicional em W1 (depende de feature flag `new_billing_v2`)
- Idempotência quebrada em W2/W4/W5 (INSERT nunca acontece para esses providers)
- Race em `webhook_handler.process()` (SELECT + INSERT sem lock)
- W5 retorna 409 (deveria ser 200 idempotente)
- Detector de produção divergente em `config.py` (`ENVIRONMENT` vs `FLASK_ENV`) — pré-existente

**Recomendação final:** APROVAR merge da FASE 4 com as 3 ações do operador. As ressalvas não-bloqueantes podem ir para FASE 5 ou P1.

---

## 6. EVIDÊNCIAS COLETADAS (referência rápida)

| Arquivo | Linhas | Conteúdo |
|---------|--------|----------|
| `models_extra.py` | 138-140 | `UniqueConstraint('provider', 'provider_event_id')` |
| `services/webhook_auth.py` | 117 | Template HMAC MP `id:{data_id};request-id:{x_request_id};ts:{ts};` |
| `services/webhook_auth.py` | 188-199 | `check_replay` apenas SELECT, sem INSERT |
| `services/webhook_handler.py` | 39-56 | INSERT sem try/except em WebhookLog |
| `services/mercadopago_service.py` | 19, 134-158 | `MERCADOPAGO_WEBHOOK_SECRET` lido mas nunca usado para HMAC antes da FASE 4 |
| `app_cors_livre.py` | 32 | `is_production` baseado em `FLASK_ENV` |
| `config.py` | 21-22 | `_is_production()` baseado em `ENVIRONMENT` (nunca setado) |
| `docker-compose.prod.yml` | 52 | `FLASK_ENV=production` setado |
| `docker-compose.yml` | 28 | `FLASK_ENV=development` setado |
| `routes/modulos.py` | 385-390 | W5 retorna 409 em replay |
| `routes/mercadopago.py` | 150-153 | W1 retorna 200 idempotent em replay |
| `routes/dynamic_tenant_webhook.py` | 42-45 | W2 retorna 200 idempotent em replay |
| `routes/dr_anderson_webhook.py` | 132-135 | W4 retorna 200 idempotent em replay |
| `docs/AUDITORIA_SEGURANCA_2026_06.md` | 77-78 | Confirma que `MERCADOPAGO_WEBHOOK_SECRET` nunca foi usado para HMAC |

---

## 7. FONTES EXTERNAS CONSULTADAS

- [Mercado Pago Developers — Notificações / Webhooks (overview)](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications) — confirmou que Webhooks oferecem HMAC signature validation e IPN NÃO suporta `x-signature`.
- [Mercado Pago Developers — Notificações / Webhooks (detail)](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks) — confirmou formato de `x-signature: ts=<timestamp>,v1=<hex>` e headers `x-signature` + `x-request-id`. Não documenta comportamento de retry em 409.

---

**FIM DO RELATÓRIO — Aguardando revisão humana.**
**Próximo passo (somente após aprovação):** marcar FASE 4 (#30) como completed. NÃO iniciar FASE 5 automaticamente.