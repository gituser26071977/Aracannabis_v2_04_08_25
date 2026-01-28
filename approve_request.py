from app_cors_livre import create_app
from models import db, SolicitacoesCadastro, Profissional
from werkzeug.security import generate_password_hash
from services.email_service import EmailService
from datetime import datetime
import secrets
import string

app = create_app()
with app.app_context():
    solicitacao = SolicitacoesCadastro.query.get(5)
    if solicitacao and solicitacao.status == 'pendente':
        print(f"Approving request for {solicitacao.nome}...")
        
        # Gerar credenciais
        alphabet = string.ascii_letters + string.digits
        senha_temporaria = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        usuario_base = solicitacao.email.split('@')[0]
        usuario = usuario_base
        contador = 1
        while Profissional.query.filter_by(usuario=usuario).first():
            usuario = f"{usuario_base}{contador}"
            contador += 1
            
        novo_profissional = Profissional(
            nome=solicitacao.nome,
            crm=solicitacao.crm,
            uf_crm=solicitacao.uf_crm,
            usuario=usuario,
            email=solicitacao.email,
            senha=generate_password_hash(senha_temporaria),
            role='profissional'
        )
        db.session.add(novo_profissional)
        
        solicitacao.status = 'aprovada'
        solicitacao.data_aprovacao = datetime.now()
        db.session.commit()
        
        print("Request approved in DB.")
        
        # Trigger email
        email_service = EmailService()
        print(f"Sending email (Dev Mode: {email_service.development_mode})...")
        email_service.send_approval_email(solicitacao.email, solicitacao.nome, usuario, senha_temporaria, novo_profissional.data_expiracao)
        print("Email process completed.")
    else:
        print("Request not found or not pending.")
