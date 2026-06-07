from flask import Flask
from models import db, Profissional
from werkzeug.security import generate_password_hash
import datetime

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
db.init_app(app)

def create_secure_admin():
    with app.app_context():
        # Verificar se já existe um usuário admin3
        admin = Profissional.query.filter_by(usuario='admin3').first()
        
        if admin:
            print("Usuário admin3 já existe!")
            return
        
        # Senha segura que atende a todos os requisitos
        senha = "Admin@123456"
        
        # Criar novo admin
        hashed_password = generate_password_hash(senha, method='pbkdf2:sha256:100000')
        
        novo_admin = Profissional(
            nome='Administrador 3',
            crm='ADMIN003',
            usuario='admin3',
            senha=hashed_password,
            created_at=datetime.datetime.utcnow()
        )
        
        try:
            db.session.add(novo_admin)
            db.session.commit()
            
            print("Novo usuário admin3 criado com sucesso!")
            print("Usuário: admin3")
            print(f"Senha: {senha}")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar usuário admin3: {str(e)}")

if __name__ == '__main__':
    create_secure_admin()
