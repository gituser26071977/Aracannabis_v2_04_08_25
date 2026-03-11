from app_cors_livre import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Migrando tabela Pacientes (adicionando campos de auth)...")
    try:
        with db.engine.connect() as conn:
            migrations = [
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255)",
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE",
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP",
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS tdah_positivo BOOLEAN DEFAULT FALSE",
                "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS depressao_positiva BOOLEAN DEFAULT FALSE"
            ]
            
            for migration in migrations:
                print(f"Executando: {migration}")
                conn.execute(text(migration))
                
            conn.commit()
            print("✅ Campos de autenticação e diagnóstico adicionados com sucesso.")
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
