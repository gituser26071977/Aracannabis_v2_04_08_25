#!/usr/bin/env python3
"""
Script para criar tabela de profissionais com sistema de cadastro e validação
"""

import sqlite3
import os
from datetime import datetime

def migrate_profissionais():
    """Criar tabela de profissionais e sistema de cadastro"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('instance', 'aracannabis.db')
    
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migração da tabela de profissionais...")
        
        # 1. Criar tabela de solicitações de cadastro
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solicitacoes_cadastro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                crm VARCHAR(20) NOT NULL,
                uf_crm VARCHAR(2) NOT NULL,
                telefone VARCHAR(20),
                especialidade VARCHAR(100),
                instituicao VARCHAR(255),
                status VARCHAR(20) DEFAULT 'pendente',
                data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_aprovacao DATETIME,
                observacoes TEXT,
                aprovado_por INTEGER,
                FOREIGN KEY (aprovado_por) REFERENCES profissionais (id)
            )
        ''')
        
        # 2. Criar tabela de senhas temporárias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS senhas_temporarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profissional_id INTEGER NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_expiracao DATETIME NOT NULL,
                usado BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (profissional_id) REFERENCES profissionais (id)
            )
        ''')
        
        # 3. Adicionar campos na tabela profissionais se não existirem
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN uf_crm VARCHAR(2)')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN telefone VARCHAR(20)')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN email VARCHAR(255)')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN especialidade VARCHAR(100)')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN instituicao VARCHAR(255)')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN ativo BOOLEAN DEFAULT TRUE')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN tipo_conta VARCHAR(20) DEFAULT "permanente"')
        except sqlite3.OperationalError:
            pass  # Campo já existe
            
        try:
            cursor.execute('ALTER TABLE profissionais ADD COLUMN data_expiracao DATETIME')
        except sqlite3.OperationalError:
            pass  # Campo já existe
        
        # 4. Criar índices para performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_email ON solicitacoes_cadastro(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_solicitacoes_crm ON solicitacoes_cadastro(crm, uf_crm)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_senhas_temp_profissional ON senhas_temporarias(profissional_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_profissionais_crm ON profissionais(crm)')
        
        # 5. Verificar dados existentes
        cursor.execute('SELECT COUNT(*) FROM solicitacoes_cadastro')
        count_solicitacoes = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM senhas_temporarias')
        count_senhas = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM profissionais')
        count_profissionais = cursor.fetchone()[0]
        
        conn.commit()
        
        print("✅ Migração concluída com sucesso!")
        print(f"📊 Estatísticas:")
        print(f"   - Solicitações de cadastro: {count_solicitacoes}")
        print(f"   - Senhas temporárias: {count_senhas}")
        print(f"   - Profissionais total: {count_profissionais}")
        
        # 6. Mostrar estrutura das tabelas
        print("\n📋 Estrutura das tabelas criadas:")
        
        cursor.execute("PRAGMA table_info(solicitacoes_cadastro)")
        print("\n🔹 solicitacoes_cadastro:")
        for row in cursor.fetchall():
            print(f"   {row[1]} ({row[2]})")
            
        cursor.execute("PRAGMA table_info(senhas_temporarias)")
        print("\n🔹 senhas_temporarias:")
        for row in cursor.fetchall():
            print(f"   {row[1]} ({row[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Iniciando migração do sistema de profissionais...")
    
    if migrate_profissionais():
        print("\n🎉 Migração concluída com sucesso!")
        print("📝 Próximos passos:")
        print("   1. Criar rotas de cadastro de profissionais")
        print("   2. Criar página de cadastro no frontend")
        print("   3. Implementar sistema de aprovação")
        print("   4. Configurar envio de emails")
    else:
        print("\n💥 Falha na migração!")
