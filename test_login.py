#!/usr/bin/env python3
"""
Script para testar o login do superadmin
"""

import os
from dotenv import load_dotenv
from flask import Flask
from models import db, Profissional
from werkzeug.security import check_password_hash

load_dotenv()

# Configurar app Flask minimalista
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Verificar qual banco está sendo usado
    print("="*70)
    print(f"📁 DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print("="*70)
    
    # Buscar o superadmin usando ORM
    profissional = Profissional.query.filter_by(usuario='superadmin').first()
    
    if profissional:
        print("\n✅ Superadmin encontrado via ORM")
        print(f"🆔 ID: {profissional.id}")
        print(f"👤 Nome: {profissional.nome}")
        print(f"📧 Email: {profissional.email}")
        print(f"🎭 Role: {profissional.role}")
        print(f"📝 Status: {profissional.status_cadastro}")
        
        # Teste de login
        print("\n" + "="*70)
        print("🔑 TESTE DE LOGIN")
        print("="*70)
        
        senha_teste = "BtNr'k*;[=3js[i="
        
        print(f"\nUsuário: {profissional.usuario}")
        print(f"Senha: {senha_teste}")
        
        if check_password_hash(profissional.senha, senha_teste):
            print("\n✅ LOGIN BEM-SUCEDIDO!")
            print("As credenciais estão corretas.")
        else:
            print("\n❌ FALHA NO LOGIN!")
            print("Senha não confere.")
    else:
        print("\n❌ Superadmin NÃO encontrado via ORM!")
        print("Isso indica que o ORM não está encontrando o usuário.")
        
        # Tentar buscar diretamente com SQL
        print("\n🔍 Tentando busca direta com SQL...")
        result = db.session.execute(
            db.text("SELECT * FROM profissionais WHERE usuario = :usuario"),
            {'usuario': 'superadmin'}
        ).fetchone()
        
        if result:
            print(f"✅ Encontrado via SQL direto! ID: {result.id}")
        else:
            print("❌ Não encontrado nem via SQL direto")