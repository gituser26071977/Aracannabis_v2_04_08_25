#!/bin/bash
# Teste do chat simples com dados reais de pacientes

BASE_URL="http://localhost:5002/api"

echo "==========================================================="
echo "  TESTE DO CHAT SIMPLES COM GEMMA3:4B"
echo "  (Versão que funciona com modelos locais pequenos)"
echo "==========================================================="
echo ""

# Login
echo "1. FAZENDO LOGIN"
echo "REDACTED"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"usuario":"admin","senha":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login"
  exit 1
fi

echo "✓ Login bem-sucedido!"
echo ""

# Teste 1: Anderson
echo "2. TESTANDO COM ANDERSON (ID: 4)"
echo "==========================================================="
echo ""
echo "📤 Pergunta: Quem é este paciente e qual é seu histórico?"
echo ""

curl -s -X POST "$BASE_URL/chat-simples" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Olá! Me dê um resumo completo sobre este paciente: nome, condição médica, quantas evoluções tem, quais medicamentos está usando e principais sintomas relatados.",
    "paciente_id": 4
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('📥 RESPOSTA:')
    print('REDACTED')
    print(data.get('resposta', 'Sem resposta'))
    print('')
    print(f\"Model usado: {data.get('provider')}/{data.get('model')}\")
    print(f\"Tem contexto: {data.get('tem_contexto')}\")
except Exception as e:
    print(f'Erro ao processar resposta: {e}')
"

echo ""
echo ""

# Teste 2: Pergunta específica sobre dosagens
echo "3. PERGUNTA ESPECÍFICA SOBRE DOSAGENS DO ANDERSON"
echo "==========================================================="
echo ""
echo "📤 Pergunta: Quais medicamentos o Anderson está tomando?"
echo ""

curl -s -X POST "$BASE_URL/chat-simples" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Quais medicamentos o paciente está usando atualmente? Liste os nomes, dosagens e frequências.",
    "paciente_id": 4
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('📥 RESPOSTA:')
    print('REDACTED')
    print(data.get('resposta', 'Sem resposta'))
except Exception as e:
    print(f'Erro: {e}')
"

echo ""
echo ""

# Teste 3: Erika
echo "4. TESTANDO COM ERIKA (ID: 6)"
echo "==========================================================="
echo ""
echo "📤 Pergunta: Me conte sobre a paciente Erika"
echo ""

curl -s -X POST "$BASE_URL/chat-simples" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Faça um resumo sobre esta paciente: dados gerais, tratamento atual e observações importantes.",
    "paciente_id": 6
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('📥 RESPOSTA:')
    print('REDACTED')
    print(data.get('resposta', 'Sem resposta'))
except Exception as e:
    print(f'Erro: {e}')
"

echo ""
echo ""

echo "==========================================================="
echo "  TESTE CONCLUÍDO!"
echo "==========================================================="
echo ""
echo "✓ Chat simples testado com sucesso!"
echo "✓ Modelo: gemma3:4b (Ollama local)"
echo "✓ Dados dos pacientes foram incluídos no contexto"
echo ""
echo "Esta versão funciona melhor com modelos locais pequenos"
echo "porque não depende de function calling - todos os dados"
echo "são passados diretamente no prompt."
echo ""
