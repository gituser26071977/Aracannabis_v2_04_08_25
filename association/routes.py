from flask import request, jsonify, g
from models import db
from association import association_bp
from association.models import Associacao, Membro, Estoque
from association.services.integration_service import IntegrationService
from association.services.dispensation_service import DispensationService
from association.validators import validar_cpf, validar_cnpj, normalizar_cpf, normalizar_cnpj
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.auth_decorators import require_clinica_management


# ================================================================
# Helpers de autorização: checa se o user logado é admin da clínica
# ================================================================
def _is_clinica_admin(user_id: int, assoc_id: int) -> bool:
    """
    Verifica se o user é admin ativo da clínica.
    Superadmin global também passa (bypass).
    """
    from models import Profissional
    from models_extra import UsuarioAssociacao

    prof = Profissional.query.get(user_id)
    if prof and prof.role == 'superadmin':
        return True

    link = UsuarioAssociacao.query.filter_by(
        profissional_id=user_id,
        associacao_id=assoc_id,
        role='admin',
        status='active',
    ).first()
    return link is not None


# --- Public endpoint (não exige plano, não exige login) ---
@association_bp.route('/list', methods=['GET'])
def list_associations():
    """Lista pública de clínicas ativas (usado em landing pages, etc)."""
    try:
        assocs = Associacao.query.filter_by(ativo=True).all()
        return jsonify({
            'success': True,
            'associacoes': [a.to_dict() for a in assocs]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ================================================================
# CRUD de Clínica — exige plano Premium/Enterprise
# ================================================================

# --- My Associations (lista do user logado) ---
@association_bp.route('/my-associations', methods=['GET'])
@jwt_required()
@require_clinica_management
def get_my_associations():
    try:
        from models_extra import UsuarioAssociacao
        user_id = int(get_jwt_identity())
        links = UsuarioAssociacao.query.filter_by(profissional_id=user_id, status='active').all()
        associations = [link.associacao.to_dict() for link in links if link.associacao.ativo]
        return jsonify(associations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- CREATE ---
@association_bp.route('/associations', methods=['POST'])
@jwt_required()
@require_clinica_management
def create_association():
    from models_extra import UsuarioAssociacao
    data = request.json or {}

    cnpj = data.get('cnpj')
    if not validar_cnpj(cnpj):
        return jsonify({'error': 'CNPJ inválido'}), 400
    cnpj_normalizado = normalizar_cnpj(cnpj)

    new_assoc = Associacao(
        nome=data.get('nome'),
        slug=data.get('slug') or (data.get('nome', '').lower().replace(' ', '-') if data.get('nome') else None),
        cnpj=cnpj_normalizado,
        email=data.get('email'),
        endereco=data.get('endereco'),
        telefone=data.get('telefone'),
    )
    db.session.add(new_assoc)
    try:
        db.session.commit()

        # Víncula o criador como admin da clínica
        user_id = int(get_jwt_identity())
        link = UsuarioAssociacao(
            profissional_id=user_id,
            associacao_id=new_assoc.id,
            role='admin',
            status='active',
        )
        db.session.add(link)
        db.session.commit()

        # Audit LGPD
        try:
            from models_extra import create_audit_entry
            create_audit_entry(
                tenant_id=new_assoc.id,
                user_id=user_id,
                action='clinica.created',
                resource_type='associacao',
                resource_id=new_assoc.id,
                details={'nome': new_assoc.nome, 'cnpj': new_assoc.cnpj},
            )
        except Exception:
            pass

        return jsonify(new_assoc.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# --- READ single ---
@association_bp.route('/associations/<int:assoc_id>', methods=['GET'])
@jwt_required()
@require_clinica_management
def get_association(assoc_id):
    assoc = Associacao.query.get_or_404(assoc_id)
    return jsonify(assoc.to_dict())


# --- UPDATE ---
@association_bp.route('/associations/<int:assoc_id>', methods=['PUT'])
@jwt_required()
@require_clinica_management
def update_association(assoc_id):
    """Atualiza dados da clínica. Requer ser admin da clínica."""
    user_id = int(get_jwt_identity())

    if not _is_clinica_admin(user_id, assoc_id):
        return jsonify({
            'error': 'Você não é administrador desta clínica.',
            'plan_required': None,
        }), 403

    assoc = Associacao.query.get_or_404(assoc_id)
    data = request.json or {}

    # Campos permitidos
    if 'nome' in data:
        assoc.nome = data['nome']
    if 'slug' in data:
        assoc.slug = data['slug']
    if 'cnpj' in data and data['cnpj']:
        if not validar_cnpj(data['cnpj']):
            return jsonify({'error': 'CNPJ inválido'}), 400
        assoc.cnpj = normalizar_cnpj(data['cnpj'])
    if 'endereco' in data:
        assoc.endereco = data['endereco']
    if 'telefone' in data:
        assoc.telefone = data['telefone']
    if 'email' in data:
        assoc.email = data['email']
    if 'ativo' in data:
        assoc.ativo = bool(data['ativo'])

    try:
        db.session.commit()

        try:
            from models_extra import create_audit_entry
            create_audit_entry(
                tenant_id=assoc.id,
                user_id=user_id,
                action='clinica.updated',
                resource_type='associacao',
                resource_id=assoc.id,
                details={'changed_fields': list(data.keys())},
            )
        except Exception:
            pass

        return jsonify(assoc.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# --- DELETE (soft) ---
@association_bp.route('/associations/<int:assoc_id>', methods=['DELETE'])
@jwt_required()
@require_clinica_management
def delete_association(assoc_id):
    """Soft delete: seta ativo=False. Requer ser admin da clínica."""
    user_id = int(get_jwt_identity())

    if not _is_clinica_admin(user_id, assoc_id):
        return jsonify({
            'error': 'Você não é administrador desta clínica.',
        }), 403

    assoc = Associacao.query.get_or_404(assoc_id)
    assoc.ativo = False

    try:
        db.session.commit()

        try:
            from models_extra import create_audit_entry
            create_audit_entry(
                tenant_id=assoc.id,
                user_id=user_id,
                action='clinica.desativada',
                resource_type='associacao',
                resource_id=assoc.id,
                details={'nome': assoc.nome, 'soft_delete': True},
            )
        except Exception:
            pass

        return jsonify({'deleted': True, 'id': assoc.id, 'ativo': False}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ================================================================
# Member Management
# ================================================================
@association_bp.route('/associations/<int:assoc_id>/members', methods=['POST'])
@jwt_required()
@require_clinica_management
def add_member(assoc_id):
    data = request.json
    cpf = data.get('cpf')

    if not validar_cpf(cpf):
        return jsonify({'error': 'CPF inválido'}), 400

    cpf_normalizado = normalizar_cpf(cpf)

    existing = Membro.query.filter_by(associacao_id=assoc_id, cpf=cpf_normalizado).first()
    if existing:
        return jsonify({'error': 'Member with this CPF already exists in this association'}), 400

    patient = IntegrationService.find_patient_by_cpf(cpf_normalizado)
    if not patient:
         return jsonify({'error': 'Paciente não encontrado com este CPF. O membro deve ser um paciente cadastrado.'}), 400

    data_nascimento = None
    if data.get('data_nascimento'):
        try:
            from datetime import datetime as _dt
            data_nascimento = _dt.strptime(data.get('data_nascimento'), '%Y-%m-%d').date()
        except ValueError:
            pass

    patient_nome = getattr(patient, 'nome', None) or data.get('nome')
    if not patient_nome:
        return jsonify({'error': 'Nome do paciente não encontrado. Por favor, forneça o nome.'}), 400

    new_member = Membro(
        associacao_id=assoc_id,
        nome=patient_nome,
        cpf=cpf_normalizado,
        data_nascimento=data_nascimento or getattr(patient, 'data_nascimento', None),
        endereco=data.get('endereco') or getattr(patient, 'endereco', None),
        telefone=data.get('telefone') or getattr(patient, 'telefone', None),
        email=data.get('email') or getattr(patient, 'email', None),
        rg=data.get('rg'),
        nome_responsavel=data.get('nome_responsavel'),
        observacoes=data.get('observacoes'),
        status='ativo',
        paciente_id=patient.id
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
@require_clinica_management
def list_members(assoc_id):
    members = Membro.query.filter_by(associacao_id=assoc_id).all()
    return jsonify([m.to_dict() for m in members])


# ================================================================
# Stock Management
# ================================================================
@association_bp.route('/associations/<int:assoc_id>/stock', methods=['POST'])
@jwt_required()
@require_clinica_management
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
@require_clinica_management
def get_stock(assoc_id):
    stock = Estoque.query.filter_by(associacao_id=assoc_id).all()
    return jsonify([s.to_dict() for s in stock])


# ================================================================
# Dispensation
# ================================================================
@association_bp.route('/associations/<int:assoc_id>/dispense', methods=['POST'])
@jwt_required()
@require_clinica_management
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