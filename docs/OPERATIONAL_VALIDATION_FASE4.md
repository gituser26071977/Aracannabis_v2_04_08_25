# FASE 4.4 — OPERATIONAL VALIDATION (P0-A)

**Data:** 2026-06-23
**Escopo:** Validar compatibilidade REAL entre a implementação FASE 4 + 4.1 e os provedores externos (Mercado Pago + Evolution API) SEM alterar código.
**Método:** análise estática do código + leitura de fontes oficiais + probes em produção (somente leitura).

**Restrições respeitadas:**
- ❌ NÃO alterei código
- ❌ NÃO criei commits
- ✅ Apenas leitura e diagnóstico

---

## 1. MERCADO PAGO — Análise de Compatibilidade

### 1.1 Especificação oficial (fontes confirmadas)

| Item | Valor oficial | Fonte |
|------|--------------|-------|
| Header de assinatura | `x-signature: ts=<unix>,v1=<hex>` | [MP Webhooks PT-BR](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks) |
| Header auxiliar | `x-request-id: <uuid>` | [MP Webhooks PT-BR](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks) |
| Localização do `data.id` | **query parameter** `?data.id=...` (também enviado no body) | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) — exemplos oficiais Python/JS/Go/Java/C# |
| Template do manifest | `id:{dataID};request-id:{xRequestID};ts:{ts};` | [MP SDK Go source](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) — função `buildManifest()` |
| Lowercase | `id` value é **lowercased** antes de HMAC | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) |
| Janela de tolerância | configurável (`WithTolerance`); padrão = sem tolerância | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) |
| Algoritmo | HMAC SHA256 com secret como chave, hex output | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) |
| Comparação | `hmac.Equal` (constant time) | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) |
| `data.id` ausente | pares com valor vazio são **omitidos** do manifest | [MP SDK Go](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go) |

### 1.2 Implementação atual vs. spec oficial

**Arquivo:** `services/webhook_auth.py:79-124` — `validate_mercadopago_signature()`

```python
def validate_mercadopago_signature(
    secret: str,
    x_signature: str,
    x_request_id: str,
    data_id: str,
    raw_body: str,
) -> Tuple[bool, str]:
```

| Item spec | Implementação | Status |
|-----------|---------------|--------|
| Header `x-signature` parsing | `dict(p.split("=", 1) for p in x_signature.split(","))` | ✅ |
| Header `x-request-id` | lido de `request.headers.get("x-request-id", "")` | ✅ |
| Template `id:{dataID};request-id:{xRequestID};ts:{ts};` | `f"id:{data_id};request-id:{x_request_id};ts:{ts};"` | ✅ estrutura idêntica |
| HMAC SHA256 hex | `_compute_hmac_sha256()` | ✅ |
| Constant-time compare | `hmac.compare_digest(expected, v1)` | ✅ |
| Lowercase do `id` value | **NÃO aplicado** | ⚠️ **risco latente** |
| `data.id` extraído do query param | Lê de JSON body via `_mp_extract_data_id()` | ⚠️ **incompatibilidade documentada** |
| Tolerância de timestamp | 300s via `validate_timestamp()` | ✅ (5 min) |

### 1.3 Probe em produção (W1 — `/api/mercadopago/webhook`)

**Testado em 2026-06-23 contra `api.visualsmartflow.com.br`:**

```bash
curl -X POST https://api.visualsmartflow.com.br/api/mercadopago/webhook \
  -H "Content-Type: application/json" \
  -d '{"data":{"id":"test"},"type":"payment"}'
```

**Resposta:** `HTTP 400 {"status":"error"}`

**Diagnóstico:** produção ainda roda versão **pré-FASE 4** (valida payload antes da auth). Confirmado em 2026-06-22 também. Smoke test em produção do HMAC FASE 4 não é possível sem deploy.

### 1.4 Cenários de risco identificados

| # | Cenário | Status | Impacto |
|---|---------|--------|---------|
| 1 | Webhook MP legítimo com `data.id` em query param E no body | ✅ OK (atualmente o body também traz `data.id` no payload JSON) | Sem impacto |
| 2 | MP envia `data.id` apenas no query param (futuro) | ❌ **Vai falhar com 401** porque `_mp_extract_data_id()` lê do body | CRÍTICO — mudança futura do MP |
| 3 | MP enviar `data.id` em uppercase (ex: UUID) | ❌ **Vai falhar com 401** porque não aplica `.lower()` | BAIXO — improvável, MP usa IDs numéricos |
| 4 | Timestamp MP > 5 min de drift | ❌ **Rejeita com 401** | Aceitável (proteção anti-replay) |
| 5 | `ts` em MP em **milissegundos** ao invés de segundos | ❌ **Vai rejeitar TUDO** (validação compara segundos) | **VERIFICAR EM PRODUÇÃO** — doc MP tem `ts=1704908010` (10 dígitos = segundos), fonte secundária menciona `1700000000000` (13 dígitos = ms) |
| 6 | Replay do mesmo `data.id` | ✅ 200 idempotente (via `register_webhook_event`) | OK |
| 7 | Race entre 2 webhooks simultâneos | ✅ 2ª request → 200 idempotente (UNIQUE constraint) | OK |
| 8 | Retry infinito (MP) | ❌ **Risco em W5** — ver §2 | Ver análise específica de W5 |

### 1.5 Veredito MP — W1

**PARCIALMENTE COMPATÍVEL.**

- ✅ Headers, template, HMAC, constant-time compare: corretos.
- ⚠️ **Defeito #1:** `data.id` é lido do JSON body, spec oficial diz para ler do query param. Funciona enquanto MP envia nos dois lugares (atualmente sim). **Risco latente.**
- ⚠️ **Defeito #2:** `id` value não é lowercased antes de HMAC. Funciona para IDs numéricos, falha se MP mudar para UUIDs.
- ⚠️ **Incerteza #1:** unidade do `ts` (segundos vs milissegundos). Doc principal diz segundos. Verificar em produção.

**Ação necessária ANTES do deploy:** executar smoke test com payload real do MP em ambiente de homologação para confirmar o formato exato que chega. **Sem este teste, há risco de 100% dos webhooks MP serem rejeitados em produção.**

---

## 2. MERCADO PAGO — Análise de W5 (Modulos)

### 2.1 Especificação

W5 (`/api/modulos/webhook`) recebe webhooks do Mercado Pago para ativação de módulos. Mesma origem do W1, mas lógica de negócio diferente.

### 2.2 Implementação atual — `routes/modulos.py:354-358`

```python
@modulos_bp.route("/webhook", methods=["POST"])
@hmac_webhook_required(
    secret_env="MERCADOPAGO_MODULOS_WEBHOOK_SECRET",
    signature_header="x-webhook-signature",  # ← ERRADO: deveria ser x-signature
    provider_name="modulos",
)
def webhook_mercadopago():
```

### 2.3 Incompatibilidade crítica

| Aspecto | O que MP envia | O que W5 espera | Status |
|---------|----------------|-----------------|--------|
| Header | `x-signature: ts=...,v1=...` | `x-webhook-signature: sha256=...` | ❌ **NOME DIFERENTE** |
| Header auxiliar | `x-request-id: <uuid>` | (nenhum) | ❌ **AUSENTE** |
| Template HMAC | `id:{dataID};request-id:{xRequestID};ts:{ts};` | `sha256(secret, body_raw)` | ❌ **DIFERENTE** |
| Onde está `data.id` | query param + body | (não extrai) | ❌ **IGNORADO** |

**W5 NUNCA VAI VALIDAR UM WEBHOOK REAL DO MERCADO PAGO.**

### 2.4 Probe em produção (W5 — `/api/modulos/webhook`)

```bash
curl -X POST https://api.visualsmartflow.com.br/api/modulos/webhook \
  -H "Content-Type: application/json" \
  -d '{"modulo":"base","prof":1}'
```

**Resposta:** `HTTP 200 {"expira_em":"2026-07-23...","modulo":"base","ok":true,"profissional_id":1,"simulate":false,"status":"active"}`

**Diagnóstico:** produção pré-FASE 4 não tem decorator HMAC. Quando FASE 4 deployada, este endpoint **vai retornar 401 para TODOS os webhooks legítimos do MP** porque o decorator espera header errado.

### 2.5 Veredito W5

**INCOMPATÍVEL — BUG CRÍTICO DE IMPLEMENTAÇÃO.**

W5 deveria usar `@mercadopago_webhook_required(get_data_id=...)` (mesmo padrão de W1) ou um decorator dedicado que valida o template oficial MP. O uso de `@hmac_webhook_required` (genérico) é incorreto para um webhook MP.

**Severidade:** BLOQUEADOR. Deploy da FASE 4 com W5 atual = **100% de perda de webhooks de pagamento de módulos.**

---

## 3. EVOLUTION API — Análise de Compatibilidade

### 3.1 Especificação oficial (fontes confirmadas)

**Fonte primária:** [evolution-api repo](https://github.com/EvolutionAPI/evolution-api/blob/main/src/api/integrations/event/webhook/webhook.controller.ts)

| Item | Comportamento |
|------|---------------|
| Headers customizados | Lê de `webhook.headers` (objeto livre, configurado pelo usuário) |
| `x-webhook-signature` | **NÃO adicionado automaticamente** |
| `X-Webhook-Secret` | **NÃO adicionado automaticamente** |
| HMAC SHA256 nativo | **NÃO suportado** |
| Único header built-in | `Authorization: Bearer <jwt>` SE o usuário colocar `jwt_key` no objeto headers |
| Timeout | 30s (configurável) |
| Schema | `enabled`, `url`, `headers`, `byEvents`, `base64`, `events` |

### 3.2 Operacional

**Para um operador configurar Evolution API com HMAC SHA256, é NECESSÁRIO:**

1. Calcular o HMAC em algum sistema intermediário (proxy, Cloudflare Worker, AWS Lambda, n8n)
2. Passar o resultado em `webhook.headers` como valor estático (o que torna o HMAC inútil — mesmo valor para todos os requests)
3. OU usar `jwt_key` para gerar JWT dinâmico (única opção built-in que muda por request)

**Não existe mecanismo nativo na Evolution API para assinar o body com HMAC.**

### 3.3 Implementação atual vs. Evolution API

**W2 (`/api/tenant/webhook`):** `@hmac_webhook_required(secret_env="EVOLUTION_WEBHOOK_SECRET", signature_header="x-webhook-signature", provider_name="evolution_multi_tenant")`

**W4 (`/api/dr-anderson/webhook`):** `@hmac_webhook_required(secret_env="DR_ANDERSON_WEBHOOK_SECRET", signature_header="x-webhook-signature", provider_name="evolution_dr_anderson")`

| Item | O que SIAP espera | O que Evolution envia | Status |
|------|-------------------|------------------------|--------|
| Header `x-webhook-signature: sha256=<hmac>` | sim | **não (por default)** | ❌ **vai falhar** |
| Header estático (ex: `X-Internal-Token`) | não suportado | sim (configurável) | alternativa possível |

### 3.4 Probe em produção (W2 e W4)

```bash
# W2
curl -X POST https://api.visualsmartflow.com.br/api/tenant/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","instance":"smoke","data":{}}'
```

**Resposta:** `HTTP 200 {"reason":"ai_not_configured_or_inactive","status":"ignored"}`

```bash
# W4
curl -X POST https://api.visualsmartflow.com.br/api/dr-anderson/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","data":{}}'
```

**Resposta:** (provavelmente similar a W2, pré-FASE 4)

**Diagnóstico:** produção pré-FASE 4 não tem decorator. Quando FASE 4 deployada, W2 e W4 **vão retornar 401 para TODOS os webhooks legítimos do Evolution** porque Evolution não adiciona `x-webhook-signature` automaticamente.

### 3.5 Cenários de risco identificados

| # | Cenário | Status | Impacto |
|---|---------|--------|---------|
| 1 | Evolution envia webhook (default) | ❌ **Vai falhar com 401** | BLOQUEADOR |
| 2 | Operador configura `X-Webhook-Secret: <secret>` fixo em `webhook.headers` | ❌ W2/W4 esperam `x-webhook-signature` (header diferente) | BLOQUEADOR |
| 3 | Operador configura proxy externo para calcular HMAC e adicionar header | ✅ Funciona | Possível mas operacionalmente pesado |
| 4 | Operador usa `jwt_key` para Authorization Bearer dinâmico | ❌ SIAP não valida JWT | Não ajuda |

### 3.6 Veredito Evolution

**INCOMPATÍVEL — não existe mecanismo nativo.**

W2 e W4 foram implementados esperando que Evolution API adicione header `x-webhook-signature` automaticamente. **Isso não acontece** — Evolution apenas repassa os headers configurados em `webhook.headers` (objeto estático).

**Possíveis soluções (requerem mudança de código):**
1. Trocar W2/W4 de HMAC para `X-Internal-Token` estático + `compare_digest` (mesmo padrão de W3)
2. Configurar proxy externo (n8n, Cloudflare Worker) que calcule HMAC e adicione header
3. Usar `Authorization: Bearer <jwt>` com `jwt_key` placeholder (Evolution suporta) + validação JWT no SIAP

**Severidade:** BLOQUEADOR para deploy da FASE 4. Sem uma das 3 soluções, **100% dos webhooks Evolution serão rejeitados em produção**.

---

## 4. MATRIZ DE COMPATIBILIDADE

| Webhook | Provedor | Header esperado | Header que provedor envia | HMAC nativo do provedor? | Implementação compatível? | Ação necessária |
|---------|----------|-----------------|---------------------------|--------------------------|--------------------------|-----------------|
| **W1** `/api/mercadopago/webhook` | Mercado Pago | `x-signature: ts=...,v1=...` + `x-request-id` | `x-signature: ts=...,v1=...` + `x-request-id` | ✅ Sim (oficial) | ⚠️ **PARCIAL** | (1) Verificar `ts` em segundos vs ms em produção; (2) Adicionar leitura de `data.id` do query param; (3) Aplicar `.lower()` no `data_id` |
| **W2** `/api/tenant/webhook` | Evolution API | `x-webhook-signature: sha256=...` | nenhum por default | ❌ **NÃO** | ❌ **INCOMPATÍVEL** | Trocar para `X-Internal-Token` estático + `compare_digest`, OU usar proxy externo para HMAC |
| **W3** `/api/dr-anderson/criar-lead` | interno (Dr.Anderson Agent) | `X-Internal-Key: <key>` | `X-Internal-Key: <key>` (controlado por nós) | N/A (chave estática) | ✅ **OK** | Nenhuma |
| **W4** `/api/dr-anderson/webhook` | Evolution API | `x-webhook-signature: sha256=...` | nenhum por default | ❌ **NÃO** | ❌ **INCOMPATÍVEL** | Idem W2 |
| **W5** `/api/modulos/webhook` | Mercado Pago (modulos) | `x-webhook-signature: sha256=...` (genérico HMAC) | `x-signature: ts=...,v1=...` + `x-request-id` (formato oficial MP) | ✅ Sim (mas formato diferente) | ❌ **INCOMPATÍVEL** | Trocar para `@mercadopago_webhook_required` (mesmo padrão de W1) |

---

## 5. CENÁRIOS DE REJEIÇÃO LEGÍTIMA (FALSOS 401)

### 5.1 Webhook legítimo que receberia 401

| # | Webhook | Cenário | Probabilidade | Impacto |
|---|---------|---------|---------------|---------|
| 1 | W1 MP | MP enviar `data.id` apenas no query param (mudança futura) | Baixa agora, alta no futuro | 100% de rejeição |
| 2 | W1 MP | `ts` em ms ao invés de segundos (se spec mudar) | Média (doc ambígua) | 100% de rejeição |
| 3 | W2 Evolution | Qualquer webhook Evolution real (default) | **CERTA** | 100% de rejeição |
| 4 | W4 Evolution | Qualquer webhook Evolution real (default) | **CERTA** | 100% de rejeição |
| 5 | W5 MP Modulos | Qualquer webhook MP real | **CERTA** | 100% de rejeição |
| 6 | W1 MP | `data.id` em uppercase (MP começar a usar UUIDs) | Muito baixa | 100% de rejeição |

### 5.2 Retry infinito (cenários)

| # | Webhook | Cenário | Loop? |
|---|---------|---------|-------|
| 1 | W1 | MP retenta 401 → SIAP 401 → MP retenta... | ⚠️ Possível, MP retentaria até desistir |
| 2 | W5 | Idem W1 | ⚠️ **CRÍTICO** — loop até desistência (não é mais 409 idempotente, é 401 direto) |
| 3 | W2/W4 | Evolution não tem retry automático built-in (precisa do operador) | ❌ Sem loop |

**Risco de loop:** Baixo (MP tem circuit breaker próprio), mas possível.

---

## 6. PARECER FINAL — GO ou NO-GO

### 6.1 Análise

| Componente | Status | Severidade |
|------------|--------|-----------|
| W1 MercadoPago | ⚠️ Parcialmente compatível | MÉDIO (funciona na prática se MP mantém formato atual) |
| W2 Evolution tenant | ❌ Incompatível | **BLOQUEADOR** |
| W3 Internal (criar-lead) | ✅ Compatível | OK |
| W4 Evolution Dr.Anderson | ❌ Incompatível | **BLOQUEADOR** |
| W5 Modulos MP | ❌ Incompatível (decorator errado) | **BLOQUEADOR** |

**Total de bloqueadores:** 3 (W2, W4, W5)

### 6.2 Veredito

# 🛑 NO-GO

A FASE 4 + 4.1, no estado atual do código, **NÃO pode ser deployada em produção.**

**Razões:**

1. **W5 (MercadoPago Modulos)** — usa `@hmac_webhook_required` (genérico, espera `x-webhook-signature` + HMAC do body) mas recebe webhooks MP oficiais (`x-signature` + template `id:...;request-id:...;ts:...`). **100% de rejeição dos pagamentos de módulos.**

2. **W2 e W4 (Evolution API)** — esperam `x-webhook-signature: sha256=...` mas Evolution não calcula HMAC nativamente. **100% de rejeição dos webhooks WhatsApp (Dr. Anderson + Multi-Tenant).**

3. **W1 (MercadoPago principal)** — parcialmente compatível. Pode funcionar enquanto MP enviar `data.id` no body E no query param E em segundos. Mas tem 3 defeitos latentes.

### 6.3 Condições para virar GO

**Cada bloqueador precisa de decisão + ação do operador/engenheiro:**

| # | Bloqueador | Opção A (mínima) | Opção B (robusta) | Opção C (proxy) |
|---|-----------|------------------|-------------------|-----------------|
| 1 | W5 Modulos | Trocar decorator para `@mercadopago_webhook_required` (1 linha) | Idem A + extrair `data.id` do query param | Proxy externo |
| 2 | W2/W4 Evolution | Trocar para `@internal_key_required` (chave estática `X-Internal-Token`) | Proxy externo (n8n/Cloudflare Worker) calcula HMAC | — |
| 3 | W1 MP fine-tuning | (N/A — funciona na prática) | Adicionar `data.id` query + `.lower()` + verificar `ts` unidade | — |

**Recomendação pragmática (P0-A):**
- W5 → Opção A (1 linha de mudança + re-testar)
- W2/W4 → Opção A com `X-Internal-Token` estático (4-6 linhas de mudança)
- W1 → Aceitar como está (compatibilidade prática é alta)

**Após essas 3 correções de ~10 linhas, a FASE 4 vira GO.**

### 6.4 Recomendação operacional adicional

**NÃO fazer deploy da FASE 4 + 4.1 em produção AGORA.** Aguardar:
1. Decisão humana sobre as 3 opções acima
2. Correção de 10 linhas no máximo
3. Re-rodar smoke test
4. Re-executar FASE 4.4 com probes em produção

---

## 7. APÊNDICE — Evidências de produção

### 7.1 Probe 1 — W1 MP sem signature
```bash
$ curl -X POST https://api.visualsmartflow.com.br/api/mercadopago/webhook \
    -H "Content-Type: application/json" \
    -d '{"data":{"id":"test"},"type":"payment"}'
HTTP 400 {"status":"error"}
```
**Diagnóstico:** código antigo (pré-FASE 4) — valida payload antes de auth.

### 7.2 Probe 2 — W2 Evolution sem signature
```bash
$ curl -X POST https://api.visualsmartflow.com.br/api/tenant/webhook \
    -H "Content-Type: application/json" \
    -d '{"event":"messages.upsert","instance":"smoke","data":{}}'
HTTP 200 {"reason":"ai_not_configured_or_inactive","status":"ignored"}
```
**Diagnóstico:** código antigo (pré-FASE 4) — entra no handler sem auth.

### 7.3 Probe 3 — W5 Modulos sem signature
```bash
$ curl -X POST https://api.visualsmartflow.com.br/api/modulos/webhook \
    -H "Content-Type: application/json" \
    -d '{"modulo":"base","prof":1}'
HTTP 200 {"expira_em":"2026-07-23T16:43:59.627484","modulo":"base","ok":true,"profissional_id":1,"simulate":false,"status":"active"}
```
**Diagnóstico:** código antigo (pré-FASE 4) — processa sem auth. **Este endpoint é público e desprotegido atualmente.**

### 7.4 Conclusão das probes

**Produção atual:** todos os 5 webhooks (W1, W2, W3, W4, W5) rodam em modo pré-FASE 4. W3 está parcialmente protegido (retorna 403 sem key, mas sem `compare_digest`). W1, W2, W4, W5 estão desprotegidos.

---

## 8. PRÓXIMOS PASSOS

1. ✅ Aguardar revisão humana deste relatório
2. ⏸️ Decidir entre as opções A/B/C para W2, W4, W5
3. ⏸️ Aplicar correções (≤ 10 linhas de código) — **PRECISA APROVAÇÃO HUMANA**
4. ⏸️ Re-rodar FASE 4.2 (smoke test) com payload real
5. ⏸️ Re-executar FASE 4.3 (deploy readiness) com código corrigido
6. ⏸️ Re-executar FASE 4.4 (operational validation) em produção pós-deploy
7. ⏸️ Iniciar FASE 5 (Rate Limit Redis) **somente após aprovação**

---

**⚠️ Parando aqui. NÃO alterei código. NÃO criei commits. NÃO iniciei FASE 5. Aguardando revisão humana das 3 opções de correção para W2/W4/W5.**

---

## Fontes oficiais consultadas

- [Mercado Pago — Webhooks PT-BR](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks)
- [Mercado Pago SDK Go — `pkg/webhook/webhook.go`](https://github.com/mercadopago/sdk-go/blob/main/pkg/webhook/webhook.go)
- [Evolution API — `webhook.controller.ts`](https://github.com/EvolutionAPI/evolution-api/blob/main/src/api/integrations/event/webhook/webhook.controller.ts)
- [Evolution API — `webhook.schema.ts`](https://github.com/EvolutionAPI/evolution-api/blob/main/src/api/integrations/event/webhook/webhook.schema.ts)