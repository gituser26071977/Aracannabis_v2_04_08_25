from flask import request, jsonify
from models import db
from association import association_bp
from association.models import Associacao, Membro, Estoque
from association.services.integration_service import IntegrationService
from association.services.dispensation_service import DispensationService
from association.validators import validar_cpf, validar_cnpj, normalizar_cpf, normalizar_cnpj
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity

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
def list_associations():
    try:
        assocs = Associacao.query.filter_by(ativo=True).all()
        return jsonify({
            'success': True,
            'associacoes': [a.to_dict() for a in assocs]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
