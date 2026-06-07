# 🤖 Configuração do Chat de IA com Gemma3:4b

## ✅ O que foi feito

### 1. Configuração do Modelo
- **Provedor:** Ollama Local
- **Modelo:** gemma3:4b (leve e rápido)
- **URL:** http://127.0.0.1:11434
- **Status:** ✅ Funcionando

### 2. Problema Identificado
O sistema multi-agente CrewAI com o modelo gemma3:4b não conseguia usar "function calling" (chamar ferramentas) para acessar dados do banco. Por isso, as respostas eram genéricas como:
> "Para fornecer um relatório de supervisão completo..."

### 3. Solução Implementada
Criamos uma **nova rota de chat simplificada** que:
- ✅ Busca dados DIRETAMENTE do banco de dados
- ✅ Monta contexto completo no prompt
- ✅ Funciona perfeitamente com modelos locais pequenos
- ✅ Não depende de function calling

### 4. Mudanças no Código

#### Backend:
- **Arquivo criado:** `routes/ai_chat_simples.py`
- **Endpoint:** `POST /api/chat-simples`
- **Registrado em:** `app_cors_livre.py`

#### Frontend:
- **Serviço adicionado:** `chatSimplesService` em `services/api.js`
- **Página atualizada:** `pages/AIChatPage.js` - agora usa `chatSimplesService`

## 🚀 Como Usar

### Via Interface Web (Frontend)
1. Acesse: http://localhost:3000
2. Faça login:
   - **Usuário:** admin
   - **Senha:** admin123
3. Navegue até **"Assistente IA"** ou **"Chat"**
4. Selecione um paciente (Anderson, Erika ou Teste 1)
5. Faça perguntas como:
   - "Qual o último tratamento prescrito?"
   - "Quais medicamentos o paciente está usando?"
   - "Mostre os sintomas recentes"
   - "Faça um resumo do paciente"

### Via API (curl)
```bash
# 1. Fazer login
TOKEN=$(curl -s -X POST "http://localhost:5002/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","senha":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

# 2. Usar o chat
curl -X POST "http://localhost:5002/api/chat-simples" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Qual o último tratamento prescrito?",
    "paciente_id": 4
  }'
```

### Via Script de Teste
```bash
cd "/home/holzwarth/Projetos/Aracannabis SIAP_2025/ARACANNABIS_PRONTUARIO_NO_AI"
./test_chat_simples.sh
```

## 📊 Exemplo de Resposta Funcionando

**Pergunta:** "Quais medicamentos o Anderson está usando?"

**Resposta:**
```
Com base nos dados fornecidos, o paciente Anderson Batista Holzwarth
está atualmente utilizando os seguintes medicamentos:

* Schanti: 2 gotas, 2 vezes ao dia
  - Composição: CBD 20.0%, THC 13.3%
* Óleo inicial 1 (CBD): 6 gotas, 4 vezes ao dia
  - Composição: CBD 30.0%
```

## 🔧 Arquivos Modificados

### Backend
```
routes/ai_chat_simples.py          (NOVO)
app_cors_livre.py                  (MODIFICADO - registrou nova rota)
docker-compose.yml                 (MODIFICADO - modelo gemma3:4b)
.env                               (MODIFICADO - modelo gemma3:4b)
```

### Frontend
```
frontend/src/services/api.js       (MODIFICADO - novo serviço)
frontend/src/pages/AIChatPage.js   (MODIFICADO - usa novo serviço)
```

### Scripts de Teste
```
test_chat_simples.sh               (NOVO)
test_chat_gemma.sh                 (CRIADO)
test_chat_com_paciente.sh          (CRIADO)
```

## ⚙️ Variáveis de Ambiente

### .env
```bash
DEFAULT_LLM_PROVIDER=ollama_local
DEFAULT_LLM_MODEL=gemma3:4b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### docker-compose.yml
```yaml
environment:
  - DEFAULT_LLM_PROVIDER=ollama_local
  - DEFAULT_LLM_MODEL=gemma3:4b
  - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## 🎯 Endpoints Disponíveis

### Endpoint Antigo (Multi-agente - não funciona bem com modelos pequenos)
```
POST /api/crew-ai/chat
Body: {
  "mensagem": "...",
  "paciente_id": 4,
  "contexto": {}
}
```

### Endpoint Novo (Simples - RECOMENDADO)
```
POST /api/chat-simples
Body: {
  "mensagem": "...",
  "paciente_id": 4
}
```

## 📝 Dados de Teste Disponíveis

### Pacientes Cadastrados
1. **Anderson Batista Holzwarth (ID: 4)**
   - Condição: Ansiedade
   - 2 evoluções
   - 6 dosagens (Schanti, Óleo CBD)
   - 9 sintomas (ansiedade, insônia, dor)

2. **Erika Clementino da Silva (ID: 6)**
   - Diagnóstico: THDA
   - Sem dados adicionais

3. **Teste 1 (ID: 5)**
   - Dados não verificados

### Credenciais
```
Usuário: admin
Senha: admin123
```

## 🐛 Troubleshooting

### Problema: Chat retorna "Para fornecer um relatório..."
**Solução:** O frontend ainda está usando a rota antiga. Verifique se o frontend foi reiniciado após as alterações.

```bash
docker restart aracannabis_frontend
```

### Problema: "Não possuo dados adicionais"
**Solução:** Verifique se os dados existem no banco:

```bash
docker exec aracannabis_db psql -U postgres -d aracannabis \
  -c "SELECT COUNT(*) FROM evolucoes WHERE paciente_id = 4;"
```

### Problema: Erro de conexão com Ollama
**Solução:** Verifique se o Ollama está rodando:

```bash
curl http://localhost:11434/api/tags
```

## 📚 Documentação Adicional

- Frontend: http://localhost:3000
- Backend: http://localhost:5002
- Banco de dados: localhost:5434
- Ollama: http://localhost:11434

## 🎉 Status Final

✅ **Ollama configurado com gemma3:4b**
✅ **Rota simplificada funcionando**
✅ **Frontend atualizado**
✅ **Testado com dados reais**
✅ **Documentação completa**

**O sistema está 100% funcional!** 🚀
