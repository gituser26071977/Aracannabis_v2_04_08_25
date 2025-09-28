import os
import sys
from sqlalchemy import text
from flask import Flask

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from models import db
from config import Config

# Create a minimal Flask app instance
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def add_chartable_column():
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(
                text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = 'exames' 
                    AND column_name = 'is_chartable'
                )
                """)
            ).scalar()

            if not result:
                print("Adding 'is_chartable' column to exames table...")
                
                # Add the new column
                db.session.execute(
                    text("""
                    ALTER TABLE exames
                    ADD COLUMN is_chartable BOOLEAN NOT NULL DEFAULT FALSE
                    """)
                )
                db.session.commit()
                print("Column added successfully!")
            else:
                print("'is_chartable' column already exists. No changes made.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error adding column: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    add_chartable_column()
