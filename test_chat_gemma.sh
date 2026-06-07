#!/bin/bash
# Script de teste para o chat de IA com Gemma3:4b

BASE_URL="http://localhost:5002/api"

echo "==========================================================="
echo "  TESTE DO CHAT DE IA COM GEMMA3:4B (OLLAMA LOCAL)"
echo "==========================================================="
echo ""

# 1. Verificar configuração da IA
echo "1. VERIFICANDO CONFIGURAÇÃO DA IA"
echo "REDACTED"
curl -s "$BASE_URL/ai-config/health" | python3 -m json.tool
echo ""
echo ""

# 2. Fazer login (ajuste email e senha conforme necessário)
echo "2. FAZENDO LOGIN"
echo "REDACTED"
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","senha":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Erro: Não foi possível fazer login"
  echo "   Verifique as credenciais no script ou crie um usuário admin"
  exit 1
fi

echo "✓ Login bem-sucedido!"
echo ""
echo ""

# 3. Listar pacientes
echo "3. LISTANDO PACIENTES"
echo "REDACTED"
PACIENTES=$(curl -s "$BASE_URL/pacientes" \
  -H "Authorization: Bearer $TOKEN")

echo "$PACIENTES" | python3 -m json.tool | head -30
echo ""

PACIENTE_ID=$(echo "$PACIENTES" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['pacientes'][0]['id'] if data.get('pacientes') else '')" 2>/dev/null)

echo ""

# 4. Testar chat SEM contexto de paciente
echo "4. TESTANDO CHAT SEM CONTEXTO DE PACIENTE"
echo "REDACTED"
echo "📤 Enviando: 'Olá! Qual é o seu nome e qual sua função?'"
echo ""

curl -s -X POST "$BASE_URL/crew-ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Olá! Qual é o seu nome e qual sua função?",
    "contexto": {"source": "test_script"}
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ Resposta:', data.get('resposta', {}).get('resultado', 'Sem resposta'))"

echo ""
echo ""

# 5. Testar chat COM contexto de paciente (se houver)
if [ -n "$PACIENTE_ID" ]; then
  echo "5. TESTANDO CHAT COM DADOS DE PACIENTE (ID: $PACIENTE_ID)"
  echo "REDACTED"
  echo "📤 Enviando: 'Me dê um resumo sobre este paciente'"
  echo ""

  curl -s -X POST "$BASE_URL/crew-ai/chat" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"mensagem\": \"Me dê um resumo breve sobre este paciente: nome, condição médica e situação atual.\",
      \"paciente_id\": $PACIENTE_ID,
      \"contexto\": {\"source\": \"test_script\"}
    }" | python3 -c "import sys, json; data=json.load(sys.stdin); print('✓ Resposta:', data.get('resposta', {}).get('resultado', 'Sem resposta'))"
else
  echo "5. PULANDO TESTE COM PACIENTE"
  echo "REDACTED"
  echo "⚠ Nenhum paciente encontrado no sistema"
fi

echo ""
echo ""
echo "==========================================================="
echo "  RESUMO DOS TESTES"
echo "==========================================================="
echo ""
echo "✓ Todos os testes concluídos!"
echo ""
echo "Configuração atual:"
echo "  - Provedor: ollama_local"
echo "  - Modelo: gemma3:4b"
echo "  - URL: http://127.0.0.1:11434"
echo ""
echo "Acesse o frontend em: http://localhost:3000"
echo "E teste o chat interativo na interface!"
echo ""
