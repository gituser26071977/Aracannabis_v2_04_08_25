from flask import Flask
from models import db, Profissional
from werkzeug.security import generate_password_hash
import datetime

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
db.init_app(app)

def create_new_admin():
    with app.app_context():
        # Verificar se já existe um usuário admin2
        admin = Profissional.query.filter_by(usuario='admin2').first()
        
        if admin:
            print("Usuário admin2 já existe!")
            return
        
        # Senha simples para teste
        senha = "admin123"
        
        # Criar novo admin
        hashed_password = generate_password_hash(senha)
        
        novo_admin = Profissional(
            nome='Administrador 2',
            crm='ADMIN002',
            usuario='admin2',
            senha=hashed_password,
            created_at=datetime.datetime.utcnow()
        )
        
        try:
            db.session.add(novo_admin)
            db.session.commit()
            
            print("Novo usuário admin2 criado com sucesso!")
            print("Usuário: admin2")
            print(f"Senha: {senha}")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar usuário admin2: {str(e)}")

if __name__ == '__main__':
    create_new_admin()
