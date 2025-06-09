from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, LogAtividade
from datetime import datetime

lgpd_bp = Blueprint('lgpd', __name__)

@lgpd_bp.route('/consentimento/<int:paciente_id>', methods=['GET'])
@jwt_required()
def obter_consentimento(paciente_id):
    """Endpoint para obter o status de consentimento LGPD de um paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Consulta de status de consentimento LGPD do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'paciente_id': paciente_id,
        'consentimento_lgpd': paciente.consentimento_lgpd,
        'data_consentimento': paciente.data_consentimento.isoformat() if paciente.data_consentimento else None
    }), 200

@lgpd_bp.route('/consentimento/<int:paciente_id>', methods=['POST'])
@jwt_required()
def registrar_consentimento(paciente_id):
    """Endpoint para registrar o consentimento LGPD de um paciente"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'consentimento' not in data:
        return jsonify({'error': 'Status de consentimento é obrigatório'}), 400
    
    try:
        # Atualizar status de consentimento
        paciente.consentimento_lgpd = data['consentimento']
        
        # Se consentimento for True, registrar data atual
        if data['consentimento']:
            paciente.data_consentimento = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Atualização',
            detalhes=f'Atualização de consentimento LGPD do paciente ID {paciente_id}: {"Concedido" if data["consentimento"] else "Revogado"}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Consentimento LGPD atualizado com sucesso',
            'consentimento_lgpd': paciente.consentimento_lgpd,
            'data_consentimento': paciente.data_consentimento.isoformat() if paciente.data_consentimento else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar consentimento LGPD: {str(e)}'}), 500

@lgpd_bp.route('/politica-privacidade', methods=['GET'])
def obter_politica_privacidade():
    """Endpoint para obter a política de privacidade"""
    return jsonify({
        'titulo': 'Política de Privacidade - Aracannabis',
        'ultima_atualizacao': '2025-05-21',
        'versao': '1.0',
        'url': '/politica-privacidade'
    }), 200

@lgpd_bp.route('/direitos-titular/<int:paciente_id>', methods=['POST'])
@jwt_required()
def solicitar_direitos_titular(paciente_id):
    """Endpoint para solicitar exercício de direitos do titular"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if not all(k in data for k in ('tipo_solicitacao', 'detalhes')):
        return jsonify({'error': 'Tipo de solicitação e detalhes são obrigatórios'}), 400
    
    # Validar tipo de solicitação
    tipos_validos = ['acesso', 'correcao', 'exclusao', 'revogacao', 'outros']
    if data['tipo_solicitacao'] not in tipos_validos:
        return jsonify({'error': f'Tipo de solicitação inválido. Valores aceitos: {", ".join(tipos_validos)}'}), 400
    
    try:
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Solicitação LGPD',
            detalhes=f'Solicitação de {data["tipo_solicitacao"]} para paciente ID {paciente_id}: {data["detalhes"]}'
        )
        db.session.add(log)
        db.session.commit()
        
        # Aqui seria implementada a lógica para processar a solicitação
        # Por exemplo, enviar e-mail para o DPO, criar ticket em sistema de suporte, etc.
        
        return jsonify({
            'message': 'Solicitação registrada com sucesso',
            'numero_protocolo': f'LGPD-{datetime.utcnow().strftime("%Y%m%d")}-{paciente_id}-{log.id}',
            'status': 'em_analise'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar solicitação: {str(e)}'}), 500
