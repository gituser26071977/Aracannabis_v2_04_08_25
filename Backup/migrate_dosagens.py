#!/usr/bin/env python3
"""
Script para migrar a tabela de dosagens e adicionar o campo gotas_por_ml
"""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from models import db
from config import get_config
import psycopg2

def migrate_dosagens():
    """Adiciona a coluna gotas_por_ml à tabela dosagens"""
    
    print("🔄 Iniciando migração da tabela dosagens...")
    
    # Configurar Flask app
    app = Flask(__name__)
    current_config = get_config()
    app.config.from_object(current_config)
    
    db.init_app(app)
    
    with app.app_context():
        try:
            # Conectar diretamente ao PostgreSQL para executar a migração
            connection = psycopg2.connect(
                host="localhost",
                database="aracannabis",
                user="postgres",
                password="postgres"
            )
            cursor = connection.cursor()
            
            # Verificar se a coluna já existe
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='dosagens' AND column_name='gotas_por_ml';
            """)
            
            if cursor.fetchone():
                print("✅ Coluna gotas_por_ml já existe!")
            else:
                print("➕ Adicionando coluna gotas_por_ml...")
                
                # Adicionar a coluna
                cursor.execute("""
                    ALTER TABLE dosagens 
                    ADD COLUMN gotas_por_ml INTEGER DEFAULT 30 NOT NULL;
                """)
                
                # Atualizar registros existentes
                cursor.execute("""
                    UPDATE dosagens 
                    SET gotas_por_ml = 30 
                    WHERE gotas_por_ml IS NULL;
                """)
                
                connection.commit()
                print("✅ Coluna gotas_por_ml adicionada com sucesso!")
            
            # Verificar a estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name='dosagens'
                ORDER BY ordinal_position;
            """)
            
            print("\n📋 Estrutura atual da tabela dosagens:")
            for row in cursor.fetchall():
                column_name, data_type, is_nullable, column_default = row
                nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                default = f" DEFAULT {column_default}" if column_default else ""
                print(f"   {column_name}: {data_type} {nullable}{default}")
            
            cursor.close()
            connection.close()
            
            print("\n🎉 Migração concluída com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            if 'connection' in locals():
                connection.rollback()
                connection.close()

if __name__ == "__main__":
    migrate_dosagens()
