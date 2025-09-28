#!/usr/bin/env python3
"""
Criar usuário admin para o sistema
"""

import os
from dotenv import load_dotenv
load_dotenv()

from app_cors_livre import create_app
from models import db, Profissional
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Verificar se já existe um admin
        admin_existente = Profissional.query.filter_by(usuario='admin@aracannabis.com').first()
        
        if admin_existente:
            print("✅ Admin já existe!")
            print(f"Usuário: {admin_existente.usuario}")
            return
        
        # Criar novo admin
        admin = Profissional(
            nome='Administrador',
            usuario='admin@aracannabis.com',
            senha=generate_password_hash('admin123'),
            crm='ADMIN001'
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin criado com sucesso!")
        print("Email: admin@aracannabis.com")
        print("Senha: admin123")

if __name__ == "__main__":
    create_admin()
