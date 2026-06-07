#!/usr/bin/env python3
"""
Script de migração para criar a tabela de consultas
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import psycopg2

def criar_tabela_consultas():
    """Criar tabela de consultas no banco de dados"""
    
    # Obter configurações do banco
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada no arquivo .env")
        return False
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Verificando se a tabela 'consultas' já existe...")
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'consultas'
            );
        """)
        
        tabela_existe = cursor.fetchone()[0]
        
        if tabela_existe:
            print("✅ Tabela 'consultas' já existe no banco de dados")
            return True
        
        print("📝 Criando tabela 'consultas'...")
        
        # SQL para criar a tabela de consultas
        create_table_sql = """
        CREATE TABLE consultas (
            id SERIAL PRIMARY KEY,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
            profissional_id INTEGER REFERENCES profissionais(id) ON DELETE SET NULL,
            data_hora TIMESTAMP NOT NULL,
            duracao_minutos INTEGER NOT NULL DEFAULT 60,
            tipo_consulta VARCHAR NOT NULL DEFAULT 'presencial',
            status VARCHAR NOT NULL DEFAULT 'agendada',
            observacoes TEXT,
            google_event_id VARCHAR,
            lembrete_email_enviado BOOLEAN NOT NULL DEFAULT FALSE,
            lembrete_whatsapp_enviado BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.execute(create_table_sql)
        
        # Criar índices para melhor performance
        print("📊 Criando índices...")
        
        indices = [
            "CREATE INDEX idx_consultas_paciente_id ON consultas(paciente_id);",
            "CREATE INDEX idx_consultas_profissional_id ON consultas(profissional_id);",
            "CREATE INDEX idx_consultas_data_hora ON consultas(data_hora);",
            "CREATE INDEX idx_consultas_status ON consultas(status);",
            "CREATE INDEX idx_consultas_data_status ON consultas(data_hora, status);"
        ]
        
        for indice in indices:
            cursor.execute(indice)
        
        # Criar trigger para atualizar updated_at automaticamente
        print("⚡ Criando trigger para updated_at...")
        
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_consultas_updated_at 
            BEFORE UPDATE ON consultas 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        cursor.execute(trigger_sql)
        
        # Confirmar transação
        conn.commit()
        
        print("✅ Tabela 'consultas' criada com sucesso!")
        print("✅ Índices criados com sucesso!")
        print("✅ Trigger para updated_at criado com sucesso!")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erro ao criar tabela de consultas: {e}")
        if conn:
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verificar_estrutura():
    """Verificar se a estrutura da tabela está correta"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL não encontrada")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Verificando estrutura da tabela 'consultas'...")
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'consultas'
            ORDER BY ordinal_position;
        """)
        
        colunas = cursor.fetchall()
        
        if not colunas:
            print("❌ Tabela 'consultas' não encontrada")
            return False
        
        print("\n📋 Estrutura da tabela 'consultas':")
        print("-" * 60)
        for coluna in colunas:
            nome, tipo, nullable, default = coluna
            nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
            default_str = f" DEFAULT {default}" if default else ""
            print(f"  {nome:<25} {tipo:<20} {nullable_str}{default_str}")
        
        print("-" * 60)
        print(f"✅ Total de colunas: {len(colunas)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {e}")
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Função principal"""
    print("🏥 MIGRAÇÃO DO SISTEMA DE CONSULTAS - ARACANNABIS")
    print("=" * 50)
    
    # Criar tabela de consultas
    if criar_tabela_consultas():
        print("\n🎉 Migração concluída com sucesso!")
        
        # Verificar estrutura
        print("\n" + "=" * 50)
        verificar_estrutura()
        
        print("\n✅ Sistema de consultas pronto para uso!")
        print("\n📅 Funcionalidades disponíveis:")
        print("  • Agendamento de consultas")
        print("  • Calendário interativo")
        print("  • Lembretes por email e WhatsApp")
        print("  • Integração com Google Calendar (configurável)")
        print("  • Controle de status das consultas")
        print("  • Histórico completo de agendamentos")
        
    else:
        print("\n❌ Falha na migração!")
        sys.exit(1)

if __name__ == "__main__":
    main()
