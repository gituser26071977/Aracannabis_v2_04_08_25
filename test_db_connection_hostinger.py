#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL da Hostinger
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

def test_database_connection():
    """Testa a conexão com o banco de dados PostgreSQL"""
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter URL do banco
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ Erro: DATABASE_URL não encontrada no arquivo .env")
        print("📝 Exemplo de DATABASE_URL:")
        print("   DATABASE_URL=postgresql://usuario:senha@hostname:5432/nome_do_banco")
        return False
    
    print(f"🔗 Testando conexão com: {database_url.replace(database_url.split('@')[0].split('//')[1], '***:***')}")
    
    try:
        # Tentar conectar
        print("⏳ Conectando ao banco de dados...")
        conn = psycopg2.connect(database_url)
        
        # Testar uma query simples
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Conexão bem-sucedida!")
        print(f"📊 Versão do PostgreSQL: {version[0]}")
        
        # Testar se consegue criar uma tabela temporária
        cursor.execute("""
            CREATE TEMPORARY TABLE test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("INSERT INTO test_table (name) VALUES ('teste_conexao');")
        cursor.execute("SELECT * FROM test_table;")
        result = cursor.fetchone()
        
        print(f"🧪 Teste de escrita/leitura: {result}")
        
        # Fechar conexões
        cursor.close()
        conn.close()
        
        print("🎉 Todos os testes passaram! O banco está pronto para uso.")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erro de conexão: {e}")
        print("\n🔧 Possíveis soluções:")
        print("1. Verificar se as credenciais estão corretas")
        print("2. Verificar se o hostname/porta estão corretos")
        print("3. Verificar se o banco de dados existe")
        print("4. Verificar se o usuário tem permissões")
        return False
        
    except psycopg2.Error as e:
        print(f"❌ Erro do PostgreSQL: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def show_connection_info():
    """Mostra informações sobre como configurar a conexão"""
    print("\n" + "="*60)
    print("📋 CONFIGURAÇÃO DO BANCO POSTGRESQL NA HOSTINGER")
    print("="*60)
    print("\n1. Acesse o painel da Hostinger")
    print("2. Vá em 'Banco de Dados' > 'PostgreSQL'")
    print("3. Anote as seguintes informações:")
    print("   - Hostname (servidor)")
    print("   - Porta (geralmente 5432)")
    print("   - Nome do banco de dados")
    print("   - Usuário")
    print("   - Senha")
    print("\n4. Configure o arquivo .env:")
    print("   DATABASE_URL=postgresql://usuario:senha@hostname:5432/nome_do_banco")
    print("\n5. Para criar um novo banco de dados:")
    print("   - Conecte via psql ou phpPgAdmin")
    print("   - Execute: CREATE DATABASE aracannabis_prod;")
    print("   - Execute: CREATE USER aracannabis_user WITH PASSWORD 'senha_segura';")
    print("   - Execute: GRANT ALL PRIVILEGES ON DATABASE aracannabis_prod TO aracannabis_user;")
    print("\n6. Atualize a DATABASE_URL com o novo banco:")
    print("   DATABASE_URL=postgresql://aracannabis_user:senha_segura@hostname:5432/aracannabis_prod")

def create_database_schema():
    """Cria o schema básico do banco de dados"""
    load_dotenv()
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL não configurada")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("📊 Criando schema do banco de dados...")
        
        # Verificar se as tabelas já existem
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE';
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if existing_tables:
            print(f"📋 Tabelas existentes: {', '.join(existing_tables)}")
            response = input("⚠️  Tabelas já existem. Deseja recriar? (s/N): ")
            if response.lower() != 's':
                print("❌ Operação cancelada")
                return False
        
        # Aqui você pode adicionar o SQL para criar as tabelas
        # Por enquanto, vamos usar o SQLAlchemy para isso
        print("✅ Use 'python migrate_db.py' para criar as tabelas via SQLAlchemy")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE DE CONEXÃO POSTGRESQL - HOSTINGER")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        show_connection_info()
    elif len(sys.argv) > 1 and sys.argv[1] == "--create-schema":
        if test_database_connection():
            create_database_schema()
    else:
        success = test_database_connection()
        
        if not success:
            print("\n💡 Para ver instruções de configuração, execute:")
            print("   python test_db_connection_hostinger.py --info")
        else:
            print("\n🎯 Próximos passos:")
            print("1. Execute: python migrate_db.py")
            print("2. Execute: python create_secure_admin.py")
            print("3. Teste o sistema: python app.py")
