from app_cors_livre import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Verificando tabela upload_sessions...")
    try:
        # Tenta selecionar, se falhar cria
        db.session.execute(text("SELECT 1 FROM upload_sessions LIMIT 1"))
        print("Tabela upload_sessions já existe.")
    except Exception:
        print("Criando tabela upload_sessions...")
        db.session.rollback()
        # Create table manually using SQL to avoid extensive migrations setup for now
        db.session.execute(text("""
            CREATE TABLE upload_sessions (
                id SERIAL PRIMARY KEY,
                token VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(50) DEFAULT 'pending' NOT NULL,
                file_path VARCHAR(255),
                file_type VARCHAR(50),
                original_filename VARCHAR(255),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
            );
        """))
        db.session.commit()
        print("Tabela criada com sucesso.")
