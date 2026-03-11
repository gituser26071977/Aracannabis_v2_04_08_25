"""
Rotas de autenticação para pacientes

Permite que pacientes criem conta e façam login
"""

from flask import Blueprint, request, jsonify
from models import db, Paciente
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
import re

patient_auth_bp = Blueprint('patient_auth', __name__)

def validate_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_cpf(cpf):
    """Valida formato de CPF (apenas números, 11 dígitos)"""
    cpf_clean = re.sub(r'\D', '', cpf)
    return len(cpf_clean) == 11

@patient_auth_bp.route('/register', methods=['POST'])
def patient_register():
    """
    Paciente cria conta vinculada ao CPF existente
    
    Payload:
    {
        "cpf": "12345678900",
        "email": "paciente@email.com",
        "senha": "senha123"
    }
    """
    data = request.get_json()
    
    cpf = data.get('cpf')
    email = data.get('email')
    senha = data.get('senha')
    
    # Validações
    if not cpf or not email or not senha:
        return jsonify({'error': 'CPF, email e senha são obrigatórios'}), 400
    
    # Validar formato de email
    if not validate_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    # Validar formato de CPF
    if not validate_cpf(cpf):
        return jsonify({'error': 'CPF inválido. Use apenas números (11 dígitos)'}), 400
    
    # Validar senha (mínimo 6 caracteres)
    if len(senha) < 6:
        return jsonify({'error': 'Senha deve ter no mínimo 6 caracteres'}), 400
    
    # Limpar CPF
    cpf_clean = re.sub(r'\D', '', cpf)
    
    # Buscar paciente por CPF
    paciente = Paciente.query.filter_by(cpf=cpf_clean).first()
    
    # Se não existe localmente, tentar buscar no sistema externo
    import_data = None
    if not paciente:
        try:
            from association.services.external_integration_service import ExternalAssociationService
            # Tentar buscar dados externos
            external_data = ExternalAssociationService.search_associate(cpf_clean)
            
            if external_data:
                # Criar novo paciente com dados externos
                paciente = Paciente(
                    cpf=cpf_clean,
                    nome=external_data.get('nome') or 'Nome não informado',
                    email=email, # Usa o email fornecido no registro, pois é o login
                    telefone=external_data.get('telefone'),
                    endereco=external_data.get('endereco'),
                    rg=external_data.get('rg')
                )
                
                # Tratar data de nascimento se vier string
                if external_data.get('data_nascimento'):
                    try:
                        if isinstance(external_data.get('data_nascimento'), str):
                             paciente.data_nascimento = datetime.strptime(external_data.get('data_nascimento'), '%Y-%m-%d').date()
                    except:
                        pass
                        
                # Adicionar ao banco
                db.session.add(paciente)
                import_data = True
            else:
                 return jsonify({
                    'error': 'CPF não encontrado no sistema. Consulte seu médico para cadastro.'
                }), 404
        except Exception as e:
            print(f"Error checking external api: {e}")
            return jsonify({
                'error': 'CPF não encontrado no sistema. Consulte seu médico para cadastro.'
            }), 404
    
    # Se for paciente existente (não importado agora)
    if not import_data:
        # Verificar se paciente já tem email cadastrado/conta ativa
        if paciente.email and hasattr(paciente, 'senha_hash') and paciente.senha_hash:
            return jsonify({'error': 'Este CPF já possui conta cadastrada. Faça login.'}), 409
    
    # Verificar se email já está em uso por outro paciente
    existing_email = Paciente.query.filter(
        Paciente.email == email,
        Paciente.id != (paciente.id if paciente.id else -1) # id pode ser None se for novo
    ).first()
    
    if existing_email:
        return jsonify({'error': 'Este email já está cadastrado'}), 409
    
    # Atualizar paciente com credenciais
    paciente.email = email
    paciente.senha_hash = generate_password_hash(senha)
    
    # Usar getattr para campos que podem não existir ainda
    if hasattr(Paciente, 'is_active'):
        paciente.is_active = True
    if hasattr(Paciente, 'email_verified'):
        paciente.email_verified = False  # Futuramente implementar verificação
    
    try:
        db.session.commit()
        
        # TODO: Enviar email de boas-vindas
        
        return jsonify({
            'message': 'Conta criada com sucesso! Faça login para acessar seu prontuário.',
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'email': paciente.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar conta: {str(e)}'}), 500


@patient_auth_bp.route('/login', methods=['POST'])
def patient_login():
    """
    Login de paciente
    
    Payload:
    {
        "email": "paciente@email.com",
        "senha": "senha123"
    }
    """
    data = request.get_json()
    
    email = data.get('email')
    senha = data.get('senha')
    
    if not email or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Buscar paciente por email
    paciente = Paciente.query.filter_by(email=email).first()
    
    if not paciente:
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar se tem senha_hash (conta criada)
    if not hasattr(paciente, 'senha_hash') or not paciente.senha_hash:
        return jsonify({
            'error': 'Conta não configurada. Por favor, registre-se primeiro.'
        }), 401
    
    # Verificar senha
    if not check_password_hash(paciente.senha_hash, senha):
        return jsonify({'error': 'Credenciais inválidas'}), 401
    
    # Verificar se está ativo
    if hasattr(paciente, 'is_active') and not paciente.is_active:
        return jsonify({'error': 'Conta desativada. Contate o suporte.'}), 403
    
    # Gerar token com tipo 'patient'
    access_token = create_access_token(
        identity=str(paciente.id),
        additional_claims={'user_type': 'patient'},
        expires_delta=timedelta(hours=12)
    )
    
    # Atualizar last_login
    if hasattr(paciente, 'last_login_at'):
        paciente.last_login_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': paciente.id,
            'nome': paciente.nome,
            'email': paciente.email,
            'user_type': 'patient'
        },
        'message': 'Login realizado com sucesso'
    }), 200


@patient_auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_patient_info():
    """Retorna informações básicas do paciente logado"""
    
    # Verificar se é um paciente
    claims = get_jwt()
    if claims.get('user_type') != 'patient':
        return jsonify({'error': 'Acesso restrito a pacientes'}), 403
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    return jsonify({
        'paciente': paciente.to_dict()
    }), 200


@patient_auth_bp.route('/verify-cpf', methods=['POST'])
def verify_cpf():
    """
    Verifica se um CPF está cadastrado no sistema
    
    Endpoint público para o formulário de registro
    """
    data = request.get_json()
    cpf = data.get('cpf')
    
    if not cpf:
        return jsonify({'error': 'CPF é obrigatório'}), 400
    
    if not validate_cpf(cpf):
        return jsonify({'error': 'CPF inválido'}), 400
    
    cpf_clean = re.sub(r'\D', '', cpf)
    
    paciente = Paciente.query.filter_by(cpf=cpf_clean).first()
    
    if not paciente:
        # Tenta buscar no sistema externo
        try:
            from association.services.external_integration_service import ExternalAssociationService
            external_data = ExternalAssociationService.search_associate(cpf_clean)
            
            if external_data:
                return jsonify({
                    'exists': False,
                    'can_import': True,
                    'external_data': external_data,
                    'nome': external_data.get('nome'),
                    'message': 'CPF encontrado na Associação. Seus dados serão importados.'
                }), 200
        except Exception as e:
            print(f"Error checking external api: {e}")
            
        return jsonify({
            'exists': False,
            'can_import': False,
            'message': 'CPF não encontrado. Consulte seu médico para cadastro.'
        }), 200
    
    # Verificar se já tem conta
    has_account = bool(paciente.email and hasattr(paciente, 'senha_hash') and paciente.senha_hash)
    
    return jsonify({
        'exists': True,
        'has_account': has_account,
        'nome': paciente.nome if not has_account else None  # Só mostrar nome se não tiver conta
    }), 200
