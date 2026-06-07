#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from app_cors_livre import create_app
from models import db, Profissional
from werkzeug.security import generate_password_hash

def create_test_user():
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se já existe um usuário de teste
            existing_user = Profissional.query.filter_by(usuario='teste_debug').first()
            if existing_user:
                print("Usuário teste_debug já existe. Removendo...")
                db.session.delete(existing_user)
                db.session.commit()
            
            # Criar novo usuário de teste
            senha_hash = generate_password_hash('123456')
            
            novo_usuario = Profissional(
                nome='Usuário de Teste Debug',
                crm='TEST001',
                uf_crm='SP',
                usuario='teste_debug',
                senha=senha_hash
            )
            
            db.session.add(novo_usuario)
            db.session.commit()
            
            print("✅ Usuário de teste criado com sucesso!")
            print("Usuario: teste_debug")
            print("Senha: 123456")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário de teste: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    create_test_user()
