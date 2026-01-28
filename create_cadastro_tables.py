#!/usr/bin/env python3
"""
Script para criar tabelas necessárias para o sistema de cadastro de profissionais
usando PostgreSQL.
"""

import os
from sqlalchemy import create_engine, text

DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/aracannabis"

def create_tables():
    """Criar tabelas necessárias para o sistema de cadastro"""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_engine(database_url)

    try:
        print("🔧 Criando tabelas para sistema de cadastro...")

        ddl_commands = [
            """
            CREATE TABLE IF NOT EXISTS solicitacoes_cadastro (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                crm TEXT NOT NULL,
                uf_crm TEXT NOT NULL,
                telefone TEXT,
                especialidade TEXT,
                instituicao TEXT,
                status TEXT NOT NULL DEFAULT 'pendente',
                data_solicitacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_aprovacao TIMESTAMP,
                observacoes TEXT,
                aprovado_por INTEGER REFERENCES profissionais(id) ON DELETE SET NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS senhas_temporarias (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES profissionais(id) ON DELETE CASCADE,
                senha_hash TEXT NOT NULL,
                data_expiracao TIMESTAMP NOT NULL,
                usado BOOLEAN NOT NULL DEFAULT FALSE
            );
            """,
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS email TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS telefone TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS especialidade TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS instituicao TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS uf_crm TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS tipo_conta TEXT;",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS data_expiracao TIMESTAMP;"
        ]

        index_commands = [
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_email ON solicitacoes_cadastro(email)",
            "CREATE INDEX IF NOT EXISTS idx_solicitacoes_status ON solicitacoes_cadastro(status)",
            "CREATE INDEX IF NOT EXISTS idx_senhas_temp_usuario ON senhas_temporarias(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_senhas_temp_expiracao ON senhas_temporarias(data_expiracao)",
            "CREATE INDEX IF NOT EXISTS idx_profissionais_email ON profissionais(email)",
            "CREATE INDEX IF NOT EXISTS idx_profissionais_ativo ON profissionais(ativo)"
        ]

        with engine.connect() as connection:
            for command in ddl_commands:
                connection.execute(text(command))
            for command in index_commands:
                connection.execute(text(command))
            connection.commit()

        print("✅ Tabelas criadas com sucesso!")

        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result.fetchall()]

            print("\n📋 Tabelas existentes no banco:")
            for table in tables:
                count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"   - {table}: {count} registros")

        return True

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False

def test_email_system():
    """Testar sistema de email"""
    print("\n📧 Testando sistema de email...")
    
    try:
        from services.email_service import EmailService
        email_service = EmailService()
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
