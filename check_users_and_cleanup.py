#!/usr/bin/env python3
"""
Script para verificar usuários existentes e remover os últimos 3 cadastros,
mantendo apenas o admin.
"""

import os
import sys
from datetime import datetime
from flask import Flask
from models import db, Profissional

def create_app():
    app = Flask(__name__)
    
    # Configuração do banco de dados
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "aracannabis.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def list_all_users():
    """Lista todos os usuários ordenados por data de criação"""
    users = Profissional.query.order_by(Profissional.created_at.asc()).all()
    
    print("\n=== USUÁRIOS EXISTENTES ===")
    print(f"Total de usuários: {len(users)}")
    print("-" * 80)
    
    for i, user in enumerate(users, 1):
        print(f"{i}. ID: {user.id}")
        print(f"   Nome: {user.nome}")
        print(f"   CRM: {user.crm}")
        print(f"   Usuário: {user.usuario}")
        print(f"   Criado em: {user.created_at}")
        print("-" * 40)
    
    return users

def delete_last_three_users(users):
    """Remove os últimos 3 usuários cadastrados, mantendo o admin"""
    if len(users) <= 1:
        print("❌ Apenas 1 usuário ou menos encontrado. Não é possível remover.")
        return False
    
    # Identifica o admin (primeiro usuário ou com nome 'admin')
    admin_user = None
    for user in users:
        if user.usuario.lower() == 'admin' or user.nome.lower() == 'admin':
            admin_user = user
            break
    
    if not admin_user:
        admin_user = users[0]  # Considera o primeiro como admin
    
    print(f"\n🔒 Admin identificado: {admin_user.nome} (ID: {admin_user.id})")
    
    # Ordena por data de criação (mais recentes primeiro)
    # Trata casos onde created_at pode ser None
    users_sorted = sorted(users, key=lambda x: x.created_at or datetime.min, reverse=True)
    
    # Remove o admin da lista para não deletá-lo
    users_to_consider = [u for u in users_sorted if u.id != admin_user.id]
    
    if len(users_to_consider) < 3:
        print(f"⚠️  Apenas {len(users_to_consider)} usuários não-admin encontrados.")
        users_to_delete = users_to_consider
    else:
        users_to_delete = users_to_consider[:3]
    
    if not users_to_delete:
        print("✅ Nenhum usuário para deletar (apenas admin existe).")
        return True
    
    print(f"\n🗑️  Usuários que serão REMOVIDOS:")
    for user in users_to_delete:
        print(f"   - {user.nome} (ID: {user.id}, Usuário: {user.usuario})")
    
    # Confirma a operação
    confirm = input(f"\n⚠️  CONFIRMA a remoção de {len(users_to_delete)} usuário(s)? (sim/não): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada pelo usuário.")
        return False
    
    # Remove os usuários
    try:
        for user in users_to_delete:
            print(f"🗑️  Removendo: {user.nome} (ID: {user.id})")
            db.session.delete(user)
        
        db.session.commit()
        print(f"✅ {len(users_to_delete)} usuário(s) removido(s) com sucesso!")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao remover usuários: {str(e)}")
        return False

def main():
    app = create_app()
    
    with app.app_context():
        try:
            # Lista usuários existentes
            users = list_all_users()
            
            if len(users) == 0:
                print("❌ Nenhum usuário encontrado no banco de dados.")
                return
            
            # Remove os últimos 3 usuários
            success = delete_last_three_users(users)
            
            if success:
                print("\n=== USUÁRIOS APÓS LIMPEZA ===")
                list_all_users()
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            return

if __name__ == "__main__":
    main()
