# Configuração do WhatsApp para SIAP

Guia completo para configurar a integração WhatsApp com segurança.

---

## Opção 1: Evolution API (Recomendado - Open Source)

### 1. Deploy da Evolution API

```bash
# Via Docker Compose
docker run -d \
  --name evolution-api \
  -p 8080:8080 \
  -e AUTHENTICATION_API_KEY=your_random_key_here \
  atendai/evolution-api:latest
```

### 2. Conectar WhatsApp

1. Acesse `http://localhost:8080` (ou seu servidor)
2. Crie uma instância: `POST /instance/create`
```json
{
  "instanceName": "siap",
  "qrcode": true
}
```
3. Escaneie o QR Code com WhatsApp Business
4. Status: `GET /instance/connectionState/siap`

### 3. Configurar Webhook no Evolution API

**CRÍTICO**: Configure o webhook com autenticação!

```bash
curl -X POST http://localhost:8080/webhook/set/siap \
  -H "Content-Type: application/json" \
  -H "apikey: your_random_key_here" \
  -d '{
    "url": "https://seu-dominio.com/api/crew-ai/whatsapp-webhook",
    "webhook_by_events": false,
    "events": ["messages.upsert"],
    "webhook_base64": false,
    "headers": {
      "X-Webhook-Secret": "<SEU_SECRET_AQUI>"
    }
  }'
```

### 4. Configurar Variáveis de Ambiente no SIAP

Adicione ao `.env` (ou variáveis de ambiente do servidor):

```env
# Webhook WhatsApp Security
WEBHOOK_SECRET_KEY=<MESMO_SECRET_CONFIGURADO_NA_EVOLUTION_API>
WEBHOOK_MAX_REQUESTS_PER_MINUTE=10

# IP Whitelist (opcional - separado por vírgulas)
WEBHOOK_IP_WHITELIST=123.456.789.0,98.76.54.32

# Evolution API (para enviar mensagens)
WHATSAPP_API_URL=http://localhost:8080
WHATSAPP_INSTANCE_NAME=siap
WHATSAPP_API_KEY=your_random_key_here
```

### 5. Testar Webhook

```bash
# Simular mensagem do Evolution API
curl -X POST https://seu-dominio.com/api/crew-ai/whatsapp-webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: <SEU_SECRET>" \
  -d '{
    "messages": [{
      "from": "5511999999999@c.us",
      "body": "Olá, quero cadastrar um paciente",
      "id": "test123"
    }]
}'
```

**Resposta esperada**:
```json
{
  "status": "received",
  "responses": [{
    "phone": "5511999999999",
    "message_id": "test123",
    "resposta": "Olá! Para cadastrar um paciente, preciso dos seguintes dados..."
  }]
}
```

---

## Opção 2: Twilio (Pago)

### 1. Criar Conta Twilio

1. Acesse [twilio.com](https://www.twilio.com)
2. Crie conta e configure WhatsApp Business
3. Obtenha credenciais: Account SID + Auth Token

### 2. Configurar Variáveis de Ambiente

```env
WHATSAPP_API_URL=https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json
WHATSAPP_TOKEN=YOUR_AUTH_TOKEN
WEBHOOK_SECRET_KEY=<GERAR_SECRET_ALEATORIO>
```

### 3. Configurar Webhook no Twilio

No dashboard do Twilio:
- WhatsApp > Senders > Configure
- Webhook URL: `https://seu-dominio.com/api/crew-ai/whatsapp-webhook`
- Headers personalizados: `X-Webhook-Secret: <SEU_SECRET>`

---

## Segurança do Webhook

### 1. Gerar Secret Seguro

```bash
# Gerar secret aleatório (use um desses)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# ou
openssl rand -base64 32
```

Exemplo de output: `xK8v2P9mQ4rL7nW1tY6sZ3oA5bC8dE0f`

### 2. Configurações Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `WEBHOOK_SECRET_KEY` | Secret compartilhado (OBRIGATÓRIO) | `xK8v2P9mQ4rL7nW1...` |
| `WEBHOOK_MAX_REQUESTS_PER_MINUTE` | Rate limit | `10` (padrão) |
| `WEBHOOK_IP_WHITELIST` | IPs permitidos (opcional) | `1.2.3.4,5.6.7.8` |

### 3. Logs de Segurança

O sistema registra automaticamente:
- ✅ Acessos autenticados com sucesso
- ⚠️ Tentativas sem autenticação
- ❌ Tentativas com secret inválido
- ⚠️ Rate limit excedido

Exemplo de log:
```
[WARNING] Tentativa de acesso ao webhook WhatsApp sem autenticação do IP: 192.168.1.100
[ERROR] Tentativa de acesso ao webhook WhatsApp com secret inválido do IP: 192.168.1.100
[INFO] Webhook autenticado com sucesso do IP: 192.168.1.50
```

---

## Testando a Integração

### 1. Teste Local (Desenvolvimento)

```bash
# 1. Expor localhost via ngrok (para testes)
ngrok http 5002

# 2. Anotar URL pública
# https://abc123.ngrok.io

# 3. Configurar webhook na Evolution API com a URL do ngrok
# https://abc123.ngrok.io/api/crew-ai/whatsapp-webhook
```

### 2. Comandos de Teste via WhatsApp

Envie mensagens para o número conectado:

```
1. "Listar meus pacientes"
   → Deve retornar lista de pacientes

2. "Cadastrar paciente João Silva, CPF 12345678900, nascimento 15/03/1990"
   → Deve criar paciente

3. "Buscar paciente ID 3"
   → Deve retornar dados do paciente

4. "Gerar prescrição para paciente João: Canabidiol 200mg/ml, 3 gotas 2x ao dia"
   → Deve gerar prescrição (quando implementado)
```

### 3. Verificar Logs

```bash
docker logs siap-api --tail 50 -f
```

Procure por:
- `Webhook WhatsApp autenticado recebido`
- `Mensagem WhatsApp de 5511999999999`
- `Resposta gerada para WhatsApp`

---

## Troubleshooting

### Problema: "Autenticação necessária"

**Causa**: Header `X-Webhook-Secret` não está sendo enviado

**Solução**:
1. Verificar configuração do webhook na Evolution API
2. Garantir que headers personalizados estão configurados:
```json
{
  "headers": {
    "X-Webhook-Secret": "seu_secret_aqui"
  }
}
```

### Problema: "Autenticação falhou"

**Causa**: Secret do webhook não coincide com `WEBHOOK_SECRET_KEY`

**Solução**:
1. Verificar `.env` do SIAP: `echo $WEBHOOK_SECRET_KEY`
2. Verificar configuração da Evolution API
3. Regenerar secret e reconfigurar ambos

### Problema: "Rate limit excedido"

**Causa**: Muitas mensagens em curto período (padrão: 10/min)

**Solução**:
1. Aguardar 1 minuto
2. Aumentar limite: `WEBHOOK_MAX_REQUESTS_PER_MINUTE=20`
3. Implementar fila de mensagens (futuro)

### Problema: "IP não autorizado"

**Causa**: IP da Evolution API não está no whitelist

**Solução**:
1. Descobrir IP da Evolution API: `curl ifconfig.me`
2. Adicionar ao `.env`: `WEBHOOK_IP_WHITELIST=1.2.3.4,5.6.7.8`
3. Reiniciar backend: `docker restart siap-api`

---

## Produção - Checklist

- [ ] `WEBHOOK_SECRET_KEY` configurado com secret forte (32+ chars)
- [ ] Evolution API rodando em servidor com HTTPS
- [ ] Webhook configurado com URL HTTPS do SIAP
- [ ] Rate limiting ativo (`WEBHOOK_MAX_REQUESTS_PER_MINUTE`)
- [ ] IP whitelist configurado (opcional mas recomendado)
- [ ] Logs de segurança monitorados
- [ ] Backup de configuração da Evolution API
- [ ] Teste de failover (o que acontece se Evolution API cair?)

---

## Próximos Recursos

- [ ] Mapear telefone → profissional (modelo `ProfissionalTelefone`)
- [ ] Enviar mensagens proativamente (lembretes, confirmações)
- [ ] Suporte a mídia (imagens, áudio, documentos)
- [ ] Fila de mensagens (processamento assíncrono)
- [ ] Dashboard de analytics (mensagens enviadas/recebidas)
