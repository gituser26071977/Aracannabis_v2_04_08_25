#!/usr/bin/env python3
"""
Script para criar um usuário superadmin no sistema Aracannabis.
Este script cria um usuário com role='superadmin' e uma senha forte gerada automaticamente.
"""

import secrets
import string
from flask import Flask
from models import db, Profissional
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

def generate_strong_password(length=16):
    """Gera uma senha forte com letras maiúsculas, minúsculas, números e símbolos"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_superadmin():
    """Cria um usuário superadmin no sistema"""
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    db.init_app(app)
    
    with app.app_context():
        # Verificar se já existe um superadmin
        existing_superadmin = Profissional.query.filter_by(role='superadmin').first()
        if existing_superadmin:
            print(f"⚠️  Superadmin já existe: {existing_superadmin.usuario}")
            print(f"📧 Email: {existing_superadmin.email}")
            choice = input("Deseja criar um novo superadmin ou resetar a senha do existente? (novo/resetar): ").strip().lower()
            
            if choice == 'resetar':
                nova_senha = generate_strong_password()
                existing_superadmin.senha = generate_password_hash(nova_senha)
                db.session.commit()
                print("\n" + "="*70)
                print("🔐 CREDENCIAIS DO SUPERADMIN (RESETADA)")
                print("="*70)
                print(f"👤 Usuário: {existing_superadmin.usuario}")
                print(f"📧 Email: {existing_superadmin.email}")
                print(f"🔑 Nova Senha: {nova_senha}")
                print("="*70)
                print("\n⚠️  SALVE ESTAS CREDENCIAIS EM LOCAL SEGURO!")
                print("="*70 + "\n")
                return
            else:
                print("🔐 Criando um novo superadmin...")
        
        # Gerar credenciais para o superadmin
        usuario_superadmin = "superadmin"
        email_superadmin = "superadmin@aracannabis.com.br"
        nome_superadmin = "Super Administrador"
        senha_superadmin = generate_strong_password()
        senha_hash = generate_password_hash(senha_superadmin)
        
        # Criar o usuário superadmin
        novo_superadmin = Profissional(
            nome=nome_superadmin,
            crm="ADMIN0001",
            uf_crm="BR",
            usuario=usuario_superadmin,
            email=email_superadmin,
            senha=senha_hash,
            role="superadmin",
            status_cadastro="aprovado",
            data_aprovacao=datetime.now()
        )
        
        try:
            db.session.add(novo_superadmin)
            db.session.commit()
            
            print("\n" + "="*70)
            print("🔐 CREDENCIAIS DO SUPERADMIN CRIADAS COM SUCESSO")
            print("="*70)
            print(f"👤 Nome: {nome_superadmin}")
            print(f"📧 Email: {email_superadmin}")
            print(f"🆔 Usuário: {usuario_superadmin}")
            print(f"🔑 Senha: {senha_superadmin}")
            print(f"🎭 Role: superadmin")
            print("="*70)
            print("\n⚠️  ATENÇÃO: Salve estas credenciais em local seguro!")
            print("   Esta senha foi gerada automaticamente e é segura.")
            print("   Você pode alterá-la através da interface do sistema.")
            print("="*70 + "\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar superadmin: {e}")
            raise

if __name__ == '__main__':
    from datetime import datetime
    create_superadmin()