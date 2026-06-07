from dotenv import load_dotenv
from datetime import datetime, timedelta
from services.email_service import EmailService
from models import db
from sqlalchemy import text

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar serviço de email
email_service = EmailService()

def reenviar_credenciais(profissional_id):
    try:
        # Buscar profissional
        query = text("SELECT * FROM profissionais WHERE id = :id")
        result = db.session.execute(query, {'id': profissional_id})
        profissional = result.fetchone()
        
        if not profissional:
            print("Profissional não encontrado")
            return False
        
        # Gerar nova senha temporária
        def gerar_senha_temporaria():
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            return ''.join(secrets.choice(alphabet) for _ in range(12))
        
        nova_senha_temporaria = gerar_senha_temporaria()
        from werkzeug.security import generate_password_hash
        nova_senha_hash = generate_password_hash(nova_senha_temporaria)
        
        nova_data_expiracao = datetime.now() + timedelta(days=7)
        
        # Atualizar senha no banco de dados
        query = text('''
            UPDATE profissionais
            SET senha = :senha, data_expiracao = :data_expiracao
            WHERE id = :id
        ''')
        db.session.execute(query, {
            'senha': nova_senha_hash,
            'data_expiracao': nova_data_expiracao,
            'id': profissional_id
        })
        
        # Atualizar registro de senha temporária
        query = text('''
            UPDATE senhas_temporarias
            SET senha_hash = :senha_hash, data_expiracao = :data_expiracao, usado = FALSE
            WHERE usuario_id = :usuario_id
        ''')
        db.session.execute(query, {
            'senha_hash': nova_senha_hash,
            'data_expiracao': nova_data_expiracao,
            'usuario_id': profissional_id
        })
        
        db.session.commit()
        
        # Enviar email com novas credenciais
        email_enviado = email_service.send_approval_email(
            profissional.email, 
            profissional.nome, 
            profissional.usuario, 
            nova_senha_temporaria, 
            nova_data_expiracao
        )
        
        if email_enviado:
            print(f"Credenciais reenviadas para {profissional.email}")
            return True
        else:
            print(f"Falha ao enviar email para {profissional.email}")
            return False
            
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao reenviar credenciais: {e}")
        return False

if __name__ == "__main__":
    # ID do profissional para reenviar credenciais
    profissional_id = 2  # ID do usuário teste@example.com
    
    # Inicializar banco de dados
    from app_cors_livre import create_app
    app = create_app()
    with app.app_context():
        reenviar_credenciais(profissional_id)
