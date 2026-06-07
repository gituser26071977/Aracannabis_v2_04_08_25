from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Dosagem, Paciente, LogAtividade
from datetime import datetime

dosagens_bp = Blueprint('dosagens', __name__)

@dosagens_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_dosagens(paciente_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Dosagem.query.filter_by(paciente_id=paciente_id)
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(Dosagem.data >= data_inicio)
        except ValueError:
            return jsonify({'error': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(Dosagem.data <= data_fim)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Ordenar por data decrescente
    dosagens = query.order_by(Dosagem.data.desc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Listagem de dosagens do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'dosagens': [d.to_dict() for d in dosagens]
    }), 200

@dosagens_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def registrar_dosagem(paciente_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if not all(k in data for k in ('data', 'dosagem')):
        return jsonify({'error': 'Data e dosagem são obrigatórios'}), 400
    
    try:
        # Converter string de data para objeto date
        data_dosagem = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        # Criar nova dosagem
        nova_dosagem = Dosagem(
            paciente_id=paciente_id,
            data=data_dosagem,
            dosagem=data['dosagem']
        )
        
        db.session.add(nova_dosagem)
        
        # Atualizar a dosagem atual do paciente
        paciente.dosagem = data['dosagem']
        paciente.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Registro',
            detalhes=f'Nova dosagem registrada para paciente ID {paciente_id}: {data["dosagem"]}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Dosagem registrada com sucesso',
            'dosagem': nova_dosagem.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar dosagem: {str(e)}'}), 500

@dosagens_bp.route('/<int:dosagem_id>', methods=['DELETE'])
@jwt_required()
def excluir_dosagem(dosagem_id):
    current_user = get_jwt_identity()
    profissional_id = current_user.get('id')
    
    dosagem = Dosagem.query.get(dosagem_id)
    
    if not dosagem:
        return jsonify({'error': 'Dosagem não encontrada'}), 404
    
    try:
        paciente_id = dosagem.paciente_id
        dosagem_valor = dosagem.dosagem
        
        db.session.delete(dosagem)
        
        # Registrar atividade antes de confirmar a exclusão
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Exclusão',
            detalhes=f'Dosagem excluída: {dosagem_valor} (ID {dosagem_id}) do paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Dosagem excluída com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir dosagem: {str(e)}'}), 500

@dosagens_bp.route('/grafico/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def dados_grafico_dosagens(paciente_id):
    """Endpoint para obter dados para gráfico de evolução de dosagens"""
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Dosagem.query.filter_by(paciente_id=paciente_id)
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(Dosagem.data >= data_inicio)
        except ValueError:
            return jsonify({'error': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(Dosagem.data <= data_fim)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Ordenar por data
    dosagens = query.order_by(Dosagem.data).all()
    
    # Extrair valores numéricos das dosagens para o gráfico
    import re
    
    dados_grafico = []
    
    for dosagem in dosagens:
        # Tentar extrair valor numérico da dosagem (ex: "10 gotas" -> 10)
        valor_numerico = None
        match = re.search(r'(\d+(\.\d+)?)', dosagem.dosagem)
        if match:
            valor_numerico = float(match.group(1))
        
        dados_grafico.append({
            'x': dosagem.data.isoformat(),
            'y': valor_numerico,
            'dosagem_texto': dosagem.dosagem
        })
    
    return jsonify({
        'dados_grafico': {
            'label': 'Dosagem',
            'data': dados_grafico
        }
    }), 200
