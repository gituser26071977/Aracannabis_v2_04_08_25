import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT id, nome, email 
        FROM profissionais 
        ORDER BY id ASC 
        LIMIT 1
    """))
    profissional = result.fetchone()

if profissional:
    print(f"ID: {profissional[0]}")
    print(f"Nome: {profissional[1]}")
    print(f"Email: {profissional[2]}")
else:
    print("Nenhum profissional encontrado no banco de dados")
