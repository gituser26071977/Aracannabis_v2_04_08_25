from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Profissional
from security_config import (
    validate_password_strength,
    sanitize_input
)
import re
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/create-admin', methods=['GET'])
def create_admin():
    """Cria um usuário administrador padrão"""
    admin = Profissional.query.filter_by(usuario='admin').first()
    if admin:
        return jsonify({'message': 'Usuário admin já existe!', 'usuario': 'admin'}), 200
    
    senha_segura = "Aracannabis@2025"
    hashed_password = generate_password_hash(senha_segura, method='pbkdf2:sha256:100000')
    
    admin = Profissional(
        nome='Administrador',
        crm='ADMIN001',
        uf_crm='XX',  # Dummy value for admin
        usuario='admin',
        senha=hashed_password,
        created_at=datetime.datetime.utcnow()
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
        return jsonify({
            'message': 'Usuário admin criado com sucesso!',
            'usuario': 'admin',
            'senha': '***SENHA OCULTA*** - Verificar logs do servidor'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar usuário admin: {str(e)}'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    data = sanitize_input(data)
    
    if not all(k in data for k in ('nome', 'crm', 'uf_crm', 'usuario', 'senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    if Profissional.query.filter_by(usuario=data['usuario']).first():
        return jsonify({'error': 'Nome de usuário já existe'}), 409
    
    if Profissional.query.filter_by(crm=data['crm'], uf_crm=data['uf_crm']).first():
        return jsonify({'error': 'CRM já cadastrado'}), 409
    
    if not re.match(r'^[0-9]{4,6}$', data['crm']):
        return jsonify({'error': 'Formato de CRM inválido'}), 400

    if not re.match(r'^[A-Z]{2}$', data['uf_crm']):
        return jsonify({'error': 'Formato de UF do CRM inválido'}), 400
    
    is_valid, error_msg = validate_password_strength(data['senha'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    hashed_password = generate_password_hash(data['senha'], method='pbkdf2:sha256:100000')
    
    novo_profissional = Profissional(
        nome=data['nome'],
        crm=data['crm'],
        uf_crm=data['uf_crm'],
        usuario=data['usuario'],
        senha=hashed_password
    )
    
    try:
        db.session.add(novo_profissional)
        db.session.commit()
        return jsonify({
            'message': 'Profissional cadastrado com sucesso',
            'profissional': novo_profissional.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao cadastrar: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Only require 'usuario' and 'senha' for login
    if 'usuario' not in data or 'senha' not in data:
        return jsonify({'error': 'Dados incompletos'}), 400
    
    # Sanitize inputs
    usuario = sanitize_input(data['usuario'])
    senha = sanitize_input(data['senha'])
    
    profissional = Profissional.query.filter_by(usuario=usuario).first()
    
    if not profissional or not check_password_hash(profissional.senha, senha):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    expires = datetime.timedelta(hours=1)
    access_token = create_access_token(identity=str(profissional.id), expires_delta=expires)
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': access_token,
        'user': profissional.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    profissional = Profissional.query.get(int(current_user_id))
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    return jsonify({
        'user': profissional.to_dict()
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    data = sanitize_input(data)
    
    if not all(k in data for k in ('senha_atual', 'nova_senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    profissional = Profissional.query.get(int(current_user_id))
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    if not check_password_hash(profissional.senha, data['senha_atual']):
        return jsonify({'error': 'Senha atual incorreta'}), 401
    
    is_valid, error_msg = validate_password_strength(data['nova_senha'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    hashed_password = generate_password_hash(data['nova_senha'], method='pbkdf2:sha256:100000')
    profissional.senha = hashed_password
    
    try:
        db.session.commit()
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500
