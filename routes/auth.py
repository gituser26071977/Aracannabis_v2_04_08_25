from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Profissional, LogAtividade
from security_config import (
    validate_password_strength, 
    csrf_protect, 
    sanitize_input,
    mask_sensitive_data
)
import re
import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/create-admin', methods=['GET'])
def create_admin():
    """Cria um usuário administrador padrão"""
    # Verificar se já existe um usuário admin
    admin = Profissional.query.filter_by(usuario='admin').first()
    
    if admin:
        return jsonify({'message': 'Usuário admin já existe!', 'usuario': 'admin'}), 200
    
    # Senha forte que atende aos requisitos de segurança
    senha_segura = "Aracannabis@2025"
    
    # Criar usuário admin com hash seguro
    hashed_password = generate_password_hash(senha_segura, method='pbkdf2:sha256:100000')
    
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
            detalhes='Usuário administrador padrão criado com senha segura'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário admin criado com sucesso!',
            'usuario': 'admin',
            'senha': senha_segura,
            'nota': 'Esta senha atende aos requisitos de segurança. Recomendamos alterá-la após o primeiro login.'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar usuário admin: {str(e)}'}), 500

# Decorator para registrar tentativas de login
def log_login_attempt(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obter o IP do cliente
        ip = request.remote_addr
        
        # Registrar tentativa no log (poderia ser expandido para um sistema mais robusto)
        print(f"Tentativa de login de {ip} em {datetime.datetime.now()}")
        
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
@csrf_protect
def register():
    data = request.get_json()
    
    # Sanitizar dados de entrada
    data = sanitize_input(data)
    
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
    
    # Validar força da senha
    is_valid, error_msg = validate_password_strength(data['senha'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Criar novo profissional
    hashed_password = generate_password_hash(data['senha'], method='pbkdf2:sha256:100000')
    
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
@csrf_protect
@log_login_attempt
def login():
    data = request.get_json()
    
    # Sanitizar dados de entrada
    data = sanitize_input(data)
    
    if not all(k in data for k in ('usuario', 'senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    profissional = Profissional.query.filter_by(usuario=data['usuario']).first()
    
    if not profissional or not check_password_hash(profissional.senha, data['senha']):
        # Registrar falha de login
        log = LogAtividade(
            profissional_id=profissional.id if profissional else None,
            acao='Falha de Login',
            detalhes=f'Tentativa de login falhou para usuário: {data["usuario"]}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Criar token JWT com tempo de expiração
    expires = datetime.timedelta(hours=1)
    access_token = create_access_token(
        identity=str(profissional.id),
        expires_delta=expires
    )
    
    # Criar refresh token
    refresh_expires = datetime.timedelta(days=7)
    refresh_token = create_access_token(
        identity=str(profissional.id),
        expires_delta=refresh_expires,
        additional_claims={"refresh": True}
    )
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional.id,
        acao='Login',
        detalhes=f'Login realizado: {profissional.nome}'
    )
    db.session.add(log)
    db.session.commit()
    
    # Mascarar dados sensíveis
    user_data = profissional.to_dict()
    if 'crm' in user_data:
        user_data['crm'] = mask_sensitive_data(user_data['crm'], 'crm')
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': 3600,  # 1 hora em segundos
        'user': user_data,
        'csrf_token': current_app.config['CSRF_TOKEN']
    }), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    profissional = Profissional.query.get(profissional_id)
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    # Mascarar dados sensíveis
    user_data = profissional.to_dict()
    if 'crm' in user_data:
        user_data['crm'] = mask_sensitive_data(user_data['crm'], 'crm')
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes='Consulta ao perfil'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'user': user_data,
        'csrf_token': current_app.config['CSRF_TOKEN']
    }), 200

@auth_bp.route('/check', methods=['GET'])
@jwt_required()
def check_auth():
    current_user_id = get_jwt_identity()
    profissional = Profissional.query.get(int(current_user_id))
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    # Mascarar dados sensíveis
    user_data = profissional.to_dict()
    if 'crm' in user_data:
        user_data['crm'] = mask_sensitive_data(user_data['crm'], 'crm')
    
    return jsonify({
        'authenticated': True,
        'user': user_data,
        'csrf_token': current_app.config['CSRF_TOKEN']
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@csrf_protect
def change_password():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    
    # Sanitizar dados de entrada
    data = sanitize_input(data)
    
    if not all(k in data for k in ('senha_atual', 'nova_senha')):
        return jsonify({'error': 'Dados incompletos'}), 400
    
    profissional = Profissional.query.get(profissional_id)
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    # Verificar senha atual
    if not check_password_hash(profissional.senha, data['senha_atual']):
        return jsonify({'error': 'Senha atual incorreta'}), 401
    
    # Validar força da nova senha
    is_valid, error_msg = validate_password_strength(data['nova_senha'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Atualizar senha
    hashed_password = generate_password_hash(data['nova_senha'], method='pbkdf2:sha256:100000')
    profissional.senha = hashed_password
    profissional.updated_at = datetime.datetime.utcnow()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Alteração de Senha',
        detalhes='Senha alterada com sucesso'
    )
    
    try:
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Senha alterada com sucesso'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500
