from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from models import db, Profissional
from config import Config

app = Flask(__name__)
app.config.from_object(Config())
db.init_app(app)
jwt = JWTManager(app)  # Initialize JWTManager

with app.app_context():
    # Create test user with valid fields
    # Generate unique credentials using timestamp
    import time
    timestamp = int(time.time() * 1000)
    unique_crm = str(timestamp)[-6:]
    unique_username = f"testuser_{str(timestamp)[-6:]}"
    
    test_user = Profissional(
        nome='Test User',
        usuario=unique_username,
        senha='testpassword',
        crm=unique_crm,
        uf_crm='SP'
    )

    # Add to session and commit
    db.session.add(test_user)
    db.session.commit()

    # Generate token
    access_token = create_access_token(identity=str(test_user.id))
    print(f'TEST_TOKEN={access_token}')
