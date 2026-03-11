
from dotenv import load_dotenv
load_dotenv()

from app_cors_livre import create_app
from models import Profissional

def get_email():
    app = create_app()
    with app.app_context():
        try:
            # Find a user with an email
            user = Profissional.query.filter(Profissional.email.isnot(None)).first()
            if user:
                print(f"EMAIL:{user.email}")
            else:
                print("NO_EMAIL_FOUND")
        except Exception as e:
            print(f"ERROR:{e}")

if __name__ == "__main__":
    get_email()
