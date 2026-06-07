#!/usr/bin/env python3
"""
Script para verificar estrutura da tabela senhas_temporarias
"""

import sqlite3
import os

def check_senhas_temp():
    """Verificar estrutura da tabela senhas_temporarias"""
    
    db_path = os.path.join('instance', 'aracannabis.db')
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar estrutura da tabela senhas_temporarias
        cursor.execute("PRAGMA table_info(senhas_temporarias)")
        columns = cursor.fetchall()
        print("🔹 Estrutura da tabela senhas_temporarias:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
            
        # Verificar estrutura da tabela solicitacoes_cadastro
        cursor.execute("PRAGMA table_info(solicitacoes_cadastro)")
        columns = cursor.fetchall()
        print("\n🔹 Estrutura da tabela solicitacoes_cadastro:")
        for col in columns:
            print(f"   {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    check_senhas_temp()
