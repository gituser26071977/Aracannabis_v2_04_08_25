#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv()

from app_cors_livre import create_app
from models import db, Profissional

def check_users():
    app = create_app()
    
    with app.app_context():
        try:
            users = Profissional.query.all()
            print(f"=== USUÁRIOS ENCONTRADOS ({len(users)}) ===")
            
            if not users:
                print("Nenhum usuário encontrado no banco de dados.")
                return None
                
            for user in users:
                print(f"ID: {user.id}")
                print(f"Nome: {user.nome}")
                print(f"Usuario: {user.usuario}")
                print(f"CRM: {user.crm}")
                print("---")
                
            return users[0].usuario if users else None
            
        except Exception as e:
            print(f"Erro ao consultar usuários: {e}")
            return None

if __name__ == "__main__":
    first_user = check_users()
    if first_user:
        print(f"\nPrimeiro usuário encontrado: {first_user}")
    else:
        print("\nNenhum usuário disponível para teste.")
