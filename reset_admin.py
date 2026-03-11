import os
from flask import Flask
from models import db, Profissional, UsuarioAssociacao
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db.init_app(app)

with app.app_context():
    from flask_sqlalchemy import SQLAlchemy
    try:
        # Tentar atualizar todos admins
        admins = Profissional.query.filter_by(usuario='admin3').all()
        for a in admins:
            a.senha = generate_password_hash('Admin@123456')
            a.ativo = True
            print(f"Senha de {a.usuario} resetada com sucesso para Admin@123456")
        db.session.commit()
    except Exception as e:
        print(f"Erro ao resetar: {e}")
