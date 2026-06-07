from app_cors_livre import create_app, db
from models import Profissional
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = Profissional.query.filter_by(usuario='admin').first()
    if admin:
        print(f"Admin encontrado. Hash atual: {admin.senha[:20]}...")
        # Reset to known password
        new_pass = "Aracannabis@2025"
        admin.senha = generate_password_hash(new_pass, method='pbkdf2:sha256:100000')
        admin.email = "contato@arapath.com.br" # Defina um email válido para teste de recuperação
        try:
            db.session.commit()
            print(f"✅ Senha do admin resetada para: {new_pass}")
            print(f"✅ Email do admin definido para: {admin.email}")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            db.session.rollback()
    else:
        print("❌ Usuário admin não encontrado!")
