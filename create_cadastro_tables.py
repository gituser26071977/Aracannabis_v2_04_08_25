#!/usr/bin/env python3
"""
Script para criar tabelas necessárias para o sistema de cadastro de profissionais
"""

import os
import sqlite3
from datetime import datetime

def create_tables():
    """Criar tabelas necessárias para o sistema de cadastro"""
    
    db_path = os.path.join("instance", "aracannabis.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Criando tabelas para sistema de cadastro...")
        
        # 1. Tabela de solicitações de cadastro
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solicitacoes_cadastro (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                crm TEXT NOT NULL,
                uf_crm TEXT NOT NULL,
                telefone TEXT,
                especialidade TEXT,
                instituicao TEXT,
                status TEXT DEFAULT 'pendente' CHECK(status IN ('pendente', 'aprovada', 'rejeitada')),
                data_solicitacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_aprovacao DATETIME,
                observacoes TEXT,
                aprovado_por INTEGER,
                FOREIGN KEY (aprovado_por) REFERENCES profissionais (id)
            )
        ''')
        
        # 2. Tabela de senhas temporárias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS senhas_temporarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                senha_hash TEXT NOT NULL,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_expiracao DATETIME NOT NULL,
                usado BOOLEAN DEFAULT 0,
                FOREIGN KEY (usuario_id) REFERENCES profissionais (id) ON DELETE CASCADE
            )
        ''')
        
        # 3. Verificar se a tabela profissionais tem as colunas necessárias
        cursor.execute("PRAGMA table_info(profissionais)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar colunas que podem estar faltando
        new_columns = [
            ('email', 'TEXT'),
            ('telefone', 'TEXT'),
            ('especialidade', 'TEXT'),
            ('instituicao', 'TEXT'),
            ('uf_crm', 'TEXT'),
            ('ativo', 'BOOLEAN DEFAULT 1'),
            ('tipo_conta', 'TEXT DEFAULT "permanente"'),
            ('data_expiracao', 'DATETIME')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f'ALTER TABLE profissionais ADD COLUMN {column_name} {column_type}')
                    print(f"✅ Coluna '{column_name}' adicionada à tabela profissionais")
                except Exception as e:
                    print(f"⚠️  Erro ao adicionar coluna '{column_name}': {e}")
        
        # 4. Criar índices para melhor performance
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_email ON solicitacoes_cadastro(email)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes_cadastro(status)",
            "CREATE INDEX IF NOT EXISTS idx_senhas_temp_usuario ON senhas_temporarias(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_senhas_temp_expiracao ON senhas_temporarias(data_expiracao)",
            "CREATE INDEX IF NOT EXISTS idx_profissionais_email ON profissionais(email)",
            "CREATE INDEX IF NOT EXISTS idx_profissionais_ativo ON profissionais(ativo)"
        ]
        
        for index_sql in indices:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"⚠️  Erro ao criar índice: {e}")
        
        conn.commit()
        print("✅ Tabelas criadas com sucesso!")
        
        # Verificar tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tabelas existentes no banco:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def test_email_system():
    """Testar sistema de email"""
    print("\n📧 Testando sistema de email...")
    
    try:
        from services.email_service import email_service
        
        success, message = email_service.test_connection()
        
        if success:
            print("✅ Conexão SMTP funcionando!")
            print(f"   Servidor: {email_service.smtp_server}:{email_service.smtp_port}")
            print(f"   Usuário: {email_service.username}")
            print(f"   Email de origem: {email_service.email_from}")
        else:
            print(f"❌ Erro na conexão SMTP: {message}")
            
        return success
        
    except Exception as e:
        print(f"❌ Erro ao testar email: {e}")
        return False

def main():
    print("🚀 Configurando sistema de cadastro de profissionais...")
    
    # Criar tabelas
    tables_created = create_tables()
    
    if not tables_created:
        print("❌ Falha ao criar tabelas. Abortando.")
        return
    
    # Testar email
    email_working = test_email_system()
    
    print(f"\n📊 RESUMO:")
    print(f"   ✅ Tabelas: {'OK' if tables_created else 'ERRO'}")
    print(f"   {'✅' if email_working else '❌'} Email: {'OK' if email_working else 'ERRO'}")
    
    if tables_created and email_working:
        print(f"\n🎉 Sistema de cadastro configurado com sucesso!")
        print(f"   - Usuários podem solicitar cadastro")
        print(f"   - Admins podem aprovar/rejeitar solicitações")
        print(f"   - Emails de confirmação serão enviados automaticamente")
    else:
        print(f"\n⚠️  Sistema parcialmente configurado. Verifique os erros acima.")

if __name__ == "__main__":
    main()
