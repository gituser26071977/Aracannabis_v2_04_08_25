from models import db
from flask import Flask
from config import Config
from sqlalchemy import text
import logging

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def add_column():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if column exists is harder in raw sql, so we just try to add it and ignore if fails or verify first.
                # But here we will simple execute ALTER TABLE.
                print("Adding column data_registro to produtos table...")
                conn.execute(text("ALTER TABLE produtos ADD COLUMN data_registro DATE"))
                conn.execute(text("UPDATE produtos SET data_registro = DATE(created_at) WHERE data_registro IS NULL"))
                conn.commit()
                print("Column added successfully.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    add_column()
