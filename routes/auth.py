from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Profissional, SenhaTemporaria
from security_config import (
    validate_password_strength,
    sanitize_input
)
import re
import datetime
import logging
import secrets
import os
from services.email_service import EmailService

email_service = EmailService()

logger = logging.getLogger(__name__)

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

    if data.get('email'):
        email = data['email'].lower().strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'error': 'Email inválido'}), 400
        if Profissional.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já cadastrado'}), 409
    
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
        senha=hashed_password,
        email=data.get('email')
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
    data = request.get_json() or {}

    # DEBUG LOG
    logger.info(f"LOGIN ATTEMPT - Raw data: {data}")

    identifier = data.get('email') or data.get('usuario')
    senha_raw = data.get('senha')

    if not identifier or not senha_raw:
        logger.warning(f"LOGIN FAILED - Dados incompletos: {list(data.keys())}")
        return jsonify({'error': 'Dados incompletos'}), 400

    # Sanitize inputs
    identifier = sanitize_input(identifier)
    senha = sanitize_input(senha_raw)

    logger.info(f"LOGIN ATTEMPT - Identificador: {identifier}, Senha length: {len(senha)}")

    if '@' in identifier:
        profissional = Profissional.query.filter_by(email=identifier).first()
    else:
        profissional = Profissional.query.filter_by(usuario=identifier).first()

    if not profissional:
        logger.warning("LOGIN FAILED - Identificador não encontrado")
        return jsonify({'error': 'Credenciais inválidas'}), 401

    if not check_password_hash(profissional.senha, senha):
        logger.warning("LOGIN FAILED - Senha incorreta para identificador informado")
        return jsonify({'error': 'Credenciais inválidas'}), 401

    logger.info(f"LOGIN SUCCESS - Usuario '{profissional.usuario}' logado com sucesso")

    # Verificar expiração (exceto admin)
    if profissional.role != 'admin' and profissional.data_expiracao and profissional.data_expiracao < datetime.datetime.now():
        logger.warning(f"LOGIN FAILED - Acesso expirado para {profissional.usuario}")
        pass
        # Enviar email de aviso
        try:
            email_service.send_trial_expired_email(profissional.email, profissional.nome)
        except Exception as e:
            logger.error(f"Erro ao enviar email de expiração: {e}")
            
        return jsonify({
            'error': 'Seu período de testes expirou. Atualize seu plano.',
            'expired': True
        }), 403
    
    expires = datetime.timedelta(hours=12)
    access_token = create_access_token(identity=str(profissional.id), expires_delta=expires)

    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': access_token,
        'user': profissional.to_dict(),
        'token_expires_in_hours': 12
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


@auth_bp.route('/request-password-setup', methods=['POST'])
def request_password_setup():
    data = request.get_json() or {}
    email = sanitize_input(data.get('email', '')).lower().strip()
    if not email:
        return jsonify({'error': 'Email é obrigatório'}), 400

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Email inválido'}), 400

    profissional = Profissional.query.filter_by(email=email).first()
    if not profissional:
        logger.info("PASSWORD SETUP: Email não encontrado")
        return jsonify({'error': 'Email não encontrado em nossa base de dados.'}), 404

    expiracao_horas = int(os.getenv('PASSWORD_SETUP_EXPIRATION_HOURS', '24'))
    data_expiracao = datetime.datetime.utcnow() + datetime.timedelta(hours=expiracao_horas)

    token = secrets.token_urlsafe(32)
    token_hash = generate_password_hash(token, method='pbkdf2:sha256:100000')

    try:
        SenhaTemporaria.query.filter_by(usuario_id=profissional.id, usado=False).update({'usado': True})
        nova_senha = SenhaTemporaria(
            usuario_id=profissional.id,
            senha_hash=token_hash,
            data_expiracao=data_expiracao,
            usado=False
        )
        db.session.add(nova_senha)
        db.session.commit()

        base_url = os.getenv('FRONTEND_BASE_URL') or os.getenv('BASE_URL') or 'http://localhost:3000'
        link_definicao = f"{base_url}/definir-senha?user_id={profissional.id}&token={token}"
        email_service.send_password_setup_email(
            profissional.email,
            profissional.nome,
            link_definicao,
            data_expiracao
        )
        return jsonify({'message': 'Link de recuperação enviado com sucesso! Verifique seu email.'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao gerar link de senha: {e}")
        return jsonify({'error': 'Erro ao gerar link de senha'}), 500


@auth_bp.route('/define-password', methods=['POST'])
def define_password():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    token = data.get('token', '')
    nova_senha = data.get('nova_senha', '')

    if not user_id or not token or not nova_senha:
        return jsonify({'error': 'Dados incompletos'}), 400

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Usuário inválido'}), 400

    profissional = Profissional.query.get(user_id_int)
    if not profissional:
        return jsonify({'error': 'Usuário inválido'}), 404

    senha_record = SenhaTemporaria.query.filter_by(
        usuario_id=profissional.id,
        usado=False
    ).order_by(SenhaTemporaria.id.desc()).first()

    if not senha_record:
        return jsonify({'error': 'Token inválido ou expirado'}), 400

    if senha_record.data_expiracao < datetime.datetime.utcnow():
        return jsonify({'error': 'Token expirado'}), 400

    if not check_password_hash(senha_record.senha_hash, token):
        return jsonify({'error': 'Token inválido'}), 400

    is_valid, error_msg = validate_password_strength(nova_senha)
    if not is_valid:
        return jsonify({'error': error_msg}), 400

    try:
        profissional.senha = generate_password_hash(nova_senha, method='pbkdf2:sha256:100000')
        senha_record.usado = True
        db.session.commit()
        return jsonify({'message': 'Senha definida com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao definir senha: {str(e)}'}), 500
