#!/bin/bash
# Teste final do chat de IA com gemma3:4b

echo "════════════════════════════════════════════════════════════"
echo "  🤖 TESTE FINAL - CHAT DE IA COM GEMMA3:4B"
echo "════════════════════════════════════════════════════════════"
echo ""

BASE_URL="http://localhost:5002/api"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verificando serviços..."
echo ""

# 1. Verificar Ollama
echo -n "1. Ollama (localhost:11434)... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${RED}✗ Offline${NC}"
    echo "   Execute: ollama serve"
    exit 1
fi

# 2. Verificar Backend
echo -n "2. Backend (localhost:5002)... "
if curl -s http://localhost:5002/api/ai-config/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${RED}✗ Offline${NC}"
    echo "   Execute: docker-compose up -d backend"
    exit 1
fi

# 3. Verificar Frontend
echo -n "3. Frontend (localhost:3000)... "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${YELLOW}⚠ Offline (não crítico)${NC}"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  📊 CONFIGURAÇÃO ATUAL"
echo "════════════════════════════════════════════════════════════"
echo ""

CONFIG=$(curl -s http://localhost:5002/api/ai-config/health)
PROVIDER=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin).get('default_provider', 'N/A'))" 2>/dev/null)
MODEL=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin).get('default_model', 'N/A'))" 2>/dev/null)

echo "Provedor: $PROVIDER"
echo "Modelo: $MODEL"
echo ""

# 4. Fazer login
echo "════════════════════════════════════════════════════════════"
echo "  🔐 AUTENTICAÇÃO"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Fazendo login como admin..."

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","senha":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}✗ Erro ao fazer login${NC}"
    echo "Resposta: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Login bem-sucedido${NC}"
echo ""

# 5. Testar chat COM paciente (Anderson)
echo "════════════════════════════════════════════════════════════"
echo "  💬 TESTE DO CHAT COM PACIENTE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Paciente: Anderson Batista Holzwarth (ID: 4)"
echo "Pergunta: 'Qual o último tratamento prescrito?'"
echo ""
echo "⏳ Enviando mensagem..."
echo ""

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/chat-simples" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Qual o último tratamento prescrito para o paciente? Liste os medicamentos, dosagens e concentrações.",
    "paciente_id": 4
  }')

echo "────────────────────────────────────────────────────────────"
echo "📥 RESPOSTA DO ASSISTENTE:"
echo "────────────────────────────────────────────────────────────"
echo ""

RESPOSTA=$(echo "$CHAT_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    resposta = data.get('resposta', 'Sem resposta')
    print(resposta)
    print()
    print('Model: {}/{}'.format(data.get('provider', 'N/A'), data.get('model', 'N/A')))
    print('Contexto carregado: {}'.format('Sim' if data.get('tem_contexto') else 'Não'))
except Exception as e:
    print('Erro ao processar resposta:', e)
    print('Resposta bruta:', sys.stdin.read())
" 2>&1)

echo "$RESPOSTA"
echo ""

# Verificar se a resposta é válida (não é a resposta genérica de supervisor)
if echo "$RESPOSTA" | grep -qi "relatório de supervisão\|coordenar tarefas"; then
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${RED}❌ TESTE FALHOU${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "O chat ainda está retornando respostas genéricas."
    echo "Isso significa que o frontend ainda está usando a rota antiga."
    echo ""
    echo "SOLUÇÃO:"
    echo "1. Limpe o cache do navegador (Ctrl+Shift+R)"
    echo "2. Ou execute: docker restart aracannabis_frontend"
    echo "3. Aguarde 30 segundos e recarregue a página"
    echo ""
elif echo "$RESPOSTA" | grep -qi "medicamento\|dosagem\|schanti\|cbd\|thc"; then
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${GREEN}✅ TESTE BEM-SUCEDIDO!${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "O chat está funcionando corretamente!"
    echo "O assistente está acessando e analisando os dados do paciente."
    echo ""
    echo "Próximos passos:"
    echo "1. Acesse: http://localhost:3000"
    echo "2. Faça login (admin/admin123)"
    echo "3. Navegue até 'Assistente IA'"
    echo "4. Selecione um paciente e faça perguntas"
    echo ""
else
    echo "════════════════════════════════════════════════════════════"
    echo -e "  ${YELLOW}⚠ RESULTADO INCONCLUSIVO${NC}"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "A resposta não contém palavras-chave esperadas."
    echo "Verifique manualmente se os dados do paciente foram incluídos."
    echo ""
fi

echo "════════════════════════════════════════════════════════════"
echo "  📋 RESUMO"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Ollama:   ✓"
echo "Backend:  ✓"
echo "Modelo:   $MODEL"
echo "Endpoint: /api/chat-simples"
echo ""
echo "Documentação completa: CHAT_IA_CONFIGURACAO.md"
echo ""
