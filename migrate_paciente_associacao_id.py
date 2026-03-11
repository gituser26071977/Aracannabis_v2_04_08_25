from app_cors_livre import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Migrando tabela Pacientes (adicionando associacao_id)...")
    try:
        with db.engine.connect() as conn:
            # Add column
            print("Adicionando coluna associacao_id...")
            conn.execute(text("ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS associacao_id INTEGER"))
            
            # Add Foreign Key constraint (nomeada para facilitar rollback se precisar)
            print("Adicionando Foreign Key fk_pacientes_associacao...")
            conn.execute(text("""
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_pacientes_associacao') THEN 
                        ALTER TABLE pacientes 
                        ADD CONSTRAINT fk_pacientes_associacao 
                        FOREIGN KEY (associacao_id) 
                        REFERENCES associacoes(id); 
                    END IF; 
                END $$;
            """))
            
            conn.commit()
            print("✅ Coluna 'associacao_id' e FK adicionadas com sucesso.")
            
    except Exception as e:
        print(f"❌ Erro na migração: {e}")
