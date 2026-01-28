from app_cors_livre import create_app
from models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check columns using raw SQL for postgres
        result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'exame_lab_resultados';"))
        columns = [row[0] for row in result]
        print(f"Columns in exame_lab_resultados: {columns}")
        
        if 'created_at' not in columns:
            print("Column 'created_at' is MISSING.")
        else:
            print("Column 'created_at' EXISTS.")
            
    except Exception as e:
        print(f"Error checking columns: {e}")
