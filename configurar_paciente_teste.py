#!/usr/bin/env python3
"""
Script para configurar a conta do paciente de teste
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_cors_livre import create_app
from models import db, Paciente
from werkzeug.security import generate_password_hash

def configurar_paciente_teste():
    app = create_app()
    
    with app.app_context():
        print("🔧 Configurando paciente de teste...\n")
        
        paciente = Paciente.query.get(1)
        
        if not paciente:
            print("❌ Paciente ID=1 não encontrado!")
            return
        
        print(f"📋 Paciente encontrado: {paciente.nome}")
        print(f"   Email atual: {paciente.email}")
        print(f"   Tem senha: {paciente.senha_hash is not None}")
        print(f"   Ativo: {getattr(paciente, 'is_active', False)}")
        
        # Configurar conta
        paciente.email = 'paciente.teste@example.com'
        paciente.senha_hash = generate_password_hash('senhateste123')
        
        if hasattr(paciente, 'is_active'):
            paciente.is_active = True
        if hasattr(paciente, 'email_verified'):
            paciente.email_verified = True
        
        db.session.commit()
        
        print("\n✅ Conta configurada!")
        print(f"   Email: {paciente.email}")
        print("   Senha: senhateste123")
        print(f"   Ativo: {paciente.is_active}")

if __name__ == '__main__':
    configurar_paciente_teste()
