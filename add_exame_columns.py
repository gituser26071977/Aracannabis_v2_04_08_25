from app_cors_livre import create_app, db
from sqlalchemy import text

def upgrade():
    app = create_app()
    # Add new columns to exames table
    with app.app_context():
        db.session.execute(text("ALTER TABLE exames ADD COLUMN titulo VARCHAR"))
        db.session.execute(text("ALTER TABLE exames ADD COLUMN descricao TEXT"))
        db.session.execute(text("ALTER TABLE exames ADD COLUMN valor FLOAT"))
        db.session.execute(text("ALTER TABLE exames ADD COLUMN unidade VARCHAR"))
        db.session.commit()
        print("Added new columns to exames table")

if __name__ == '__main__':
    upgrade()
