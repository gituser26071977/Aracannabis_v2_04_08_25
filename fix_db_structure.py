import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
database_url = os.getenv("DATABASE_URL", "sqlite:///aracannabis.db")
print(f"🔌 Conectando ao banco de dados: {database_url}")

engine = create_engine(database_url)

def fix_database():
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 1. Verificar e criar tabela 'associacoes' se não existir
        if not inspector.has_table("associacoes"):
            print("⚠️ Tabela 'associacoes' não encontrada. Criando...")
            try:
                # Definição baseada em association/models.py
                conn.execute(text("""
                    CREATE TABLE associacoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome VARCHAR NOT NULL,
                        slug VARCHAR UNIQUE,
                        cnpj VARCHAR UNIQUE NOT NULL,
                        endereco VARCHAR,
                        telefone VARCHAR,
                        email VARCHAR,
                        ativo BOOLEAN DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("✅ Tabela 'associacoes' criada.")
            except Exception as e:
                print(f"❌ Erro ao criar tabela 'associacoes': {e}")
        else:
            print("✅ Tabela 'associacoes' já existe.")

        # 2. Verificar colunas na tabela 'pacientes'
        columns_pacientes = [col['name'] for col in inspector.get_columns('pacientes')]
        print(f"📊 Colunas atuais em 'pacientes': {columns_pacientes}")

        # 2.1 Adicionar 'associacao_id'
        if 'associacao_id' not in columns_pacientes:
            print("⚠️ Coluna 'associacao_id' faltando em 'pacientes'. Adicionando...")
            try:
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN associacao_id INTEGER REFERENCES associacoes(id)"))
                print("✅ Coluna 'associacao_id' adicionada.")
            except Exception as e:
                print(f"❌ Erro ao adicionar 'associacao_id': {e}")
        else:
            print("✅ Coluna 'associacao_id' já existe.")

        # 2.2 Adicionar 'profissional_responsavel_id'
        if 'profissional_responsavel_id' not in columns_pacientes:
            print("⚠️ Coluna 'profissional_responsavel_id' faltando em 'pacientes'. Adicionando...")
            try:
                # Adicionando como nullable inicialmente para evitar erro em registros existentes
                conn.execute(text("ALTER TABLE pacientes ADD COLUMN profissional_responsavel_id INTEGER REFERENCES profissionais(id)"))
                print("✅ Coluna 'profissional_responsavel_id' adicionada.")
            except Exception as e:
                print(f"❌ Erro ao adicionar 'profissional_responsavel_id': {e}")
        else:
            print("✅ Coluna 'profissional_responsavel_id' já existe.")

        # 3. Criar tabelas de Compliance IA (se solicitado no futuro, por enquanto focamos no core)
        # Mas vamos garantir que as tabelas de associação auxiliares existam
        if not inspector.has_table("membros_associacao"):
             print("⚠️ Tabela 'membros_associacao' não encontrada. Criando...")
             try:
                conn.execute(text("""
                    CREATE TABLE membros_associacao (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        associacao_id INTEGER NOT NULL REFERENCES associacoes(id),
                        cpf VARCHAR NOT NULL,
                        paciente_id INTEGER REFERENCES pacientes(id),
                        nome VARCHAR NOT NULL,
                        data_nascimento DATE,
                        endereco TEXT,
                        telefone VARCHAR,
                        email VARCHAR,
                        rg VARCHAR,
                        nome_responsavel VARCHAR,
                        observacoes TEXT,
                        data_filiacao DATE,
                        status VARCHAR DEFAULT 'ativo',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT uq_assoc_cpf UNIQUE (associacao_id, cpf)
                    );
                """))
                print("✅ Tabela 'membros_associacao' criada.")
             except Exception as e:
                 print(f"❌ Erro ao criar 'membros_associacao': {e}")

        conn.commit()
        print("\n🏁 Processo de correção de banco de dados finalizado.")

if __name__ == "__main__":
    fix_database()
