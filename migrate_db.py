import os
import sqlite3
from app import create_app

def migrate_database():
    """
    Script para migrar o banco de dados adicionando as novas colunas LGPD e campos de dosagem
    """
    # Obter o caminho do banco de dados da aplicação
    app = create_app()
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print(f"Migrando banco de dados: {db_path}")
    
    # Verificar se o arquivo do banco de dados existe
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return False
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Migração da tabela pacientes
        print("Migrando tabela pacientes...")
        cursor.execute("PRAGMA table_info(pacientes)")
        pacientes_columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar coluna consentimento_lgpd se não existir
        if 'consentimento_lgpd' not in pacientes_columns:
            print("Adicionando coluna consentimento_lgpd à tabela pacientes")
            cursor.execute("ALTER TABLE pacientes ADD COLUMN consentimento_lgpd BOOLEAN DEFAULT 0")
        else:
            print("Coluna consentimento_lgpd já existe")
        
        # Adicionar coluna data_consentimento se não existir
        if 'data_consentimento' not in pacientes_columns:
            print("Adicionando coluna data_consentimento à tabela pacientes")
            cursor.execute("ALTER TABLE pacientes ADD COLUMN data_consentimento DATETIME")
        else:
            print("Coluna data_consentimento já existe")
        
        # Migração da tabela dosagens
        print("\nMigrando tabela dosagens...")
        cursor.execute("PRAGMA table_info(dosagens)")
        dosagens_columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar novas colunas à tabela dosagens
        new_dosagens_columns = {
            'gotas': 'INTEGER DEFAULT 0',
            'frequencia_diaria': 'INTEGER DEFAULT 1',
            'concentracao_cbd': 'FLOAT DEFAULT 0.0',
            'concentracao_thc': 'FLOAT DEFAULT 0.0',
            'concentracao_cbg': 'FLOAT DEFAULT 0.0',
            'concentracao_cbn': 'FLOAT DEFAULT 0.0'
        }
        
        for column_name, column_type in new_dosagens_columns.items():
            if column_name not in dosagens_columns:
                print(f"Adicionando coluna {column_name} à tabela dosagens")
                cursor.execute(f"ALTER TABLE dosagens ADD COLUMN {column_name} {column_type}")
            else:
                print(f"Coluna {column_name} já existe")
        
        # Commit das alterações
        conn.commit()
        print("\nMigração concluída com sucesso!")
        return True
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
