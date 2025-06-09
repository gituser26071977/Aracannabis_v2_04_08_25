from app import create_app # Importar create_app para usar o mesmo contexto da aplicação principal
from models import db, Profissional
from werkzeug.security import generate_password_hash
import datetime

# Não precisamos mais de um app Flask separado aqui, usaremos o contexto do create_app
# app = Flask(__name__)
# app.config.from_object('config.DevelopmentConfig') # Removido
# db.init_app(app) # Removido

def reset_admin_password():
    app = create_app() # Criar uma instância da aplicação para obter o contexto correto
    with app.app_context():
        # Encontrar o usuário admin
        admin = Profissional.query.filter_by(usuario='admin').first()
        
        if not admin:
            print("Usuário admin não encontrado!")
            return
        
        # Nova senha segura
        nova_senha = "Aracannabis@2025"
        
        # Atualizar a senha
        admin.senha = generate_password_hash(nova_senha, method='pbkdf2:sha256:100000')
        admin.updated_at = datetime.datetime.utcnow()
        
        # Salvar as alterações
        db.session.commit()
        
        print(f"Senha do usuário admin resetada com sucesso!")
        print(f"Nova senha: {nova_senha}")

if __name__ == '__main__':
    reset_admin_password()
