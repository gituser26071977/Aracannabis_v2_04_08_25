from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Profissional, SenhaTemporaria, Assinatura
from security_config import (
    validate_password_strength,
    sanitize_input,
    limiter,
    LOGIN_RATE_LIMIT,
    SENSITIVE_ENDPOINTS_RATE_LIMIT,
)
import re
import datetime
import logging
import secrets
import os
from services.email_service import EmailService
from models_extra import EmailVerification
from services.feature_flag_service import FeatureFlagService
from services.subscription_expiration_service import SubscriptionExpirationService

# Sprint S1 — EPIC 1 (Security & LGPD): provider de identidade unificado
# (araos.platform.identity.tokens.JWTTokenProvider). flask_jwt_extended
# permanece para as rotas legadas (~30); S2/S3 fará migração gradual.
from services.araos_auth import (
    issue_araos_token_pair,
    refresh_araos_token_pair,
    revoke_araos_token,
    araos_jwt_required,
    get_araos_current_user,
)

email_service = EmailService()

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)
profissionais_bp = Blueprint('profissionais', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit(LOGIN_RATE_LIMIT)
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
@limiter.limit(LOGIN_RATE_LIMIT)
def login():
    # P0-03 (Missão 18): ZERO PII em logs. Nunca logar identifier,
    # senha (mesmo hash parcial), tamanho de senha, ou payload bruto.
    data = request.get_json() or {}

    identifier = data.get('email') or data.get('usuario')
    senha_raw = data.get('senha')

    if not identifier or not senha_raw:
        logger.warning("login: payload incompleto (chaves=%d)", len(data))
        return jsonify({'error': 'Dados incompletos'}), 400

    # P0-04 (Missão 18): sanitize_input NUNCA deve ser aplicado em senhas.
    # Aplicar sanitize apenas em identifier.
    identifier = sanitize_input(identifier)

    # Log apenas métrica de presença, sem conteúdo
    logger.info("login: tentativa recebida (identifier_has_at=%s)", '@' in identifier)

    if '@' in identifier:
        profissional = Profissional.query.filter_by(email=identifier).first()
    else:
        profissional = Profissional.query.filter_by(usuario=identifier).first()

    if not profissional:
        logger.warning("login: identificador nao encontrado")
        return jsonify({'error': 'Credenciais inválidas'}), 401

    from werkzeug.security import check_password_hash
    # Verificação de senha SEM logar nada do material sensível
    senha_valida = check_password_hash(profissional.senha, senha_raw)

    if not senha_valida:
        logger.warning("login: credenciais invalidas")
        return jsonify({'error': 'Credenciais inválidas'}), 401

    logger.info("login: sucesso user_id=%s", profissional.id)

    # Verificar expiração (exceto admin e superadmin)
    trial_expired = False
    if profissional.role not in ['admin', 'superadmin'] and profissional.data_expiracao and profissional.data_expiracao < datetime.datetime.now():
        logger.warning(f"LOGIN - Acesso expirado para {profissional.usuario} (bloqueio suave)")
        trial_expired = True
        # Enviar email de aviso
        try:
            email_service.send_trial_expired_email(profissional.email, profissional.nome)
        except Exception as e:
            logger.error(f"Erro ao enviar email de expiração: {e}")
    
    expires = datetime.timedelta(hours=12)
    access_token = create_access_token(identity=str(profissional.id), expires_delta=expires)

    # Sprint S1 — emissão dual: AraOS (novo, primário) + flask_jwt_extended (legado)
    # O par AraOS suporta /api/auth/refresh; o legacy_access_token mantém
    # compatibilidade com rotas que ainda usam @jwt_required().
    try:
        araos_pair = issue_araos_token_pair(
            actor_id=str(profissional.id),
            tenant_id=str(profissional.tenant_id) if getattr(profissional, 'tenant_id', None) else "default",
            roles=[profissional.role] if getattr(profissional, 'role', None) else [],
            permissions=[],
            email=getattr(profissional, 'email', None),
            full_name=getattr(profissional, 'nome', None),
        )
    except Exception as exc:  # pragma: no cover — defesa em produção
        logger.error("AraOS issue falhou: %s", exc)
        return jsonify({'error': 'Falha ao emitir token de sessão'}), 500

    if trial_expired:
        return jsonify({
            'message': 'Login realizado, mas seu trial expirou.',
            'access_token': araos_pair.access_token,
            'refresh_token': araos_pair.refresh_token,
            'legacy_access_token': access_token,
            'user': profissional.to_dict(),
            'token_expires_in': araos_pair.expires_in,
            'token_expires_in_hours': 12,
            'trial_expired': True
        }), 200

    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': araos_pair.access_token,
        'refresh_token': araos_pair.refresh_token,
        'legacy_access_token': access_token,
        'user': profissional.to_dict(),
        'token_expires_in': araos_pair.expires_in,
        'token_expires_in_hours': 12
    }), 200


# ═══════════════════════════════════════════════════════════════════════
# Sprint S1 — EPIC 1: Refresh Token (item 1.4) + Logout (revogação)
# ═══════════════════════════════════════════════════════════════════════


@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit(LOGIN_RATE_LIMIT)
def refresh_token():
    """
    Renova par de tokens AraOS a partir de refresh_token válido.

    Request:
        {"refresh_token": "<jwt_refresh>"}

    Response 200:
        {"access_token": "<jwt>",
         "refresh_token": "<jwt>",  # novo (one-time use)
         "expires_in": 3600,
         "token_type": "Bearer"}

    Errors:
        400 — refresh_token ausente
        401 — refresh_token inválido/expirado/revogado
    """
    data = request.get_json() or {}
    refresh = data.get('refresh_token', '').strip()

    if not refresh:
        return jsonify({'error': 'refresh_token ausente'}), 400

    try:
        new_pair = refresh_araos_token_pair(refresh)
    except Exception as exc:
        # refresh_araos_token_pair levanta TokenExpiredError/TokenInvalidError
        # internamente via JWTTokenProvider; capturamos aqui.
        logger.warning("refresh: token inválido/expirado (%s)", type(exc).__name__)
        return jsonify({'error': 'refresh_token inválido ou expirado'}), 401
    except RuntimeError as exc:
        # Provider não inicializado
        logger.error("refresh: provider não disponível: %s", exc)
        return jsonify({'error': 'Auth não configurada'}), 503

    return jsonify({
        'access_token': new_pair.access_token,
        'refresh_token': new_pair.refresh_token,
        'expires_in': new_pair.expires_in,
        'token_type': new_pair.token_type,
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)
def logout():
    """
    Revoga o access_token AraOS ativo.

    Request:
        Header: Authorization: Bearer <access_token>

    Response 200:
        {"message": "Logout efetuado", "revoked": true|false}

    Errors:
        400 — header ausente
        401 — token inválido (idempotente: ainda retorna sucesso)
    """
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Authorization header ausente'}), 400

    token = auth.split(' ', 1)[1].strip()
    revoked = revoke_araos_token(token)
    return jsonify({'message': 'Logout efetuado', 'revoked': revoked}), 200


@auth_bp.route('/me', methods=['GET'])
@araos_jwt_required
def me():
    """
    Endpoint protegido demonstrativo do @araos_jwt_required.

    Retorna os claims do token ativo. Substitui o uso direto de
    flask_jwt_extended para rotas que migram para o provider AraOS.
    """
    user = get_araos_current_user() or {}
    return jsonify({'user': user}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Retorna o perfil do usuário autenticado"""
    current_user_id = get_jwt_identity()
    profissional = Profissional.query.get(int(current_user_id))
    
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404

    from services.perfil_acesso import resolver_perfil

    data = profissional.to_dict()
    data['perfil_efetivo'] = resolver_perfil(profissional)
    return jsonify({'user': data}), 200

@profissionais_bp.route('/profissionais/<int:prof_id>/assinatura', methods=['GET'])
@jwt_required()
def get_subscription(prof_id):
    """Retorna a assinatura do profissional"""
    current_user_id = get_jwt_identity()
    current_user = Profissional.query.get(int(current_user_id))
    
    # Only allow users to see their own subscription or admins to see any
    if current_user.id != prof_id and current_user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    profissional = Profissional.query.get(prof_id)
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    assinatura = Assinatura.query.filter_by(profissional_id=prof_id).first()
    if not assinatura:
        return jsonify({'error': 'Assinatura não encontrada'}), 404
    
    return jsonify(assinatura.to_dict()), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)
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
@limiter.limit(LOGIN_RATE_LIMIT)
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
@limiter.limit(LOGIN_RATE_LIMIT)
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
