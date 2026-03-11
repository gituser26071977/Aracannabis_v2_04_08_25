#!/usr/bin/env python3
"""
Script simples para criar um usuário superadmin no sistema Aracannabis.
Este script cria um usuário com role='superadmin' e uma senha forte gerada automaticamente.
"""

import secrets
import string
from werkzeug.security import generate_password_hash
from datetime import datetime
from app_cors_livre import create_app
from models import Profissional, db

def generate_strong_password(length=16):
    """Gera uma senha forte com letras maiúsculas, minúsculas, números e símbolos"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

# Usar create_app() que configura todos os modelos corretamente
app = create_app()

with app.app_context():
    
    try:
        # Verificar se já existe um superadmin
        existing_superadmin = Profissional.query.filter_by(usuario='superadmin').first()
        
        if existing_superadmin:
            print(f"⚠️  Superadmin já existe: {existing_superadmin.usuario}")
            print(f"📧 Email: {existing_superadmin.email}")
            print(f"🆔 ID: {existing_superadmin.id}")
            print("\nSe deseja resetar a senha, execute:")
            print("python3 reset_superadmin_password.py")
        else:
            print("👤 Criando usuário 'superadmin'...")
            
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