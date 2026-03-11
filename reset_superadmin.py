from app_cors_livre import create_app, db
from models import Profissional
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()

with app.app_context():
    sa = Profissional.query.filter_by(usuario='superadmin').first()
    if sa:
        new_pass = "Aracannabis@Super2026"
        # Usando o mesmo método do auth.py para consistência
        sa.senha = generate_password_hash(new_pass, method='pbkdf2:sha256:100000')
        sa.status_cadastro = 'aprovado'
        if not sa.data_aprovacao:
            sa.data_aprovacao = datetime.now()
        
        try:
            db.session.commit()
            print(f"✅ Senha do superadmin resetada para: {new_pass}")
            print(f"✅ Status: {sa.status_cadastro}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar: {e}")
    else:
        print("❌ Usuário superadmin não encontrado!")
