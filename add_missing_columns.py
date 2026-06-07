import os
from sqlalchemy import create_engine, text

# Carregar configurações do .env
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aracannabis')

# Criar engine
engine = create_engine(DATABASE_URL)

# Comandos SQL para adicionar as colunas faltantes
sql_commands = [
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS email TEXT;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS telefone TEXT;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS especialidade TEXT;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS instituicao TEXT;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS tipo_conta TEXT;",
    "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS data_expiracao TIMESTAMP;",
    """
    CREATE TABLE IF NOT EXISTS senhas_temporarias (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER NOT NULL,
        senha_hash TEXT NOT NULL,
        data_expiracao TIMESTAMP NOT NULL,
        usado BOOLEAN NOT NULL DEFAULT FALSE,
        FOREIGN KEY (usuario_id) REFERENCES profissionais(id) ON DELETE CASCADE
    );
    """
]

# Executar os comandos
with engine.connect() as connection:
    for command in sql_commands:
        connection.execute(text(command))
    connection.commit()

print("Todas as colunas faltantes foram adicionadas com sucesso à tabela 'profissionais'!")
