from app_cors_livre import create_app
from models import db, Profissional
from werkzeug.security import generate_password_hash
from datetime import datetime
import secrets
import string

def generate_strong_password(length=16):
    """Gera uma senha forte com letras maiúsculas, minúsculas, números e símbolos"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_superadmin():
    app = create_app()
    with app.app_context():
        # Check if superadmin exists
        user = Profissional.query.filter_by(usuario='superadmin').first()
        
        if not user:
            print("👤 Creating 'superadmin' user...")
            
            # Generate strong password
            senha = generate_strong_password()
            senha_hash = generate_password_hash(senha)
            
            admin = Profissional(
                nome="Super Administrador",
                crm="ADMIN0001",
                uf_crm="BR",
                usuario="superadmin",
                email="superadmin@aracannabis.com.br",
                senha=senha_hash,
                role="superadmin",
                status_cadastro="aprovado",
                data_aprovacao=datetime.now()
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("\n" + "="*70)
            print("🔐 CREDENCIAIS DO SUPERADMIN CRIADAS COM SUCESSO")
            print("="*70)
            print(f"👤 Nome: Super Administrador")
            print(f"📧 Email: superadmin@aracannabis.com.br")
            print(f"🆔 Usuário: superadmin")
            print(f"🔑 Senha: {senha}")
            print(f"🎭 Role: superadmin")
            print("="*70)
            print("\n⚠️  ATENÇÃO: Salve estas credenciais em local seguro!")
            print("   Esta senha foi gerada automaticamente e é segura.")
            print("   Você pode alterá-la através da interface do sistema.")
            print("="*70 + "\n")
            
        else:
            print(f"ℹ️ Superadmin already exists with ID: {user.id}")
            print(f"📧 Email: {user.email}")
            print("Se deseja resetar a senha, use o script reset_superadmin_password.py")

if __name__ == '__main__':
    create_superadmin()
