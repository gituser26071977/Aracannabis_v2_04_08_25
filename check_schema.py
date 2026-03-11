from app_cors_livre import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Tenta selecionar novas colunas
        db.session.execute(text("SELECT tipo_dose, esquema_doses FROM dosagens LIMIT 1"))
        print("Tabela dosagens OK: tipo_dose e esquema_doses encontrados.")
        
        db.session.execute(text("SELECT id FROM prescricoes LIMIT 1"))
        print("Tabela prescricoes OK.")
        
    except Exception as e:
        print(f"ERRO SCHEMA: {e}")
