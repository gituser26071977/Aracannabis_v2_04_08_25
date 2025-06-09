# 📧 SISTEMA DE LEMBRETES - ARACANNABIS

## 🎯 **Como Funcionam os Lembretes**

O sistema de lembretes do Aracannabis envia notificações automáticas para pacientes sobre suas consultas agendadas.

## 📋 **Funcionalidades Principais**

### **1. Detecção Automática**
- ✅ **Busca consultas** das próximas 24 horas
- ✅ **Filtra por status** (agendada/confirmada)
- ✅ **Evita duplicação** (só envia se ainda não foi enviado)

### **2. Canais de Comunicação**
- 📧 **Email** - Via SMTP configurável
- 📱 **WhatsApp** - Via API externa (Twilio, etc.)

### **3. Controle de Envio**
- ✅ **Flags no banco** (`lembrete_email_enviado`, `lembrete_whatsapp_enviado`)
- ✅ **Prevenção de spam** - não reenvia lembretes já enviados
- ✅ **Log de atividades** - registra quantos lembretes foram enviados

## ⚙️ **Configuração dos Lembretes**

### **📧 Email (SMTP)**

Adicione as seguintes variáveis no arquivo `.env`:

```bash
# Configurações de Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app

# Para Gmail, use senha de aplicativo:
# 1. Ative autenticação de 2 fatores
# 2. Gere uma senha de aplicativo
# 3. Use essa senha no EMAIL_PASSWORD
```

### **📱 WhatsApp (API Externa)**

```bash
# Configurações do WhatsApp
WHATSAPP_API_URL=https://api.twilio.com/2010-04-01/Accounts/SEU_SID/Messages.json
WHATSAPP_TOKEN=seu-token-twilio

# Ou use outras APIs como:
# - WhatsApp Business API
# - Evolution API
# - Baileys
```

## 🚀 **Como Usar**

### **1. Via Interface Web**
1. Acesse a página **Consultas**
2. Clique no botão **"Lembretes"**
3. Sistema enviará automaticamente para consultas das próximas 24h

### **2. Via API**
```bash
POST /api/consultas/lembretes/enviar
Authorization: Bearer SEU_TOKEN
```

### **3. Automação (Futuro)**
- **Cron Job** - Executar diariamente
- **Scheduler** - Agendar envios automáticos
- **Webhook** - Integrar com sistemas externos

## 📝 **Modelo de Mensagens**

### **📧 Email**
```
Assunto: Lembrete de Consulta - Aracannabis

Olá [NOME_PACIENTE],

Este é um lembrete da sua consulta agendada para [DATA] às [HORA].

Tipo: [PRESENCIAL/TELEMEDICINA]
Duração: [X] minutos

[OBSERVAÇÕES se houver]

Em caso de dúvidas ou necessidade de reagendamento, 
entre em contato conosco.

Atenciosamente,
Equipe Aracannabis
```

### **📱 WhatsApp**
```
🏥 *Lembrete de Consulta - Aracannabis*

Olá [NOME_PACIENTE]!

Você tem uma consulta agendada para *[DATA] às [HORA]*.

📋 Tipo: [PRESENCIAL/TELEMEDICINA]
⏰ Duração: [X] minutos

📝 Observações: [SE HOUVER]

Em caso de dúvidas, entre em contato conosco.
```

## 🔧 **Status Atual do Sistema**

### **✅ Implementado**
- ✅ **API de lembretes** funcionando
- ✅ **Detecção de consultas** das próximas 24h
- ✅ **Estrutura de email** SMTP
- ✅ **Estrutura de WhatsApp** preparada
- ✅ **Controle de duplicação**
- ✅ **Interface web** com botão

### **⚠️ Requer Configuração**
- ⚙️ **Variáveis de ambiente** (.env)
- ⚙️ **Conta SMTP** (Gmail, Outlook, etc.)
- ⚙️ **API WhatsApp** (Twilio, etc.)

## 🧪 **Como Testar**

### **1. Configurar Email**
```bash
# No arquivo .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app
```

### **2. Criar Consulta de Teste**
1. Agende uma consulta para **hoje** ou **amanhã**
2. Certifique-se que o paciente tem **email** cadastrado

### **3. Enviar Lembrete**
1. Vá em **Consultas**
2. Clique em **"Lembretes"**
3. Verifique o console do backend para logs

### **4. Verificar Resultado**
- ✅ **Sucesso**: Mensagem "X lembretes enviados"
- ❌ **Erro**: "Configurações não encontradas"

## 📊 **Logs e Monitoramento**

### **Backend Console**
```bash
# Sucesso
Configurações de email encontradas
Lembrete enviado para: paciente@email.com

# Erro
Configurações de email não encontradas
Configurações do WhatsApp não encontradas
```

### **Banco de Dados**
```sql
-- Verificar lembretes enviados
SELECT * FROM consultas 
WHERE lembrete_email_enviado = true 
   OR lembrete_whatsapp_enviado = true;

-- Verificar logs
SELECT * FROM logs_atividades 
WHERE acao = 'Lembretes' 
ORDER BY data_hora DESC;
```

## 🔮 **Melhorias Futuras**

### **Automação**
- ⏰ **Cron Job** diário às 9h
- 📅 **Múltiplos lembretes** (24h, 2h antes)
- 🔄 **Reagendamento** via link

### **Personalização**
- 🎨 **Templates** customizáveis
- 🌐 **Múltiplos idiomas**
- 📋 **Campos dinâmicos**

### **Integrações**
- 📱 **SMS** via Twilio
- 📧 **Email marketing** (Mailchimp)
- 🔔 **Push notifications**

## 🆘 **Solução de Problemas**

### **"Configurações não encontradas"**
- ✅ Verifique o arquivo `.env`
- ✅ Reinicie o servidor backend
- ✅ Confirme as variáveis de ambiente

### **"Erro ao enviar email"**
- ✅ Verifique credenciais SMTP
- ✅ Use senha de aplicativo (Gmail)
- ✅ Confirme porta e servidor

### **"Nenhum lembrete enviado"**
- ✅ Verifique se há consultas nas próximas 24h
- ✅ Confirme que pacientes têm email/telefone
- ✅ Verifique se lembretes já foram enviados

---

**💡 Dica**: Para testar rapidamente, crie uma consulta para hoje e configure apenas o email. O WhatsApp pode ser configurado posteriormente.
