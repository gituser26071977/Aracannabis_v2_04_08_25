#!/usr/bin/env python3
"""
Script para limpar produtos e deixar apenas 3 básicos
"""

import sqlite3
import os

def clean_produtos_table():
    """Limpar tabela de produtos e deixar apenas 3 básicos"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Limpar todos os produtos existentes
        cursor.execute('DELETE FROM produtos')
        print("🗑️ Produtos existentes removidos")
        
        # Inserir apenas 3 produtos básicos
        produtos_basicos = [
            ('Óleo CBD 10%', 'oleo', 100.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 10% - 100mg/ml'),
            ('Óleo CBD 20%', 'oleo', 200.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 20% - 200mg/ml'),
            ('Óleo Full Spectrum 5%', 'oleo', 45.0, 5.0, 2.0, 1.0, 30, 30.0, 'Genérico', 'Óleo Full Spectrum 5% com múltiplos canabinoides')
        ]
        
        cursor.executemany('''
            INSERT INTO produtos (nome, tipo, concentracao_cbd, concentracao_thc, concentracao_cbg, concentracao_cbn, gotas_por_ml, volume_ml, fabricante, descricao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', produtos_basicos)
        
        conn.commit()
        print(f"✅ Inseridos {len(produtos_basicos)} produtos básicos")
        
        # Mostrar produtos criados
        cursor.execute('SELECT * FROM produtos ORDER BY nome')
        produtos = cursor.fetchall()
        
        print(f"\n📦 Produtos disponíveis ({len(produtos)}):")
        for produto in produtos:
            print(f"  - {produto[1]} (CBD: {produto[3]}mg/ml, THC: {produto[4]}mg/ml)")
        
        print("\n✅ Limpeza concluída! Agora você pode adicionar seus próprios produtos.")
        
    except Exception as e:
        print(f"❌ Erro ao limpar produtos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧹 Limpando produtos e deixando apenas 3 básicos...")
    clean_produtos_table()
    print("✅ Operação concluída!")
