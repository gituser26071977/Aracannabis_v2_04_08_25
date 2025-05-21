from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Profissional, LogAtividade
import re
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/create-admin', methods=['GET'])
def create_admin():
    """Cria um usuário administrador padrão"""
    # Verificar se já existe um usuário admin
    admin = Profissional.query.filter_by(usuario='admin').first()
    
    if admin:
        return jsonify({'message': 'Usuário admin já existe!', 'usuario': 'admin'}), 200
    
    # Criar usuário admin
    hashed_password = generate_password_hash('admin123')
    
    admin = Profissional(
        nome='Administrador',
        crm='ADMIN001',
        usuario='admin',
        senha=hashed_password,
        created_at=datetime.datetime.utcnow()
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=admin.id,
            acao='Criação de Conta',
            detalhes='Usuário administrador padrão criado'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário admin criado com sucesso!',
            'usuario': 'admin',
            'senha': 'admin123'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar usuário admin: {str(e)}'}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validar dados
    if not all(k in data for k in ('nome', 'crm', 'usuario', 'senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    # Verificar se usuário ou CRM já existem
    if Profissional.query.filter_by(usuario=data['usuario']).first():
        return jsonify({'error': 'Nome de usuário já existe'}), 409
    
    if Profissional.query.filter_by(crm=data['crm']).first():
        return jsonify({'error': 'CRM já cadastrado'}), 409
    
    # Validar formato do CRM (exemplo simples)
    if not re.match(r'^[A-Z0-9]{4,10}$', data['crm']):
        return jsonify({'error': 'Formato de CRM inválido'}), 400
    
    # Criar novo profissional
    hashed_password = generate_password_hash(data['senha'])
    
    novo_profissional = Profissional(
        nome=data['nome'],
        crm=data['crm'],
        usuario=data['usuario'],
        senha=hashed_password
    )
    
    try:
        db.session.add(novo_profissional)
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=novo_profissional.id,
            acao='Registro',
            detalhes=f'Novo profissional registrado: {data["nome"]}'
        )
        db.session.add(log)
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
    
    if not all(k in data for k in ('usuario', 'senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    profissional = Profissional.query.filter_by(usuario=data['usuario']).first()
    
    if not profissional or not check_password_hash(profissional.senha, data['senha']):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Criar token JWT
    access_token = create_access_token(identity={
        'id': profissional.id,
        'nome': profissional.nome,
        'usuario': profissional.usuario
    })
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional.id,
        acao='Login',
        detalhes=f'Login realizado: {profissional.nome}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': access_token,
        'user': profissional.to_dict()
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    profissional = Profissional.query.get(profissional_id)
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    return jsonify({
        'user': profissional.to_dict()
    }), 200

@auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_auth():
    current_user = get_jwt_identity()
    return jsonify({
        'authenticated': True,
        'user': current_user
    }), 200
