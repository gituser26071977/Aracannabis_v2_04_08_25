from app_cors_livre import create_app
from models import Profissional

app = create_app()
with app.app_context():
    admin = Profissional.query.filter_by(role='admin').first()
    if admin:
        print(f"Admin found: User={admin.usuario}, Email={admin.email}")
        # Note: We cannot retrieve the password as it is hashed, but we can reset it if needed.
    else:
        print("No admin user found.")
