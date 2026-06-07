#!/bin/bash

# Script para iniciar a aplicação Aracannabis com Docker

echo "🚀 Iniciando a aplicação Aracannabis com Docker..."

# Verificar se o Docker está instalado
if ! command -v docker &> /dev/null
then
    echo "❌ Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verificar se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null
then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Construir e iniciar os serviços
echo "🔧 Construindo e iniciando os containers..."
docker-compose up --build

echo "✅ A aplicação está rodando!"
echo "📱 Frontend: http://localhost:3000"
echo "📡 Backend: http://localhost:5002"