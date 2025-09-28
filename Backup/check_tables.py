#!/usr/bin/env python3
"""
Script para verificar tabelas existentes no banco SQLite
"""

import sqlite3
import os

def check_tables():
    """Verificar tabelas existentes no banco"""
    
    db_path = os.path.join('instance', 'aracannabis.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📋 Tabelas existentes no banco:")
        for table in tables:
            print(f"   - {table[0]}")
            
        # Verificar se a tabela profissionais existe
        if any('profissionais' in table for table in tables):
            print("\n✅ Tabela 'profissionais' encontrada!")
            
            # Mostrar estrutura da tabela profissionais
            cursor.execute("PRAGMA table_info(profissionais)")
            columns = cursor.fetchall()
            print("\n🔹 Estrutura da tabela profissionais:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
                
            return True
        else:
            print("\n❌ Tabela 'profissionais' não encontrada!")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_tables()
