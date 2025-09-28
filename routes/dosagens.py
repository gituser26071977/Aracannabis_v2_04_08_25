from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Dosagem, Paciente, LogAtividade
from datetime import datetime, timedelta

dosagens_bp = Blueprint('dosagens', __name__)

@dosagens_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_dosagens(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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
        
        # Criar nova dosagem com os novos campos
        nova_dosagem = Dosagem(
            paciente_id=paciente_id,
            data=data_dosagem,
            dosagem=data['dosagem'],
            gotas=data.get('gotas', 0),
            frequencia_diaria=data.get('frequencia_diaria', 1),
            concentracao_cbd=data.get('concentracao_cbd', 0.0),
            concentracao_thc=data.get('concentracao_thc', 0.0),
            concentracao_cbg=data.get('concentracao_cbg', 0.0),
            concentracao_cbn=data.get('concentracao_cbn', 0.0),
            gotas_por_ml=data.get('gotas_por_ml', 30)  # Padrão 30 gotas/ml
        )
        
        db.session.add(nova_dosagem)
        
        # Atualizar a dosagem atual do paciente e marcar como em tratamento
        paciente.dosagem = data['dosagem']
        paciente.updated_at = datetime.utcnow()
        paciente.em_tratamento = True
        
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
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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
    
    periodo = request.args.get('periodo', 'integral')
    data_fim_param = request.args.get('data_fim') # Manter data_fim opcional

    hoje = datetime.now().date()
    data_inicio_calculada = None

    if periodo == '1m':
        data_inicio_calculada = hoje - timedelta(days=30)
    elif periodo == '3m':
        data_inicio_calculada = hoje - timedelta(days=90)
    elif periodo == '6m':
        data_inicio_calculada = hoje - timedelta(days=180)
    elif periodo == '1y':
        data_inicio_calculada = hoje - timedelta(days=365)
    # Se 'integral', data_inicio_calculada permanece None, sem filtro de data de início.

    query = Dosagem.query.filter_by(paciente_id=paciente_id)

    if data_inicio_calculada:
        query = query.filter(Dosagem.data >= data_inicio_calculada)

    if data_fim_param:
        try:
            data_fim_obj = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
            query = query.filter(Dosagem.data <= data_fim_obj)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Ordenar por data
    dosagens = query.order_by(Dosagem.data).all()
    
    # Preparar dados para o gráfico
    dados_grafico = []
    dados_cbd = []
    dados_thc = []
    dados_cbg = []
    dados_cbn = []
    dados_canabinoides_totais = []
    
    for dosagem in dosagens:
        # Calcular dose diária
        dose_diaria = dosagem.calcular_dose_diaria()
        
        # Dados para o gráfico principal (gotas)
        dados_grafico.append({
            'x': dosagem.data.isoformat(),
            'y': dosagem.gotas,
            'dosagem_texto': f"{dosagem.gotas} gotas, {dosagem.frequencia_diaria}x ao dia"
        })
        
        # Dados para gráficos de canabinoides
        dados_cbd.append({
            'x': dosagem.data.isoformat(),
            'y': dose_diaria['cbd_mg'],
            'dosagem_texto': f"CBD: {dose_diaria['cbd_mg']} mg/dia"
        })
        
        dados_thc.append({
            'x': dosagem.data.isoformat(),
            'y': dose_diaria['thc_mg'],
            'dosagem_texto': f"THC: {dose_diaria['thc_mg']} mg/dia"
        })
        
        dados_cbg.append({
            'x': dosagem.data.isoformat(),
            'y': dose_diaria['cbg_mg'],
            'dosagem_texto': f"CBG: {dose_diaria['cbg_mg']} mg/dia"
        })
        
        dados_cbn.append({
            'x': dosagem.data.isoformat(),
            'y': dose_diaria['cbn_mg'],
            'dosagem_texto': f"CBN: {dose_diaria['cbn_mg']} mg/dia"
        })
        
        dados_canabinoides_totais.append({
            'x': dosagem.data.isoformat(),
            'y': dose_diaria['canabinoides_totais'],
            'dosagem_texto': f"Total: {dose_diaria['canabinoides_totais']} mg/dia"
        })
    
    return jsonify({
        'dados_grafico': dados_grafico,
        'dados_canabinoides': {
            'cbd': dados_cbd,
            'thc': dados_thc,
            'cbg': dados_cbg,
            'cbn': dados_cbn,
            'total': dados_canabinoides_totais
        }
    }), 200

# Add this new endpoint for the dosage chart
@dosagens_bp.route('/dosagens/grafico/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def get_dosage_chart_data(paciente_id):
    """Endpoint para obter dados do gráfico de dosagens"""
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Obter parâmetros da URL
    periodo = request.args.get('periodo', 'integral')
    
    # Calcular datas com base no período
    hoje = datetime.utcnow().date()
    if periodo == '1m':
        start_date = hoje - timedelta(days=30)
    elif periodo == '3m':
        start_date = hoje - timedelta(days=90)
    elif periodo == '6m':
        start_date = hoje - timedelta(days=180)
    elif periodo == '1y':
        start_date = hoje - timedelta(days=365)
    else:  # 'integral'
        start_date = None
    
    # Construir a query
    query = Dosagem.query.filter_by(paciente_id=paciente_id)
    if start_date:
        query = query.filter(Dosagem.data >= start_date)
    
    # Ordenar por data
    dosagens = query.order_by(Dosagem.data.asc()).all()
    
    # Preparar dados para o gráfico
    dados_grafico = []
    
    for dosagem in dosagens:
        dose_diaria = dosagem.calcular_dose_diaria()
        dados_grafico.append({
            'x': dosagem.data.strftime('%Y-%m-%d'),
            'y': dose_diaria['cbd_mg'],
            'dosagem_texto': f"Dosagem: {dosagem.dosagem}, {dosagem.gotas} gotas, {dosagem.frequencia_diaria}x/dia"
        })
    
    return jsonify({
        'dados_grafico': dados_grafico
    }), 200
