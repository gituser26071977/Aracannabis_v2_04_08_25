from app import create_app
from models import db, Profissional
from werkzeug.security import generate_password_hash
import datetime

def create_admin_user():
    """
    Cria um usuário administrador padrão para o sistema.
    """
    app = create_app()
    
    with app.app_context():
        # Verificar se já existe um usuário admin
        admin = Profissional.query.filter_by(usuario='admin').first()
        
        if admin:
            print("Usuário admin já existe!")
            return
        
        # Criar usuário admin
        hashed_password = generate_password_hash('admin123')
        
        admin = Profissional(
            nome='Administrador',
            crm='ADMIN001',
            usuario='admin',
            senha=hashed_password,
            created_at=datetime.datetime.utcnow()
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("Usuário admin criado com sucesso!")
        print("Usuário: admin")
        print("Senha: admin123")

if __name__ == '__main__':
    create_admin_user()
