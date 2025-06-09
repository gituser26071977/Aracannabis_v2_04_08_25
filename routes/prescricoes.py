from flask import Blueprint, jsonify, request
from models import db, Prescricao, Consulta
from datetime import datetime

prescricoes_bp = Blueprint('prescricoes', __name__)

@prescricoes_bp.route('/prescricao/<int:consulta_id>', methods=['GET'])
def get_prescricao(consulta_id):
    """
    Obtém dados para prescrição médica baseada em uma consulta
    Retorna dados formatados para impressão
    """
    consulta = Consulta.query.get(consulta_id)
    if not consulta:
        return jsonify({'error': 'Consulta não encontrada'}), 404

    prescricao = Prescricao.query.filter_by(consulta_id=consulta_id).first()
    
    return jsonify({
        'id': prescricao.id if prescricao else consulta_id,
        'paciente': consulta.paciente.to_dict(),
        'profissional': consulta.profissional.to_dict(),
        'data_consulta': consulta.data_consulta.isoformat(),
        'composicao': prescricao.composicao if prescricao else [],
        'observacoes': prescricao.observacoes if prescricao else ''
    })

@prescricoes_bp.route('/prescricao', methods=['POST'])
def criar_prescricao():
    """Cria/atualiza uma prescrição médica"""
    data = request.json
    consulta_id = data.get('consulta_id')
    
    if not consulta_id:
        return jsonify({'error': 'ID da consulta é obrigatório'}), 400
        
    prescricao = Prescricao.query.filter_by(consulta_id=consulta_id).first()
    
    if not prescricao:
        prescricao = Prescricao(
            consulta_id=consulta_id,
            composicao=data.get('composicao', []),
            observacoes=data.get('observacoes', '')
        )
        db.session.add(prescricao)
    else:
        prescricao.composicao = data.get('composicao', prescricao.composicao)
        prescricao.observacoes = data.get('observacoes', prescricao.observacoes)
    
    db.session.commit()
    return jsonify({'message': 'Prescrição salva com sucesso', 'id': prescricao.id}), 200
