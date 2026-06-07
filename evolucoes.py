from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Evolucao, Paciente, Profissional, LogAtividade

evolucoes_bp = Blueprint('evolucoes', __name__)

@evolucoes_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_evolucoes(paciente_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Ordenar por data decrescente
    evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id).order_by(Evolucao.data_evolucao.desc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Listagem de evoluções do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    # Preparar dados com nome do profissional
    evolucoes_data = []
    for evolucao in evolucoes:
        evolucao_dict = evolucao.to_dict()
        evolucoes_data.append(evolucao_dict)
    
    return jsonify({
        'evolucoes': evolucoes_data
    }), 200

@evolucoes_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def registrar_evolucao(paciente_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'nota_evolucao' not in data or not data['nota_evolucao'].strip():
        return jsonify({'error': 'Nota de evolução é obrigatória'}), 400
    
    try:
        # Criar nova evolução
        nova_evolucao = Evolucao(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            nota_evolucao=data['nota_evolucao'].strip()
        )
        
        db.session.add(nova_evolucao)
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Registro',
            detalhes=f'Nova evolução registrada para paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Evolução registrada com sucesso',
            'evolucao': nova_evolucao.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar evolução: {str(e)}'}), 500

@evolucoes_bp.route('/<int:evolucao_id>', methods=['GET'])
@jwt_required()
def obter_evolucao(evolucao_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    evolucao = Evolucao.query.get(evolucao_id)
    
    if not evolucao:
        return jsonify({'error': 'Evolução não encontrada'}), 404
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Visualização da evolução ID {evolucao_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'evolucao': evolucao.to_dict()
    }), 200

@evolucoes_bp.route('/<int:evolucao_id>', methods=['PUT'])
@jwt_required()
def atualizar_evolucao(evolucao_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    evolucao = Evolucao.query.get(evolucao_id)
    
    if not evolucao:
        return jsonify({'error': 'Evolução não encontrada'}), 404
    
    # Verificar se o profissional é o autor da evolução
    if evolucao.profissional_id != profissional_id:
        return jsonify({'error': 'Você não tem permissão para editar esta evolução'}), 403
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'nota_evolucao' not in data or not data['nota_evolucao'].strip():
        return jsonify({'error': 'Nota de evolução é obrigatória'}), 400
    
    try:
        # Atualizar evolução
        evolucao.nota_evolucao = data['nota_evolucao'].strip()
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Atualização',
            detalhes=f'Evolução atualizada: ID {evolucao_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Evolução atualizada com sucesso',
            'evolucao': evolucao.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar evolução: {str(e)}'}), 500

@evolucoes_bp.route('/<int:evolucao_id>', methods=['DELETE'])
@jwt_required()
def excluir_evolucao(evolucao_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    evolucao = Evolucao.query.get(evolucao_id)
    
    if not evolucao:
        return jsonify({'error': 'Evolução não encontrada'}), 404
    
    # Verificar se o profissional é o autor da evolução
    if evolucao.profissional_id != profissional_id:
        return jsonify({'error': 'Você não tem permissão para excluir esta evolução'}), 403
    
    try:
        paciente_id = evolucao.paciente_id
        
        db.session.delete(evolucao)
        
        # Registrar atividade antes de confirmar a exclusão
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Exclusão',
            detalhes=f'Evolução excluída: ID {evolucao_id} do paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Evolução excluída com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir evolução: {str(e)}'}), 500

@evolucoes_bp.route('/logs', methods=['GET'])
@jwt_required()
def listar_logs():
    """Endpoint para listar logs de atividades (para administradores)"""
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    # Verificar se o profissional existe
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return jsonify({'error': 'Profissional não encontrado'}), 404
    
    # Parâmetros de filtro
    limite = request.args.get('limite', 50, type=int)
    
    # Limitar a quantidade de logs retornados
    logs = LogAtividade.query.order_by(LogAtividade.data_hora.desc()).limit(limite).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    }), 200
