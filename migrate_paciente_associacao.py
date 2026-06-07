from app_cors_livre import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Migrando tabela Pacientes...")
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS associacao VARCHAR"))
            conn.commit()
            print("Coluna 'associacao' adicionada com sucesso.")
    except Exception as e:
        print(f"Erro na migração: {e}")
