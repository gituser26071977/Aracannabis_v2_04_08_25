import os
import sys
from sqlalchemy import text

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

try:
    from app_cors_livre import create_app
    from models import db
except ImportError as e:
    print(f"Erro importando app: {e}")
    sys.exit(1)

def apply_sql(filename):
    print(f"Applying SQL from {filename}...")
    app = create_app()
    
    with app.app_context():
        with open(filename, 'r') as f:
            sql_content = f.read()
            
        # Split by command if necessary, or execute block
        # SQLAlchemy execute supports standard SQL
        try:
            with db.engine.connect() as conn:
                # Transação
                with conn.begin():
                    conn.execute(text(sql_content))
            print("Migration applied successfully.")
        except Exception as e:
            print(f"Error applying migration: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_sql.py <sql_file>")
        sys.exit(1)
        
    apply_sql(sys.argv[1])
