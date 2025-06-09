#!/bin/bash

# Script de configuração automatizada para o sistema Aracannabis
# Versão 1.0

# Função para verificar e instalar dependências
install_dependencies() {
    echo "Verificando dependências do sistema..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "Python3 não encontrado. Instalando..."
        sudo apt-get update
        sudo apt-get install -y python3 python3-venv
    fi

    # Verificar Node.js
    if ! command -v node &> /dev/null; then
        echo "Node.js não encontrado. Instalando..."
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi

    # Verificar PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo "PostgreSQL não encontrado. Instalando..."
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
    fi

    # Verificar Git
    if ! command -v git &> /dev/null; then
        echo "Git não encontrado. Instalando..."
        sudo apt-get install -y git
    fi
}

# Função para configurar ambiente virtual
setup_virtualenv() {
    echo "Configurando ambiente virtual Python..."
    python3 -m venv venv
    source venv/bin/activate
}

# Função para instalar dependências Python
install_python_deps() {
    echo "Instalando dependências Python..."
    pip install -r requirements.txt
}

# Função para configurar banco de dados
setup_database() {
    echo "Configurando banco de dados..."
    sudo systemctl start postgresql
    python migrate_dosagens.py
}

# Função principal
main() {
    echo "Iniciando configuração do sistema Aracannabis"
    echo "---------------------------------------------"
    
    install_dependencies
    setup_virtualenv
    install_python_deps
    setup_database
    
    echo ""
    echo "Configuração concluída com sucesso!"
    echo "Execute os seguintes comandos para iniciar o sistema:"
    echo "1. Backend: python app.py"
    echo "2. Frontend: cd frontend && npm start"
}

main
