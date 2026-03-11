#!/bin/bash
# Script para criar pacote de deploy SIAP
# Remove arquivos desnecessários para reduzir tamanho

PACKAME="aracannabis_siap_deploy.tar.gz"

echo "📦 Criando pacote de deploy: $PACKAME..."

tar --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.venv*' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='aracannabis.db' \
    --exclude='*.log' \
    --exclude='uploads/*' \
    -czf "$PACKAME" .

echo "✅ Pacote criado com sucesso!"
echo "🚀 Para enviar ao VPS, use:"
echo "scp $PACKAME root@147.93.33.253:/root/"
