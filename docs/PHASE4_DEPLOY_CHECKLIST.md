# PHASE 4 — DEPLOY CHECKLIST (P0-A)

**Data:** 2026-06-22
**Branch:** `feat/clinica-management`
**Destino:** VPS Hostinger (`api.visualsmartflow.com.br`)

---

## PRÉ-DEPLOY (operador)

### Geração de secrets

```bash
# Em máquina segura, gerar 5 secrets (cada um independente):
python3 -c "import secrets; print('MERCADOPAGO_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('MERCADOPAGO_MODULOS_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('EVOLUTION_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('DR_ANDERSON_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('INTERNAL_SERVICE_KEY=' + secrets.token_urlsafe(32))"
```

⚠️ **CRÍTICO — MercadoPago:**
- `MERCADOPAGO_WEBHOOK_SECRET` e `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` devem ter **O MESMO VALOR** porque o painel MP aceita 1 secret por aplicação.
- Provisione o mesmo secret em `/api/mercadopago/webhook` e `/api/modulos/webhook`.

### Adicionar secrets ao `.env.production`

```bash
# No VPS:
cd /var/www/araos  # ou diretório do projeto
nano .env.production

# Adicionar:
MERCADOPAGO_WEBHOOK_SECRET=<gerado_acima>
MERCADOPAGO_MODULOS_WEBHOOK_SECRET=<mesmo_valor>
EVOLUTION_WEBHOOK_SECRET=<gerado_acima>
DR_ANDERSON_WEBHOOK_SECRET=<gerado_acima>
INTERNAL_SERVICE_KEY=<gerado_acima>
ALLOW_WEBHOOK_SIMULATION=0
```

### Provisionar MercadoPago

1. Acessar [Mercado Pago Developers → Suas integrações → Webhooks](https://www.mercadopago.com.br/developers/panel/notifications/webhooks)
2. Configurar a URL: `https://api.visualsmartflow.com.br/api/mercadopago/webhook`
3. **Provisionar o mesmo secret** usado para `MERCADOPAGO_WEBHOOK_SECRET` no campo "Secret"
4. **Provisionar o mesmo secret** também para URL `https://api.visualsmartflow.com.br/api/modulos/webhook`

### Provisionar Evolution API

**Opção A — HMAC (recomendado se Evolution suporta proxy):**
```bash
curl -X POST http://evolution-api:8080/webhook/set/<instance> \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.visualsmartflow.com.br/api/tenant/webhook",
    "events": ["messages.upsert"],
    "webhook_by_events": false,
    "headers": {
      "x-webhook-signature": "sha256={{hmac_sha256(body, EVOLUTION_WEBHOOK_SECRET)}}"
    }
  }'
```

**Opção B — Token fixo (alternativa se Evolution não suporta HMAC):**
- Configurar Evolution para enviar `X-Internal-Token: <EVOLUTION_WEBHOOK_SECRET>` em headers customizados
- Atualizar decorator `@hmac_webhook_required` em `routes/dynamic_tenant_webhook.py` e `routes/dr_anderson_webhook.py` para usar `validate_internal_key` em vez de HMAC
- **(Requer pequena alteração de código — fazer em P1 se necessário)**

### Backup

```bash
# Backup do banco (caso rollback precise restaurar tabela webhook_logs)
docker exec siap-db pg_dump -U siap_user -d aracannabis > /backup/backup_pre_fase4_$(date +%Y%m%d_%H%M%S).sql

# Backup do .env.production
cp .env.production .env.production.bak.pre_fase4
```

### Validar ambiente

```bash
# No VPS, validar se todas as 5 vars estão presentes:
grep -E "MERCADOPAGO_WEBHOOK_SECRET|MERCADOPAGO_MODULOS_WEBHOOK_SECRET|EVOLUTION_WEBHOOK_SECRET|DR_ANDERSON_WEBHOOK_SECRET|INTERNAL_SERVICE_KEY" .env.production

# Esperado: 5 linhas, cada uma com valor não-vazio
```

---

## DEPLOY

### Pull do código

```bash
cd /var/www/araos
git fetch origin
git checkout feat/clinica-management
git pull origin feat/clinica-management
```

### Rebuild imagem Docker

```bash
docker compose -f docker-compose.prod.yml build siap-backend --no-cache
```

### Aplicar migrations (se houver)

```bash
# Migrations são aplicadas automaticamente pelo entrypoint_siap.sh via 'flask db upgrade'
# Mas pode aplicar manualmente para confirmar:
docker compose -f docker-compose.prod.yml run --rm siap-backend flask db upgrade
```

⚠️ Para FASE 4 + 4.1, **não há migrations novas** (webhook_logs já existe desde 2026-06-07).

### Restart container

```bash
docker compose -f docker-compose.prod.yml up -d siap-backend
```

### Acompanhar logs

```bash
docker logs -f siap-backend 2>&1 | grep -E "STARTUP|webhook|RuntimeError|ERROR"
```

**Esperado nas primeiras linhas:**
```
[webhook_auth] ABORT STARTUP: ...  # se faltar algum secret (deve NÃO aparecer)
Config: ... segredos validados com sucesso.
AraOS SERVER STARTED!
```

---

## PÓS-DEPLOY (verificações imediatas)

### Smoke test 1 — Aplicação subiu?

```bash
curl -sS -o /dev/null -w "HTTP %{http_code}\n" https://api.visualsmartflow.com.br/api/status
# Esperado: HTTP 200
```

### Smoke test 2 — Auth funcionando?

```bash
# Sem signature — esperado HTTP 401 (NÃO 400, NÃO 200)

# W1 MercadoPago
curl -sS -o /dev/null -w "W1 MP: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"test":"smoke"}' \
  https://api.visualsmartflow.com.br/api/mercadopago/webhook
# Esperado: HTTP 401

# W5 Modulos
curl -sS -o /dev/null -w "W5 Modulos: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"modulo":"nutrologia","prof":1}' \
  https://api.visualsmartflow.com.br/api/modulos/webhook
# Esperado: HTTP 401

# W2 Evolution tenant
curl -sS -o /dev/null -w "W2 Tenant: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","instance":"clinica01","data":{}}' \
  https://api.visualsmartflow.com.br/api/tenant/webhook
# Esperado: HTTP 401

# W4 Evolution Dr.Anderson
curl -sS -o /dev/null -w "W4 DrAnderson: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"event":"messages.upsert","data":{}}' \
  https://api.visualsmartflow.com.br/api/dr-anderson/webhook
# Esperado: HTTP 401

# W3 criar-lead (sem internal-key)
curl -sS -o /dev/null -w "W3 Lead: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -d '{"nome":"Test"}' \
  https://api.visualsmartflow.com.br/api/dr-anderson/criar-lead
# Esperado: HTTP 401
```

### Smoke test 3 — Logs estruturados

```bash
# Verificar que logs contêm provider + event_id (sem payload sensível)
docker logs siap-backend 2>&1 | grep -E "mercadopago|evolution|modulos|dr_anderson" | head -10
# Esperado: linhas com WARNING/INFO contendo provider name e event_id
```

### Smoke test 4 — WebhookLogs sendo criados

```bash
# Conectar ao banco e contar registros
docker exec -it siap-db psql -U siap_user -d aracannabis -c \
  "SELECT provider, COUNT(*) FROM webhook_logs WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY provider;"
# Esperado: providers mercadopago, evolution_tenant, evolution_dr_anderson, modulos
```

---

## SMOKE TEST (operador — opcional, recomendado)

### W1 MercadoPago com signature válida

```bash
# Em máquina com Python:
python3 <<EOF
import hashlib, hmac, json, time, requests

SECRET = "$MERCADOPAGO_WEBHOOK_SECRET"
data_id = "99999999"
x_req_id = "smoke-test-001"
ts = int(time.time())
template = f"id:{data_id};request-id:{x_req_id};ts:{ts};"
sig = hmac.new(SECRET.encode(), template.encode(), hashlib.sha256).hexdigest()
x_signature = f"ts={ts},v1={sig}"

payload = {"data": {"id": data_id}, "type": "payment"}

resp = requests.post(
    "https://api.visualsmartflow.com.br/api/mercadopago/webhook",
    headers={
        "Content-Type": "application/json",
        "x-signature": x_signature,
        "x-request-id": x_req_id,
    },
    json=payload,
    timeout=10,
)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
EOF
# Esperado primeira vez: HTTP 200 (processado)
# Esperado segunda vez (mesmo data_id): HTTP 200 idempotente=true
```

### W2 Evolution com signature válida

```bash
python3 <<EOF
import hashlib, hmac, json, requests

SECRET = "$EVOLUTION_WEBHOOK_SECRET"
body = json.dumps({
    "event": "messages.upsert",
    "instance": "smoke-clinica",
    "data": {"key": {"id": "smoke-msg-001"}}
})
sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()

resp = requests.post(
    "https://api.visualsmartflow.com.br/api/tenant/webhook",
    headers={
        "Content-Type": "application/json",
        "x-webhook-signature": f"sha256={sig}",
    },
    data=body,
    timeout=10,
)
print(f"Status: {resp.status_code}")
print(f"Body: {resp.text}")
EOF
```

### W3 Internal Key com chave correta

```bash
curl -sS -o /dev/null -w "W3: HTTP %{http_code}\n" -X POST \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: $INTERNAL_SERVICE_KEY" \
  -d '{"nome":"Smoke Test","data_nascimento":"1990-01-01"}' \
  https://api.visualsmartflow.com.br/api/dr-anderson/criar-lead
# Esperado: HTTP 201 (criado) ou 500 (se paciente duplicado) — NUNCA 401/403
```

---

## ROLLBACK (se necessário)

### Cenário 1 — App não sobe (RuntimeError)

```bash
# Verificar log
docker logs siap-backend 2>&1 | grep -i "abort\|missing\|required"
# Esperado: indica qual ENV está faltando

# Adicionar env faltando e restart
nano .env.production
docker compose -f docker-compose.prod.yml up -d siap-backend
```

### Cenário 2 — Webhook legítimo sendo rejeitado

```bash
# Verificar se 401 está acontecendo para webhooks reais
docker logs siap-backend 2>&1 | grep -E "rejeitado|invalid signature" | tail -20

# Se falso positivo (assinatura Evolution não bate):
# 1. Verificar configuração Evolution API
# 2. Confirmar que secret Evolution = $EVOLUTION_WEBHOOK_SECRET
# 3. Reenviar webhook manualmente via Evolution dashboard
```

### Cenário 3 — Rollback total

```bash
cd /var/www/araos

# 1. Identificar commit da FASE 4
git log --oneline -10

# 2. Reverter
git revert <commit-hash-fase4> --no-edit

# 3. Rebuild + restart
docker compose -f docker-compose.prod.yml build siap-backend
docker compose -f docker-compose.prod.yml up -d siap-backend

# 4. (Opcional) Restaurar .env.production antigo
cp .env.production.bak.pre_fase4 .env.production
docker compose -f docker-compose.prod.yml up -d siap-backend

# 5. Verificar
curl -sS https://api.visualsmartflow.com.br/api/status
docker logs siap-backend 2>&1 | tail -20
```

### Cenário 4 — Bypass de emergência (NÃO RECOMENDADO)

```bash
# Desabilitar startup check temporariamente (NÃO USAR EM PRODUÇÃO REAL)
nano .env.production
# Mudar: FLASK_ENV=development
docker compose -f docker-compose.prod.yml up -d siap-backend

# ⚠️ Todos os webhooks ficam SEM autenticação neste modo.
# Use apenas para debug, restaure ASAP.
```

---

## CHECKLIST FINAL

- [ ] 5 secrets gerados e adicionados ao `.env.production`
- [ ] Mesmo secret MP provisionado para W1 e W5 no painel MP
- [ ] Evolution API configurada para enviar `x-webhook-signature`
- [ ] Backup do banco (`pg_dump`)
- [ ] Backup do `.env.production` (`.bak.pre_fase4`)
- [ ] `git pull` no VPS
- [ ] `docker compose build siap-backend`
- [ ] `docker compose up -d siap-backend`
- [ ] Logs sem `RuntimeError` / `ABORT STARTUP`
- [ ] `/api/status` retorna 200
- [ ] Todos os 5 webhooks retornam **401** sem signature (NÃO 400, NÃO 200)
- [ ] WebhookLogs sendo criados no banco
- [ ] (Opcional) Smoke test com signature válida retorna 200

**Após todos os checks:** ✅ FASE 4 deployada com sucesso.

---

**⚠️ Este checklist é para uso do operador. NÃO inicia FASE 5 automaticamente. NÃO cria novas funcionalidades. Aguarda revisão humana.**