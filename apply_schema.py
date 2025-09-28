import os
from sqlalchemy import create_engine, text, inspect

# Carregar configurações do .env
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aracannabis')

# Criar engine
engine = create_engine(DATABASE_URL)

# Ler o arquivo de esquema
with open('database_schema.sql', 'r') as file:
    schema_sql = file.read()

# Executar o script SQL para criar tabelas
with engine.connect() as connection:
    connection.execute(text('COMMIT'))  # Sair de qualquer transação pendente
    connection.execute(text(schema_sql))

# Verificar e adicionar colunas ausentes
inspector = inspect(engine)
with engine.connect() as connection:
    # Verificar colunas em exame_lab_resultados
    if 'exame_lab_resultados' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('exame_lab_resultados')]
        if 'created_at' not in columns:
            connection.execute(text('ALTER TABLE exame_lab_resultados ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP'))
            print("Coluna created_at adicionada a exame_lab_resultados")

print("Esquema atualizado com sucesso!")
