#!/bin/bash

# Parar processos existentes
echo "Parando processos existentes..."
pkill -f "python3 app.py"
pkill -f "npm start"

# Verificar o status do PostgreSQL
if ! systemctl is-active --quiet postgresql@16-main; then
  echo "O PostgreSQL não está em execução. Por favor, inicie-o manualmente com 'sudo systemctl start postgresql@16-main'"
  exit 1
fi

# Iniciar o backend
echo "Iniciando o backend..."
cd backend
source venv/bin/activate
if [ -f "app.py" ]; then
    python3 app.py > ../backend.log 2>&1 &
else
    echo "Arquivo app.py não encontrado no backend"
    exit 1
fi
cd ..

# Iniciar o frontend
echo "Iniciando o frontend..."
cd frontend
npm start > ../frontend.log 2>&1 &