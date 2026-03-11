from app_cors_livre import create_app
from models import db
from models_extra import *

app = create_app()

with app.app_context():

    print("Registered tables:", db.metadata.tables.keys())
    print("Creating all missing tables...")
    db.create_all()

    print("Tables created successfully.")
