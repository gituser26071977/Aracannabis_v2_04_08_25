#!/usr/bin/env python3
"""
Script direto para criar um usuário superadmin no sistema Aracannabis.
Este script cria um usuário com role='superadmin' e uma senha forte gerada automaticamente.
"""

import os
import secrets
import string
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from models import db, Profissional
from werkzeug.security import generate_password_hash

load_dotenv()

def generate_strong_password(length=16):
    """Gera uma senha forte com letras maiúsculas, minúsculas, números e símbolos"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

# Configurar app Flask minimalista
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Criar todas as tabelas (se necessário)
    db.create_all()
    
    try:
        # Verificar se já existe um superadmin
        existing_superadmin = db.session.execute(
            db.text("SELECT * FROM profissionais WHERE usuario = :usuario"),
            {'usuario': 'superadmin'}
        ).fetchone()
        
        if existing_superadmin:
            print(f"⚠️  Superadmin já existe no banco de dados")
            print(f"📧 Email: {existing_superadmin.email}")
            print(f"🆔 ID: {existing_superadmin.id}")
            print(f"👤 Usuário: {existing_superadmin.usuario}")
            print("\nPara resetar a senha, você pode usar:")
            print("UPDATE profissionais SET senha = :nova_senha WHERE usuario = 'superadmin'")
            print("(substitua :nova_senha pelo hash da nova senha)")
        else:
            print("👤 Criando usuário 'superadmin'...")
            
            # Gerar credenciais para o superadmin
            usuario_superadmin = "superadmin"
            email_superadmin = "superadmin@aracannabis.com.br"
            nome_superadmin = "Super Administrador"
            senha_superadmin = generate_strong_password()
            senha_hash = generate_password_hash(senha_superadmin)
            
            # Inserir o usuário superadmin diretamente no banco
            result = db.session.execute(
                db.text("""
                    INSERT INTO profissionais 
                    (nome, crm, uf_crm, usuario, email, senha, role, status_cadastro, data_aprovacao, created_at)
                    VALUES 
                    (:nome, :crm, :uf_crm, :usuario, :email, :senha, :role, :status_cadastro, :data_aprovacao, :created_at)
                """),
                {
                    'nome': nome_superadmin,
                    'crm': 'ADMIN0001',
                    'uf_crm': 'BR',
                    'usuario': usuario_superadmin,
                    'email': email_superadmin,
                    'senha': senha_hash,
                    'role': 'superadmin',
                    'status_cadastro': 'aprovado',
                    'data_aprovacao': datetime.now(),
                    'created_at': datetime.now()
                }
            )
            
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
        import traceback
        traceback.print_exc()
        raise