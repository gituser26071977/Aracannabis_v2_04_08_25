#!/usr/bin/env python3
"""
Script para criar a tabela de produtos canábicos
"""

import sqlite3
import os

def create_produtos_table():
    """Criar tabela de produtos"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Criar tabela de produtos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL DEFAULT 'oleo',
                concentracao_cbd REAL DEFAULT 0,
                concentracao_thc REAL DEFAULT 0,
                concentracao_cbg REAL DEFAULT 0,
                concentracao_cbn REAL DEFAULT 0,
                gotas_por_ml INTEGER DEFAULT 30,
                volume_ml REAL DEFAULT 30,
                fabricante TEXT,
                descricao TEXT,
                ativo BOOLEAN DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Verificar se já existem produtos
        cursor.execute('SELECT COUNT(*) FROM produtos')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Inserir produtos padrão
            produtos_padrao = [
                ('Óleo CBD 5%', 'oleo', 50.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 5% - 50mg/ml'),
                ('Óleo CBD 10%', 'oleo', 100.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 10% - 100mg/ml'),
                ('Óleo CBD 15%', 'oleo', 150.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 15% - 150mg/ml'),
                ('Óleo CBD 20%', 'oleo', 200.0, 0.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBD 20% - 200mg/ml'),
                ('Óleo Full Spectrum 5%', 'oleo', 45.0, 5.0, 2.0, 1.0, 30, 30.0, 'Genérico', 'Óleo Full Spectrum 5% com múltiplos canabinoides'),
                ('Óleo Full Spectrum 10%', 'oleo', 90.0, 10.0, 3.0, 2.0, 30, 30.0, 'Genérico', 'Óleo Full Spectrum 10% com múltiplos canabinoides'),
                ('Óleo THC:CBD 1:1', 'oleo', 50.0, 50.0, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo balanceado THC:CBD 1:1'),
                ('Óleo THC:CBD 1:2', 'oleo', 66.7, 33.3, 0.0, 0.0, 30, 30.0, 'Genérico', 'Óleo THC:CBD 1:2'),
                ('Óleo CBG 5%', 'oleo', 0.0, 0.0, 50.0, 0.0, 30, 30.0, 'Genérico', 'Óleo de CBG 5% - 50mg/ml'),
                ('Óleo CBN 2%', 'oleo', 0.0, 0.0, 0.0, 20.0, 30, 30.0, 'Genérico', 'Óleo de CBN 2% - 20mg/ml')
            ]
            
            cursor.executemany('''
                INSERT INTO produtos (nome, tipo, concentracao_cbd, concentracao_thc, concentracao_cbg, concentracao_cbn, gotas_por_ml, volume_ml, fabricante, descricao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', produtos_padrao)
            
            print(f"✅ Inseridos {len(produtos_padrao)} produtos padrão")
        
        conn.commit()
        print("✅ Tabela de produtos criada com sucesso!")
        
        # Mostrar produtos criados
        cursor.execute('SELECT * FROM produtos ORDER BY nome')
        produtos = cursor.fetchall()
        
        print(f"\n📦 Produtos cadastrados ({len(produtos)}):")
        for produto in produtos:
            print(f"  - {produto[1]} (CBD: {produto[3]}mg/ml, THC: {produto[4]}mg/ml)")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela de produtos: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Criando tabela de produtos...")
    create_produtos_table()
    print("✅ Migração concluída!")
