from app_cors_livre import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Iniciando migração manual...")
    try:
        # Adicionar colunas em dosagens
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE dosagens ADD COLUMN IF NOT EXISTS tipo_dose VARCHAR DEFAULT 'fixa'"))
            conn.execute(text("ALTER TABLE dosagens ADD COLUMN IF NOT EXISTS esquema_doses JSON"))
            conn.execute(text("ALTER TABLE dosagens ADD COLUMN IF NOT EXISTS gotas_por_ml INTEGER DEFAULT 30"))
            conn.commit()
            print("Alterações em Dosagens aplicadas.")
            
        # Criar tabela prescricoes (SQLAlchemy create_all cria apenas as que faltam, mas se modelo mudou...)
        # Prescricao é nova, então create_all deve pegar.
        db.create_all()
        print("Tabelas novas criadas.")

    except Exception as e:
        print(f"Erro na migração manual: {e}")
