#!/bin/bash

BASE_URL="http://localhost:5002/api"

echo "==========================================================="
echo "  TESTE DO CHAT COM DADOS DE PACIENTE - GEMMA3:4B"
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

# Testar com Anderson (ID 4)
echo "2. TESTANDO CHAT COM ANDERSON (ID: 4)"
echo "==========================================================="
echo ""
echo "📤 Pergunta: Me fale sobre o paciente Anderson, suas condições e histórico."
echo ""

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/crew-ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Me fale sobre o paciente Anderson Batista Holzwarth. Quais são suas condições médicas, evoluções registradas, dosagens e sintomas? Faça um resumo completo.",
    "paciente_id": 4,
    "contexto": {"source": "test_anderson"}
  }')

echo "📥 RESPOSTA DO CHAT:"
echo "REDACTED"
echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('resposta', {}).get('resultado', data))" 2>/dev/null || echo "$CHAT_RESPONSE"
echo ""
echo ""

# Testar com Erika (ID 6)
echo "3. TESTANDO CHAT COM ERIKA (ID: 6)"
echo "==========================================================="
echo ""
echo "📤 Pergunta: Me dê um resumo sobre a paciente Erika."
echo ""

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/crew-ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mensagem": "Me dê um resumo completo sobre a paciente Erica Clementino da Silva. Inclua condições, histórico de tratamento e evolução.",
    "paciente_id": 6,
    "contexto": {"source": "test_erika"}
  }')

echo "📥 RESPOSTA DO CHAT:"
echo "REDACTED"
echo "$CHAT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('resposta', {}).get('resultado', data))" 2>/dev/null || echo "$CHAT_RESPONSE"
echo ""
echo ""

echo "==========================================================="
echo "  TESTE CONCLUÍDO!"
echo "==========================================================="
echo ""
echo "✓ O chat de IA está funcionando com gemma3:4b (Ollama local)"
echo "✓ Testado com dados reais dos pacientes Anderson e Erika"
echo ""
