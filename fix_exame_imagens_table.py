#!/usr/bin/env python3
"""
Script para corrigir a tabela exame_imagens adicionando a coluna created_at
"""

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix_exame_imagens_table():
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host="localhost",
            database="aracannabis",
            user="postgres",
            password="postgres"
        )
        cur = conn.cursor()
        
        print("🔧 Verificando estrutura da tabela exame_imagens...")
        
        # Verificar se a coluna created_at existe
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'exame_imagens' AND column_name = 'created_at'
        """)
        
        if cur.fetchone() is None:
            print("📝 Adicionando coluna created_at...")
            cur.execute("""
                ALTER TABLE exame_imagens 
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            print("✅ Coluna created_at adicionada!")
        else:
            print("✅ Coluna created_at já existe!")
        
        # Verificar estrutura atual
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'exame_imagens'
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Estrutura atual da tabela exame_imagens:")
        for row in cur.fetchall():
            print(f"   - {row[0]} ({row[1]}) - Nullable: {row[2]} - Default: {row[3]}")
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n✅ Correção da tabela concluída!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    fix_exame_imagens_table()
