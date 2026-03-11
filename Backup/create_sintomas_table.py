#!/usr/bin/env python3
"""
Criar tabela para sintomas personalizados
"""

from dotenv import load_dotenv
load_dotenv()

from app_cors_livre import create_app
from models import db
from sqlalchemy import text

def create_sintomas_table():
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a tabela existe e adicionar coluna ativo se necessário
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS sintomas_personalizados (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) NOT NULL UNIQUE,
                    criado_por INTEGER REFERENCES profissionais(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Adicionar coluna ativo se não existir
            try:
                db.session.execute(text("""
                    ALTER TABLE sintomas_personalizados 
                    ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;
                """))
            except Exception as e:
                print(f"Coluna ativo já existe ou erro: {e}")
            
            db.session.commit()
            print("✅ Tabela sintomas_personalizados criada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_sintomas_table()
