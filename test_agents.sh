#!/bin/bash

# Script de teste do sistema conversacional

echo "🧪 TESTE 1: Login e obtenção de token JWT"
TOKEN=$(curl -s -X POST http://localhost:5002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"usuario": "drtest", "senha": "test123"}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Falha no login. Verifique credenciais."
  exit 1
fi

echo "✅ Login bem-sucedido! Token obtido."
echo ""

echo "🧪 TESTE 2: Chat conversacional - Buscar paciente"
curl -s -X POST http://localhost:5002/api/crew-ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mensagem": "Liste os pacientes cadastrados", "contexto": {}}' | python3 -m json.tool

echo ""
echo "🧪 TESTE 3: Chat conversacional - Criar paciente"
curl -s -X POST http://localhost:5002/api/crew-ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mensagem": "Cadastrar paciente Maria Santos, CPF 98765432100, nascimento 15/03/1985", "contexto": {}}' | python3 -m json.tool

echo ""
echo "🧪 TESTE 4: Listar agentes disponíveis"
curl -s -X GET http://localhost:5002/api/ai-management/agents \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -30

echo ""
echo "✅ Testes concluídos!"
