#!/usr/bin/env python3
"""
Script para verificar o superadmin criado
"""

import os
from dotenv import load_dotenv
from flask import Flask
from models import db
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

# Configurar app Flask minimalista
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Buscar o superadmin
    result = db.session.execute(
        db.text("SELECT * FROM profissionais WHERE usuario = :usuario"),
        {'usuario': 'superadmin'}
    ).fetchone()
    
    if result:
        print("="*70)
        print("🔍 DADOS DO SUPERADMIN NO BANCO")
        print("="*70)
        print(f"🆔 ID: {result.id}")
        print(f"👤 Nome: {result.nome}")
        print(f"📧 Email: {result.email}")
        print(f"🔐 Usuário: {result.usuario}")
        print(f"🎭 Role: {result.role}")
        print(f"📝 Status: {result.status_cadastro}")
        print(f"🔒 Senha (hash): {result.senha[:50]}...")
        print("="*70)
        
        # Testar verificação de senha com diferentes valores
        print("\n🧪 Testando verificação de senha...")
        
        # Teste 1: Senha gerada anteriormente
        senha_teste = "BtNr'k*;[=3js[i="
        check1 = check_password_hash(result.senha, senha_teste)
        print(f"Senha original: {senha_teste}")
        print(f"Verificação: {check1}")
        
        # Teste 2: Senha simples
        senha_simples = "Admin@123"
        hash_simples = generate_password_hash(senha_simples)
        check2 = check_password_hash(hash_simples, senha_simples)
        print(f"\nSenha simples: {senha_simples}")
        print(f"Verificação (hash novo): {check2}")
        
    else:
        print("❌ Superadmin não encontrado no banco de dados!")