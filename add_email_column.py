import os
from sqlalchemy import create_engine, text

# Carregar configurações do .env
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aracannabis')

# Criar engine
engine = create_engine(DATABASE_URL)

# Comando SQL para adicionar a coluna
sql_command = """
ALTER TABLE profissionais
ADD COLUMN IF NOT EXISTS email TEXT;
"""

# Executar o comando
with engine.connect() as connection:
    connection.execute(text(sql_command))
    connection.commit()

print("Coluna 'email' adicionada com sucesso à tabela 'profissionais'!")
