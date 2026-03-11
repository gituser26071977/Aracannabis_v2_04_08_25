"""
Rotas do Portal do Paciente

APIs para pacientes autenticados visualizarem seus próprios dados
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import db, Paciente, Consulta, Prescricao, Exame, Evolucao
from datetime import datetime
from sqlalchemy import desc

patient_portal_bp = Blueprint('patient_portal', __name__)

def require_patient():
    """Helper para verificar se é um paciente autenticado"""
    claims = get_jwt()
    if claims.get('user_type') != 'patient':
        return jsonify({'error': 'Acesso restrito a pacientes'}), 403
    return None

@patient_portal_bp.route('/me', methods=['GET'])
@jwt_required()
def get_patient_profile():
    """Retorna dados do paciente logado"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    return jsonify(paciente.to_dict()), 200


@patient_portal_bp.route('/me/prontuario', methods=['GET'])
@jwt_required()
def get_my_medical_records():
    """Retorna prontuário completo do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # TODO: Verificar se existe tabela de prontuários específica
    # Por enquanto, retornar dados do paciente + histórico de consultas
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Buscar consultas para montar histórico
    consultas = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data)).all()
    
    return jsonify({
        'paciente': paciente.to_dict(),
        'historico_consultas': [c.to_dict() for c in consultas],
        'total_consultas': len(consultas)
    }), 200


@patient_portal_bp.route('/me/consultas', methods=['GET'])
@jwt_required()
def get_my_consultations():
    """Histórico de consultas do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # Parâmetros opcionais de filtro
    limit = request.args.get('limit', type=int, default=50)
    offset = request.args.get('offset', type=int, default=0)
    
    consultas_query = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data))
    
    total = consultas_query.count()
    consultas = consultas_query.limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'consultas': [c.to_dict() for c in consultas]
    }), 200


@patient_portal_bp.route('/me/prescricoes', methods=['GET'])
@jwt_required()
def get_my_prescriptions():
    """Prescrições do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # Filtro: apenas ativas ou todas
    apenas_ativas = request.args.get('ativas', type=bool, default=False)
    
    query = Prescricao.query.filter_by(paciente_id=paciente_id)
    
    if apenas_ativas:
        query = query.filter_by(ativo=True)
    
    prescricoes = query.order_by(desc(Prescricao.data_criacao)).all()
    
    return jsonify({
        'total': len(prescricoes),
        'prescricoes': [p.to_dict() for p in prescricoes]
    }), 200


@patient_portal_bp.route('/me/exames', methods=['GET'])
@jwt_required()
def get_my_exams():
    """Exames realizados pelo paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    exames = Exame.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Exame.data)).all()
    
    return jsonify({
        'total': len(exames),
        'exames': [e.to_dict() for e in exames]
    }), 200


@patient_portal_bp.route('/me/evolucoes', methods=['GET'])
@jwt_required()
def get_my_evolutions():
    """Evoluções médicas do paciente"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    evolucoes = Evolucao.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Evolucao.data)).all()
    
    return jsonify({
        'total': len(evolucoes),
        'evolucoes': [e.to_dict() for e in evolucoes]
    }), 200


@patient_portal_bp.route('/me/perfil', methods=['PUT'])
@jwt_required()
def update_patient_profile():
    """Atualiza dados do perfil do paciente (limitado)"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Campos que o paciente pode atualizar
    allowed_fields = ['telefone', 'endereco']
    
    for field in allowed_fields:
        if field in data:
            setattr(paciente, field, data[field])
    
    paciente.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'paciente': paciente.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar perfil: {str(e)}'}), 500


@patient_portal_bp.route('/me/stats', methods=['GET'])
@jwt_required()
def get_my_stats():
    """Estatísticas do paciente (dashboard)"""
    error = require_patient()
    if error: return error
    
    paciente_id = get_jwt_identity()
    
    # Contar registros
    total_consultas = Consulta.query.filter_by(paciente_id=paciente_id).count()
    total_prescricoes = Prescricao.query.filter_by(paciente_id=paciente_id).count()
    prescricoes_ativas = Prescricao.query.filter_by(
        paciente_id=paciente_id, 
        ativo=True
    ).count()
    total_exames = Exame.query.filter_by(paciente_id=paciente_id).count()
    
    # Última consulta
    ultima_consulta = Consulta.query.filter_by(
        paciente_id=paciente_id
    ).order_by(desc(Consulta.data)).first()
    
    # Próxima consulta (futura)
    proxima_consulta = Consulta.query.filter(
        Consulta.paciente_id == paciente_id,
        Consulta.data > datetime.utcnow()
    ).order_by(Consulta.data).first()
    
    return jsonify({
        'total_consultas': total_consultas,
        'total_prescricoes': total_prescricoes,
        'prescricoes_ativas': prescricoes_ativas,
        'total_exames': total_exames,
        'ultima_consulta': ultima_consulta.to_dict() if ultima_consulta else None,
        'proxima_consulta': proxima_consulta.to_dict() if proxima_consulta else None
    }), 200


@patient_portal_bp.route('/me/alterar-senha', methods=['POST'])
@jwt_required()
def change_password():
    """Permite paciente alterar sua própria senha"""
    error = require_patient()
    if error: return error
    
    from werkzeug.security import generate_password_hash, check_password_hash
    
    paciente_id = get_jwt_identity()
    paciente = Paciente.query.get(paciente_id)
    
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    senha_atual = data.get('senha_atual')
    senha_nova = data.get('senha_nova')
    
    if not senha_atual or not senha_nova:
        return jsonify({'error': 'Senha atual e nova são obrigatórias'}), 400
    
    # Verificar senha atual
    if not check_password_hash(paciente.senha_hash, senha_atual):
        return jsonify({'error': 'Senha atual incorreta'}), 401
    
    # Validar nova senha
    if len(senha_nova) < 6:
        return jsonify({'error': 'Nova senha deve ter no mínimo 6 caracteres'}), 400
    
    # Atualizar senha
    paciente.senha_hash = generate_password_hash(senha_nova)
    
    try:
        db.session.commit()
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 500
