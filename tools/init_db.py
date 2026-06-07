import os
import sys

# Add root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

try:
    from app_cors_livre import create_app
    from models import db
    
    app = create_app()
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("Database initialized successfully.")
except Exception as e:
    print(f"Error initializing database: {e}")
    sys.exit(1)
