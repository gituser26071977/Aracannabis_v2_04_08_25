from app_cors_livre import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        print("Adding 'created_at' column to 'exame_lab_resultados'...")
        db.session.execute(text("ALTER TABLE exame_lab_resultados ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        db.session.commit()
        print("Column added successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding column: {e}")
