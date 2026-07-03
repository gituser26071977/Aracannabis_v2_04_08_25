# TELEGRAM_SETUP.md

**Versão:** 1.0 (D05k) **Status:** substitui `docs/WHATSAPP_SETUP.md` (legado).

**Propósito:** Provisionar bots do Telegram Bot API para receber webhooks do
SIAP (substitui Evolution API descontinuada em D05k).

---

## Por que Telegram (em vez de Evolution/WhatsApp)

A Evolution API é um gateway não-oficial para WhatsApp. Problemas:

- Risco de bloqueio pelo Meta (ToS) — pode cair a qualquer momento.
- Dependência de QR code + reconexão manual.
- Sem SLA, sem suporte oficial.

**Telegram Bot API** é oficial, estável e sem risco de bloqueio:

- 100% HTTP (sem socket persistente).
- Webhook com auth por header `X-Telegram-Bot-Api-Secret-Token`.
- Setup via `@BotFather` (oficial Telegram).
- Limite generoso: 30 msgs/s por bot, sem custo.

---

## Quando você precisa de um bot Telegram

| Caso                                      | Bot necessário                                       |
| REDACTED | REDACTED |
| Dr.Anderson recebe admin notif (cadastro) | 1 bot fixo (`TELEGRAM_DEFAULT_BOT_TOKEN`)            |
| Clínica X tem multi-tenant SDR            | 1 bot dedicado (`ConfiguracaoIA.telegram_bot_token`) |
| Desenvolvimento local (smoke test)        | 1 bot de teste (criado em segundos)                  |

---

## Passo a passo — provisionar 1 bot

### 1. Criar o bot via @BotFather

No Telegram, abra conversa com [@BotFather](https://t.me/BotFather) e rode:

```
/newbot
Nome: AraOS Dr.Anderson
Username: araos_dr_anderson_bot   # precisa terminar em 'bot'
```

O BotFather responde com o token HTTP. **Guarde com cuidado** (é o que vai para
`TELEGRAM_DEFAULT_BOT_TOKEN` no `.env`).

### 2. Definir o webhook

Com o token em mãos, registrar a URL pública do webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://api.visualsmartflow.com.br/webhooks/telegram",
    "secret_token": "<32+ chars aleatórios>",
    "drop_pending_updates": true
  }'
```

Onde `<32+ chars aleatórios>` é o `TELEGRAM_WEBHOOK_SECRET` (ou
`REDACTED` para o bot dedicado). O backend compara o
header `X-Telegram-Bot-Api-Secret-Token` com esse valor via
`hmac.compare_digest`.

### 3. Capturar o chat_id do admin

Para admin notif, é preciso saber o `chat_id` Telegram do destinatário.

**Método simples:** a pessoa manda `/start` para o bot. Quando o webhook recebe,
o `chat_id` está em `message.chat.id`. Você pode:

a) Ver nos logs do backend após o primeiro `/start` (print do chat_id). b) Rodar
o script de captura:

```bash
python tools/register_notification_chat.py <TOKEN>
# Siga as instruções interativas.
```

O valor vai para `TELEGRAM_ADMIN_CHAT_ID` no `.env`.

### 4. Configurar o `.env` do SIAP

```bash
# .env (ou .env.production)
TELEGRAM_DEFAULT_BOT_TOKEN=123456:ABC-DEF...   # do @BotFather
TELEGRAM_ADMIN_CHAT_ID=987654321               # seu chat_id pessoal
```

(Opcional, para o bot dedicado do Dr.Anderson):

```bash
REDACTED=32chars_random
```

### 5. Validar

```bash
# 5.1 — bot existe?
curl https://api.telegram.org/bot<TOKEN>/getMe
# esperado: {"ok": true, "result": {"username": "...", ...}}

# 5.2 — webhook configurado?
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
# esperado: url = "https://api.visualsmartflow.com.br/webhooks/telegram"

# 5.3 — enviar mensagem de teste
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "<TELEGRAM_ADMIN_CHAT_ID>", "text": "teste ✅"}'
```

---

## Multi-tenant (uma clínica = 1 bot)

Decisão D05k: cada tenant (clínica) ganha bot Telegram dedicado. O backend
resolve via header `X-Telegram-Bot-Api-Secret-Token` + lookup em
`ConfiguracaoIA`.

**Setup por clínica:**

1. Cliente cria bot via @BotFather (Dr.Anderson ou admin da clínica).
2. Cliente configura `ConfiguracaoIA` com 3 campos:
   - `telegram_bot_token` — token do bot
   - `telegram_webhook_secret` — 32+ chars (header `secret_token`)
   - `telegram_notification_chat_id` — chat_id onde enviar notificações
3. Cliente aponta o webhook do bot para o endpoint multi-tenant do SIAP:
   `https://api.visualsmartflow.com.br/api/tenant/webhooks/telegram`
4. Backend valida o secret por tenant e despacha para `DynamicTenantAgent`.

> **Operação cara**: cada bot precisa de aprovação via @BotFather. Para escalar
> além de ~5 clínicas, considerar Fase 2 com auto-registro via painel admin.
> Fora de escopo D05k.

---

## Substituição do WhatsAppService (legado)

D05k removeu `services/whatsapp_service.py` (compartilhava a Evolution API).
`notify_admin_new_registration` e `notify_doctor_approval` agora vivem em
`services/telegram_service.py` — usam `TELEGRAM_DEFAULT_BOT_TOKEN` +
`TELEGRAM_ADMIN_CHAT_ID`.

| Função legada                                         | Nova função                                              |
| REDACTED | REDACTED |
| `WhatsAppService.send_message(phone, text)`           | `telegram_service.send_message(chat_id, text)`           |
| `WhatsAppService.notify_admin_new_registration(...)`  | `telegram_service.notify_admin_new_registration(...)`    |
| `WhatsAppService.notify_doctor_approval(phone, nome)` | `telegram_service.notify_doctor_approval(chat_id, nome)` |

> **Nota:** a semântica mudou de telefone → chat_id. Se `paciente.telefone`
> estiver com DDI/número, **não** é mais usado pelo TelegramService. O caller é
> responsável por armazenar o `chat_id` correto em algum lugar do modelo de
> dados (fora de escopo desta missão — usar `paciente.telefone` como proxy foi
> feito em `routes/consultas.py` para preservar comportamento).

---

## Cleanup Evolution API (concluído em D05k)

Removido:

- `services/whatsapp_service.py` (mantido como stub vazio para imports legacy).
- Env vars `WHATSAPP_API_URL`, `WHATSAPP_API_KEY`, `WHATSAPP_INSTANCE_NAME`,
  `WHATSAPP_ADMIN_PHONE`, `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`,
  `EVOLUTION_WEBHOOK_SECRET`.
- Rota `/api/dr-anderson/webhook` (Evolution) — substituída por
  `/api/dr-anderson/webhooks/telegram` (Telegram).
- Rota `/api/tenant/webhook` (Evolution) — substituída por
  `/api/tenant/webhooks/telegram` (Telegram).
- Rota `/webhook` em `routes/sdr.py` (Evolution) — substituída por
  `/webhooks/telegram`.
- Rota `/webhook/teste-mensagem` em `routes/sdr.py` — convertida para Telegram.

**Backward-compat:** rotas antigas retornam `410 Gone` com mensagem
`"evolution_api_migrated_to_telegram"` apontando para a nova rota.

---

## Pendências externas

- Remover rede Docker `evolution_evolution-net` se ainda existir (fora do escopo
  D05k — `docker network ls` no VPS para confirmar).
- Limpar vars `EVOLUTION_*` em `.env.production` (deploy manual via fluxo
  normal, não via código).
- Provisionar os 2 webhooks reais do Mercado Pago no MP Developers (D05e F8 —
  ação do operador).

---

## Referências

- `services/telegram_service.py` — wrapper HTTP para Bot API.
- `routes/sdr.py:webhook_telegram_sdr` — webhook LIA/Dr.Anderson.
- `routes/dr_anderson_webhook.py:telegram_webhook` — webhook Dr.Anderson SDR.
- `routes/dynamic_tenant_webhook.py:telegram_webhook_multi_tenant` —
  multi-tenant.
- `.env.example` — vars de exemplo.
- `docs/SECRETS_INVENTORY.md` — inventário completo de secrets.

---

**Responsável:** engenharia **Próxima revisão:** ao provisionar o primeiro bot
real de clínica.
