from app_cors_livre import create_app, db
from models import Profissional

app = create_app()

with app.app_context():
    email = 'abholzwarth@gmail.com'
    user = Profissional.query.filter_by(email=email).first()
    
    if user:
        print(f"Usuário encontrado: {user.nome} (ID: {user.id})")
        print(f"Role atual: {user.role}")
        
        user.role = 'admin'
        # Ensure status is approved in case that filters access too
        user.status_cadastro = 'aprovado' 
        
        try:
            db.session.commit()
            print(f"✅ Role atualizada para: {user.role}")
            print(f"✅ Status atualizado para: {user.status_cadastro}")
        except Exception as e:
            print(f"❌ Erro ao atualizar: {e}")
            db.session.rollback()
    else:
        print(f"❌ Usuário {email} não encontrado!")
        # Create if not exists? Maybe better not to assume credentials.
