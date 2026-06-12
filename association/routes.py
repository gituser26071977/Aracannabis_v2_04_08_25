import os
import secrets
from datetime import datetime, timedelta

from flask import request, jsonify
from models import db
from association import association_bp
from association.models import Associacao, ConviteProfissionalInstituicao, Membro, Estoque
from association.services.integration_service import IntegrationService
from association.services.dispensation_service import DispensationService
from association.validators import validar_cpf, validar_cnpj, normalizar_cpf, normalizar_cnpj
from flask_jwt_extended import jwt_required, get_jwt_identity

# --- Public Association Registration (No JWT required - used during professional signup) ---
@association_bp.route('/public-register', methods=['POST'])
def public_register_association():
    """Cadastro público de associação/clínica (usado antes do login no fluxo de cadastro profissional)"""
    return jsonify({
        'success': False,
        'error': 'Cadastro público de clínica desativado. Instituições devem ser criadas em área autenticada.'
    }), 403

# --- Association CRUD ---
@association_bp.route('/my-associations', methods=['GET'])
@jwt_required()
def get_my_associations():
    try:
        from models_extra import UsuarioAssociacao  # Import local para evitar ciclo
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get all active links for this user
        links = UsuarioAssociacao.query.filter_by(profissional_id=user_id, status='active').all()
        
        # Return the associations
        associations = [link.associacao.to_dict() for link in links]
        
        return jsonify(associations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@association_bp.route('/associations', methods=['POST'])
@jwt_required()
def create_association():
    from models_extra import UsuarioAssociacao  # Import local para evitar ciclo
    data = request.json
    
    # Validação e normalização do CNPJ
    cnpj = data.get('cnpj')
    if not validar_cnpj(cnpj):
        return jsonify({'error': 'CNPJ inválido'}), 400
    
    cnpj_normalizado = normalizar_cnpj(cnpj)
    
    new_assoc = Associacao(
        nome=data.get('nome'),
        cnpj=cnpj_normalizado,
        email=data.get('email'),
        endereco=data.get('endereco'),
        telefone=data.get('telefone')
    )
    db.session.add(new_assoc)
    try:
        db.session.commit()
        
        # Criar vínculo do usuário atual como admin
        user_id = int(get_jwt_identity())
        link = UsuarioAssociacao(
            profissional_id=user_id,
            associacao_id=new_assoc.id,
            role='admin',
            status='active'
        )
        db.session.add(link)
        db.session.commit()
        
        return jsonify(new_assoc.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@association_bp.route('/list', methods=['GET'])
@jwt_required()
def list_associations():
    try:
        assocs = Associacao.query.filter_by(ativo=True).all()
        return jsonify({
            'success': True,
            'associacoes': [a.to_dict() for a in assocs]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _is_association_admin(assoc_id, user_id):
    from models_extra import UsuarioAssociacao

    return UsuarioAssociacao.query.filter_by(
        profissional_id=user_id,
        associacao_id=assoc_id,
        status='active'
    ).filter(UsuarioAssociacao.role.in_(['admin'])).first() is not None


@association_bp.route('/associations/<int:assoc_id>/professional-invites', methods=['POST'])
@jwt_required()
def create_professional_invite(assoc_id):
    """
    Cria um convite de profissional OU staff para a instituição.

    Body (professional):
        { nome, email, telefone, role: 'member' (default) | 'admin', invite_type: 'professional' (default) }

    Body (staff):
        { nome, email, telefone, role: 'secretary' | 'manager' | 'admin' | 'member', invite_type: 'staff' }

    Staff: para convidar secretária/gestor, NÃO exige CRM/UF (sem conselho de classe).
    """
    user_id = int(get_jwt_identity())
    if not _is_association_admin(assoc_id, user_id):
        return jsonify({'success': False, 'error': 'Apenas administradores da instituição podem convidar profissionais.'}), 403

    assoc = Associacao.query.get_or_404(assoc_id)
    data = request.json or {}
    email = (data.get('email') or '').strip().lower() or None
    telefone = (data.get('telefone') or '').strip() or None
    nome = (data.get('nome') or '').strip() or None
    invite_type = (data.get('invite_type') or ConviteProfissionalInstituicao.INVITE_TYPE_PROFESSIONAL).strip()
    requested_role = (data.get('role') or '').strip() or None

    if invite_type not in ConviteProfissionalInstituicao.INVITE_TYPES:
        return jsonify({
            'success': False,
            'error': f'invite_type inválido. Valores aceitos: {list(ConviteProfissionalInstituicao.INVITE_TYPES)}',
        }), 400

    if not email and not telefone:
        return jsonify({'success': False, 'error': 'Informe email ou telefone para gerar o convite.'}), 400

    # Validar role contra allow-list do tipo de convite
    allowed_roles = ConviteProfissionalInstituicao.ROLES_BY_TYPE[invite_type]
    if requested_role and requested_role not in allowed_roles:
        return jsonify({
            'success': False,
            'error': f'role "{requested_role}" não permitida para invite_type="{invite_type}". Aceitas: {list(allowed_roles)}',
        }), 400

    # Default role por tipo
    if not requested_role:
        requested_role = 'member' if invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_PROFESSIONAL else 'secretary'

    convite = ConviteProfissionalInstituicao(
        associacao_id=assoc.id,
        convidado_por_id=user_id,
        nome=nome,
        email=email,
        telefone=telefone,
        role=requested_role,
        invite_type=invite_type,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.utcnow() + timedelta(days=7),
        status='pending'
    )
    db.session.add(convite)
    db.session.commit()

    # Audit log (Fase 1)
    try:
        from models_extra import create_audit_entry
        create_audit_entry(
            tenant_id=assoc.id,
            user_id=user_id,
            action='invite.create',
            resource_type='convite',
            resource_id=str(convite.id),
            details={
                'invite_type': invite_type,
                'role': requested_role,
                'email': email,
                'telefone_hash': convite.telefone[:3] + '***' if convite.telefone else None,
            },
        )
    except Exception:
        pass

    base_url = os.getenv('FRONTEND_BASE_URL') or os.getenv('BASE_URL') or 'http://localhost:3000'
    # Staff usa rota /convite-staff; profissional usa /cadastro-profissionais
    if invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_STAFF:
        invite_link = f"{base_url}/convite-staff/{convite.token}"
    else:
        invite_link = f"{base_url}/cadastro-profissionais?convite={convite.token}"

    email_sent = False
    if email:
        try:
            from services.email_service import EmailService
            svc = EmailService()
            if invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_STAFF:
                email_sent = svc.send_staff_invite_email(
                    email=email,
                    nome=nome,
                    instituicao_nome=assoc.nome,
                    invite_link=invite_link,
                    data_expiracao=convite.expires_at,
                    role_label=requested_role,
                )
            else:
                email_sent = svc.send_professional_invite_email(
                    email, nome, assoc.nome, invite_link, convite.expires_at
                )
        except Exception:
            email_sent = False

    return jsonify({
        'success': True,
        'convite': convite.to_dict(include_token=True),
        'invite_link': invite_link,
        'email_sent': email_sent,
    }), 201


@association_bp.route('/associations/<int:assoc_id>/professional-invites', methods=['GET'])
@jwt_required()
def list_professional_invites(assoc_id):
    """
    Lista convites da instituição com filtros opcionais.

    Query params:
      - status: 'pending' | 'accepted' | 'revoked' | 'expired' (vê todos se omitido)
      - invite_type: 'staff' | 'professional'
      - email: filtro parcial (LIKE)
    Apenas admin da instituição vê.
    """
    user_id = int(get_jwt_identity())
    if not _is_association_admin(assoc_id, user_id):
        return jsonify({'success': False, 'error': 'Apenas administradores da instituição podem listar convites.'}), 403

    Associacao.query.get_or_404(assoc_id)  # 404 se não existir

    query = ConviteProfissionalInstituicao.query.filter_by(associacao_id=assoc_id)

    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(ConviteProfissionalInstituicao.status == status_filter)

    invite_type_filter = request.args.get('invite_type')
    if invite_type_filter in ConviteProfissionalInstituicao.INVITE_TYPES:
        query = query.filter(ConviteProfissionalInstituicao.invite_type == invite_type_filter)

    email_filter = request.args.get('email')
    if email_filter:
        query = query.filter(ConviteProfissionalInstituicao.email.ilike(f"%{email_filter.lower()}%"))

    convites = query.order_by(ConviteProfissionalInstituicao.created_at.desc()).all()
    return jsonify({
        'success': True,
        'convites': [c.to_dict() for c in convites],
        'total': len(convites),
    }), 200


@association_bp.route('/professional-invites/<int:invite_id>/revoke', methods=['POST'])
@jwt_required()
def revoke_professional_invite(invite_id):
    """
    Revoga um convite pendente. Apenas admin da instituição correspondente.
    Idempotente — revogar convite já aceito/revogado não causa erro.
    """
    user_id = int(get_jwt_identity())
    convite = ConviteProfissionalInstituicao.query.get_or_404(invite_id)

    if not _is_association_admin(convite.associacao_id, user_id):
        return jsonify({'success': False, 'error': 'Apenas administradores da instituição podem revogar convites.'}), 403

    previous_status = convite.status
    convite.revoke(by_user_id=user_id)
    db.session.commit()

    # Audit log
    try:
        from models_extra import create_audit_entry
        create_audit_entry(
            tenant_id=convite.associacao_id,
            user_id=user_id,
            action='invite.revoke',
            resource_type='convite',
            resource_id=str(convite.id),
            details={'previous_status': previous_status, 'invite_type': convite.invite_type},
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'convite': convite.to_dict(),
        'message': 'Convite revogado.',
    }), 200


@association_bp.route('/professional-invites/<int:invite_id>/resend', methods=['POST'])
@jwt_required()
def resend_professional_invite(invite_id):
    """
    Reenvia email do convite. Apenas admin da instituição.
    Não reseta expires_at — se expirado, retorna 410.
    """
    user_id = int(get_jwt_identity())
    convite = ConviteProfissionalInstituicao.query.get_or_404(invite_id)

    if not _is_association_admin(convite.associacao_id, user_id):
        return jsonify({'success': False, 'error': 'Apenas administradores da instituição podem reenviar convites.'}), 403

    if not convite.is_valid():
        return jsonify({
            'success': False,
            'error': 'Convite expirado, já aceito ou revogado. Gere um novo convite.',
        }), 410

    if not convite.email:
        return jsonify({
            'success': False,
            'error': 'Convite não tem email. Compartilhe o link manualmente.',
        }), 400

    base_url = os.getenv('FRONTEND_BASE_URL') or os.getenv('BASE_URL') or 'http://localhost:3000'
    if convite.invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_STAFF:
        invite_link = f"{base_url}/convite-staff/{convite.token}"
    else:
        invite_link = f"{base_url}/cadastro-profissionais?convite={convite.token}"

    email_sent = False
    try:
        from services.email_service import EmailService
        svc = EmailService()
        if convite.invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_STAFF:
            email_sent = svc.send_staff_invite_email(
                email=convite.email,
                nome=convite.nome,
                instituicao_nome=convite.associacao.nome if convite.associacao else '',
                invite_link=invite_link,
                data_expiracao=convite.expires_at,
                role_label=convite.role,
            )
        else:
            email_sent = svc.send_professional_invite_email(
                convite.email, convite.nome,
                convite.associacao.nome if convite.associacao else '',
                invite_link, convite.expires_at,
            )
    except Exception:
        email_sent = False

    # Audit
    try:
        from models_extra import create_audit_entry
        create_audit_entry(
            tenant_id=convite.associacao_id,
            user_id=user_id,
            action='invite.resend',
            resource_type='convite',
            resource_id=str(convite.id),
            details={'email_sent': email_sent},
        )
    except Exception:
        pass

    return jsonify({
        'success': True,
        'email_sent': email_sent,
        'message': 'Email reenviado.' if email_sent else 'Falha ao enviar email. Tente novamente.',
    }), 200


@association_bp.route('/professional-invites/<token>', methods=['GET'])
def get_professional_invite(token):
    convite = ConviteProfissionalInstituicao.query.filter_by(token=token).first()
    if not convite:
        return jsonify({'success': False, 'error': 'Convite não encontrado.'}), 404
    if not convite.is_valid():
        return jsonify({'success': False, 'error': 'Convite expirado, já utilizado ou revogado.'}), 410

    return jsonify({
        'success': True,
        'convite': {
            'token': convite.token,
            'nome': convite.nome,
            'email': convite.email,
            'telefone': convite.telefone,
            'role': convite.role,
            'invite_type': convite.invite_type,
            'associacao_id': convite.associacao_id,
            'associacao_nome': convite.associacao.nome if convite.associacao else None,
            'expires_at': convite.expires_at.isoformat() if convite.expires_at else None
        }
    }), 200

@association_bp.route('/associations/<int:assoc_id>', methods=['GET'])
@jwt_required()
def get_association(assoc_id):
    assoc = Associacao.query.get_or_404(assoc_id)
    return jsonify(assoc.to_dict())

# --- Member Management ---
@association_bp.route('/associations/<int:assoc_id>/members', methods=['POST'])
@jwt_required()
def add_member(assoc_id):
    data = request.json
    cpf = data.get('cpf')
    
    # Validação do CPF
    if not validar_cpf(cpf):
        return jsonify({'error': 'CPF inválido'}), 400
    
    # Normalização do CPF antes de verificar duplicatas e salvar
    cpf_normalizado = normalizar_cpf(cpf)
    
    # Check duplicate (usando CPF normalizado)
    existing = Membro.query.filter_by(associacao_id=assoc_id, cpf=cpf_normalizado).first()
    if existing:
        return jsonify({'error': 'Member with this CPF already exists in this association'}), 400

    # Tenta encontrar o paciente no sistema (SIAP)
    patient = IntegrationService.find_patient_by_cpf(cpf_normalizado)
    
    if not patient:
         return jsonify({'error': 'Paciente não encontrado com este CPF. O membro deve ser um paciente cadastrado.'}), 400

    # Parse data_nascimento if provided
    data_nascimento = None
    if data.get('data_nascimento'):
        try:
            from datetime import datetime
            data_nascimento = datetime.strptime(data.get('data_nascimento'), '%Y-%m-%d').date()
        except ValueError:
            pass

    # Safely get patient attributes
    patient_nome = getattr(patient, 'nome', None) or data.get('nome')
    if not patient_nome:
        return jsonify({'error': 'Nome do paciente não encontrado. Por favor, forneça o nome.'}), 400

    new_member = Membro(
        associacao_id=assoc_id,
        nome=patient_nome,  # Usa o nome do paciente encontrado
        cpf=cpf_normalizado,
        data_nascimento=data_nascimento or getattr(patient, 'data_nascimento', None),
        endereco=data.get('endereco') or getattr(patient, 'endereco', None),
        telefone=data.get('telefone') or getattr(patient, 'telefone', None),
        email=data.get('email') or getattr(patient, 'email', None),
        rg=data.get('rg'),
        nome_responsavel=data.get('nome_responsavel'),
        observacoes=data.get('observacoes'),
        status='ativo',
        paciente_id=patient.id # Já vincula o ID do paciente
    )
    db.session.add(new_member)
    try:
        db.session.commit()
        return jsonify({
            'member': new_member.to_dict(),
            'link_status': f"Linked to Patient ID {patient.id}"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@association_bp.route('/associations/<int:assoc_id>/members', methods=['GET'])
@jwt_required()
def list_members(assoc_id):
    members = Membro.query.filter_by(associacao_id=assoc_id).all()
    return jsonify([m.to_dict() for m in members])

# --- Stock Management ---
@association_bp.route('/associations/<int:assoc_id>/stock', methods=['POST'])
@jwt_required()
def add_stock(assoc_id):
    data = request.json
    new_stock = Estoque(
        associacao_id=assoc_id,
        produto_id=data.get('produto_id'),
        quantidade=data.get('quantidade'),
        lote=data.get('lote'),
        validade=datetime.strptime(data.get('validade'), '%Y-%m-%d').date()
    )
    db.session.add(new_stock)
    db.session.commit()
    return jsonify(new_stock.to_dict()), 201

@association_bp.route('/associations/<int:assoc_id>/stock', methods=['GET'])
@jwt_required()
def get_stock(assoc_id):
    stock = Estoque.query.filter_by(associacao_id=assoc_id).all()
    return jsonify([s.to_dict() for s in stock])

# --- Dispensation ---
@association_bp.route('/associations/<int:assoc_id>/dispense', methods=['POST'])
@jwt_required()
def dispense(assoc_id):
    data = request.json
    success, result = DispensationService.dispense_product(
        associacao_id=assoc_id,
        membro_id=data.get('membro_id'),
        produto_id=data.get('produto_id'),
        quantidade=data.get('quantidade'),
        prescricao_id=data.get('prescricao_id'),
        observacoes=data.get('observacao', '')
    )
    
    if success:
        return jsonify(result.to_dict()), 200
    else:
        return jsonify({'error': result}), 400
