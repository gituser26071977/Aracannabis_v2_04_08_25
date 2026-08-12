from flask import g, Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Sintoma, Paciente, LogAtividade, SnapIVTeste, PHQ9Teste, GAD7Teste
from datetime import datetime, timedelta
from collections import defaultdict

sintomas_bp = Blueprint('sintomas', __name__)

def _assoc_id():
    """Resolve o associacao_id atual (tenant) via middleware (P0-12)."""
    from flask import g
    assoc = getattr(g, "current_association", None)
    return getattr(assoc, "id", None)



@sintomas_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_sintomas(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Parâmetros de filtro
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    sintoma_filtro = request.args.get('sintoma')
    
    query = Sintoma.query.filter_by(paciente_id=paciente_id)
    
    # Aplicar filtros se fornecidos
    if data_inicio:
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(Sintoma.data >= data_inicio)
        except ValueError:
            return jsonify({'error': 'Formato de data_inicio inválido. Use YYYY-MM-DD'}), 400
    
    if data_fim:
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(Sintoma.data <= data_fim)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    if sintoma_filtro:
        query = query.filter(Sintoma.sintoma.ilike(f'%{sintoma_filtro}%'))
    
    # Ordenar por data e sintoma
    sintomas = query.order_by(Sintoma.data.desc(), Sintoma.sintoma).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        associacao_id=_assoc_id(),
        acao='Consulta',
        detalhes=f'Listagem de sintomas do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'sintomas': [s.to_dict() for s in sintomas]
    }), 200

@sintomas_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def registrar_sintoma(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if not all(k in data for k in ('data', 'sintoma', 'intensidade')):
        return jsonify({'error': 'Data, sintoma e intensidade são obrigatórios'}), 400
    
    try:
        # Converter string de data para objeto date
        data_sintoma = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        # Validar intensidade (0-10)
        intensidade = int(data['intensidade'])
        if intensidade < 0 or intensidade > 10:
            return jsonify({'error': 'Intensidade deve estar entre 0 e 10'}), 400
        
        # Verificar se já existe um registro para este sintoma nesta data
        sintoma_existente = Sintoma.query.filter_by(
            paciente_id=paciente_id,
            data=data_sintoma,
            sintoma=data['sintoma']
        ).first()
        
        if sintoma_existente:
            # Atualizar o existente
            sintoma_existente.intensidade = intensidade
            db.session.commit()
            
            # Registrar atividade
            log = LogAtividade(
                profissional_id=profissional_id,
                associacao_id=_assoc_id(),
                acao='Atualização',
                detalhes=f'Sintoma atualizado: {data["sintoma"]} para paciente ID {paciente_id}'
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'message': 'Sintoma atualizado com sucesso',
                'sintoma': sintoma_existente.to_dict()
            }), 200
        else:
            # Criar novo registro
            novo_sintoma = Sintoma(
                paciente_id=paciente_id,
                data=data_sintoma,
                sintoma=data['sintoma'],
                intensidade=intensidade
            )
            
            db.session.add(novo_sintoma)
            db.session.commit()
            
            # Registrar atividade
            log = LogAtividade(
                profissional_id=profissional_id,
                associacao_id=_assoc_id(),
                acao='Registro',
                detalhes=f'Novo sintoma registrado: {data["sintoma"]} para paciente ID {paciente_id}'
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'message': 'Sintoma registrado com sucesso',
                'sintoma': novo_sintoma.to_dict()
            }), 201
        
    except ValueError:
        return jsonify({'error': 'Formato de data inválido ou intensidade não é um número'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar sintoma: {str(e)}'}), 500

@sintomas_bp.route('/<int:sintoma_id>', methods=['DELETE'])
@jwt_required()
def excluir_sintoma(sintoma_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    sintoma = Sintoma.query.get(sintoma_id)
    
    if not sintoma:
        return jsonify({'error': 'Sintoma não encontrado'}), 404
    
    try:
        paciente_id = sintoma.paciente_id
        sintoma_nome = sintoma.sintoma
        
        db.session.delete(sintoma)
        
        # Registrar atividade antes de confirmar a exclusão
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Exclusão',
            detalhes=f'Sintoma excluído: {sintoma_nome} (ID {sintoma_id}) do paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Sintoma excluído com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir sintoma: {str(e)}'}), 500

@sintomas_bp.route('/sintomas-padrao', methods=['GET'])
@jwt_required()
def listar_sintomas_padrao():
    """Endpoint para obter a lista de sintomas padrão e personalizados"""
    
    sintomas_padrao = [
        'Dor', 
        'Ansiedade', 
        'Insônia',
        'Depressão'
    ]
    
    try:
        # Obter sintomas personalizados da tabela dedicada
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT nome FROM sintomas_personalizados 
            ORDER BY nome
        """))
        sintomas_personalizados = [row[0] for row in result.fetchall()]
        
        # Combinar sintomas padrão e personalizados em uma única lista
        todos_sintomas = sintomas_padrao + sintomas_personalizados
        
        return jsonify({
            'sintomas_padrao': todos_sintomas,  # Agora inclui personalizados
            'sintomas_personalizados': sintomas_personalizados  # Mantém separado para compatibilidade
        }), 200
    except Exception as e:
        print(f"Erro ao obter sintomas personalizados: {str(e)}")
        return jsonify({
            'sintomas_padrao': sintomas_padrao,
            'sintomas_personalizados': []
        }), 200

@sintomas_bp.route('/sintoma-personalizado', methods=['POST'])
@jwt_required()
def registrar_sintoma_personalizado():
    """Endpoint para registrar um novo sintoma personalizado"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'nome_sintoma' not in data or not data['nome_sintoma'].strip():
        return jsonify({'error': 'Nome do sintoma é obrigatório'}), 400
    if 'paciente_id' not in data:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400
    
    nome_sintoma = data['nome_sintoma'].strip()
    paciente_id = data['paciente_id']
    
    # Verificar se o sintoma já existe na lista padrão
    sintomas_padrao = [
        'Dor', 
        'Ansiedade', 
        'Insônia',
        'Depressão'
    ]
    
    if nome_sintoma in sintomas_padrao:
        return jsonify({'error': 'Este sintoma já existe na lista padrão'}), 400
    
    try:
        # Verificar se já existe na tabela de personalizados para este paciente
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT id FROM sintomas_personalizados 
            WHERE nome = :nome AND paciente_id = :paciente_id
        """), {'nome': nome_sintoma, 'paciente_id': paciente_id})
        
        if result.fetchone():
            return jsonify({'error': 'Este sintoma já existe para este paciente'}), 400
        
        # Inserir na tabela de sintomas personalizados
        db.session.execute(text("""
            INSERT INTO sintomas_personalizados (nome, paciente_id) 
            VALUES (:nome, :paciente_id)
        """), {
            'nome': nome_sintoma,
            'paciente_id': paciente_id
        })
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Registro',
            detalhes=f'Novo sintoma personalizado registrado: {nome_sintoma}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Sintoma personalizado registrado com sucesso',
            'sintoma': nome_sintoma
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao registrar sintoma personalizado: {str(e)}'}), 500

@sintomas_bp.route('/sintoma-personalizado/<int:sintoma_id>', methods=['DELETE'])
@jwt_required()
def remover_sintoma_personalizado(sintoma_id):
    """Endpoint para remover um sintoma personalizado"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    try:
        from sqlalchemy import text
        
        # Verificar se o sintoma existe
        result = db.session.execute(text("""
            SELECT nome FROM sintomas_personalizados 
            WHERE id = :id
        """), {'id': sintoma_id})
        
        sintoma_row = result.fetchone()
        if not sintoma_row:
            return jsonify({'error': 'Sintoma personalizado não encontrado'}), 404
        
        nome_sintoma = sintoma_row[0]
        
        # Verificar se há registros de sintomas usando este sintoma personalizado
        sintomas_em_uso = Sintoma.query.filter_by(sintoma=nome_sintoma).count()
        
        if sintomas_em_uso > 0:
            return jsonify({
                'error': f'Não é possível remover este sintoma pois há {sintomas_em_uso} registro(s) de pacientes usando-o'
            }), 400
        
        # Remover o sintoma personalizado
        db.session.execute(text("""
            DELETE FROM sintomas_personalizados 
            WHERE id = :id
        """), {'id': sintoma_id})
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Exclusão',
            detalhes=f'Sintoma personalizado removido: {nome_sintoma}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Sintoma personalizado removido com sucesso',
            'sintoma': nome_sintoma
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover sintoma personalizado: {str(e)}'}), 500

@sintomas_bp.route('/sintoma-personalizado', methods=['DELETE'])
@jwt_required()
def REDACTED():
    """Endpoint para excluir um sintoma personalizado por nome"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    if not data or 'nome_sintoma' not in data:
        return jsonify({'error': 'Nome do sintoma é obrigatório'}), 400
    
    nome_sintoma = data['nome_sintoma'].strip()
    
    try:
        from sqlalchemy import text
        
        # Buscar ID do sintoma pelo nome
        result = db.session.execute(text("""
            SELECT id FROM sintomas_personalizados 
            WHERE nome = :nome
        """), {'nome': nome_sintoma})
        
        sintoma_row = result.fetchone()
        if not sintoma_row:
            return jsonify({'error': 'Sintoma personalizado não encontrado'}), 404
        
        sintoma_id = sintoma_row[0]
        
        # Verificar se há registros de sintomas usando este sintoma personalizado
        sintomas_em_uso = Sintoma.query.filter_by(sintoma=nome_sintoma).count()
        
        if sintomas_em_uso > 0:
            return jsonify({
                'error': f'Não é possível remover este sintoma pois há {sintomas_em_uso} registro(s) de pacientes usando-o'
            }), 400
        
        # Remover o sintoma personalizado
        db.session.execute(text("""
            DELETE FROM sintomas_personalizados 
            WHERE id = :id
        """), {'id': sintoma_id})
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            associacao_id=_assoc_id(),
            acao='Exclusão',
            detalhes=f'Sintoma personalizado removido: {nome_sintoma}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Sintoma personalizado removido com sucesso',
            'sintoma': nome_sintoma
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover sintoma personalizado: {str(e)}'}), 500

@sintomas_bp.route('/grafico/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def dados_grafico_sintomas(paciente_id):
    """Endpoint para obter dados para gráfico de evolução de sintomas"""
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    periodo = request.args.get('periodo', 'integral')
    data_fim_param = request.args.get('data_fim') # Manter data_fim opcional
    
    hoje = datetime.utcnow().date()
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
    
    query = Sintoma.query.filter_by(paciente_id=paciente_id)
    
    if data_inicio_calculada:
        query = query.filter(Sintoma.data >= data_inicio_calculada)
    
    if data_fim_param:
        try:
            data_fim_obj = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
            query = query.filter(Sintoma.data <= data_fim_obj)
        except ValueError:
            return jsonify({'error': 'Formato de data_fim inválido. Use YYYY-MM-DD'}), 400
    
    # Ordenar por data
    sintomas = query.order_by(Sintoma.data).all()
    
    # Organizar dados para o gráfico
    dados_grafico = {}
    
    for sintoma in sintomas:
        nome_sintoma = sintoma.sintoma
        data_str = sintoma.data.isoformat()
        
        if nome_sintoma not in dados_grafico:
            dados_grafico[nome_sintoma] = {
                'label': nome_sintoma,
                'data': []
            }
        
        dados_grafico[nome_sintoma]['data'].append({
            'x': data_str,
            'y': sintoma.intensidade,
            'original_value': sintoma.intensidade,
            'max_value': 10
        })

    # Adicionar dados do SNAP-IV (TDAH)
    snap_query = SnapIVTeste.query.filter_by(paciente_id=paciente_id)
    if data_inicio_calculada:
        snap_query = snap_query.filter(SnapIVTeste.data_realizacao >= data_inicio_calculada)
    if data_fim_param:
        try:
            data_fim_obj = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
            snap_query = snap_query.filter(SnapIVTeste.data_realizacao <= datetime.combine(data_fim_obj, datetime.max.time()))
        except:
            pass
            
    snap_tests = snap_query.order_by(SnapIVTeste.data_realizacao).all()
    
    if snap_tests:
        # Agregar múltiplos testes do mesmo dia usando média
        from collections import defaultdict
        snap_agg = defaultdict(lambda: {'desatencao': [], 'hiperatividade': []})
        
        for teste in snap_tests:
            data_str = teste.data_realizacao.date().isoformat()
            snap_agg[data_str]['desatencao'].append(teste.pontos_desatencao)
            snap_agg[data_str]['hiperatividade'].append(teste.pontos_hiperatividade)
        
        dados_grafico['TDAH - Desatenção'] = {'label': 'TDAH - Desatenção', 'data': []}
        dados_grafico['TDAH - Hiperatividade'] = {'label': 'TDAH - Hiperatividade', 'data': []}
        
        for data_str in sorted(snap_agg.keys()):
            agg = snap_agg[data_str]
            avg_desatencao = sum(agg['desatencao']) / len(agg['desatencao'])
            avg_hiperatividade = sum(agg['hiperatividade']) / len(agg['hiperatividade'])
            
            y_desatencao = round((avg_desatencao / 27) * 10, 2)
            dados_grafico['TDAH - Desatenção']['data'].append({
                'x': data_str,
                'y': y_desatencao,
                'original_value': round(avg_desatencao, 2),
                'max_value': 27
            })
            
            y_hiperatividade = round((avg_hiperatividade / 27) * 10, 2)
            dados_grafico['TDAH - Hiperatividade']['data'].append({
                'x': data_str,
                'y': y_hiperatividade,
                'original_value': round(avg_hiperatividade, 2),
                'max_value': 27
            })

    # Adicionar dados do PHQ-9 (Depressão)
    phq9_query = PHQ9Teste.query.filter_by(paciente_id=paciente_id)
    if data_inicio_calculada:
        phq9_query = phq9_query.filter(PHQ9Teste.data_realizacao >= data_inicio_calculada)
    if data_fim_param:
        try:
            data_fim_obj = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
            phq9_query = phq9_query.filter(PHQ9Teste.data_realizacao <= datetime.combine(data_fim_obj, datetime.max.time()))
        except:
            pass
            
    phq9_tests = phq9_query.order_by(PHQ9Teste.data_realizacao).all()
    
    if phq9_tests:
        phq9_agg = defaultdict(list)
        for teste in phq9_tests:
            data_str = teste.data_realizacao.date().isoformat()
            phq9_agg[data_str].append(teste.pontuacao_total)
        
        dados_grafico['Teste Depressão (PHQ-9)'] = {'label': 'Teste Depressão (PHQ-9)', 'data': []}
        
        for data_str in sorted(phq9_agg.keys()):
            avg_phq9 = sum(phq9_agg[data_str]) / len(phq9_agg[data_str])
            y_phq9 = round((avg_phq9 / 27) * 10, 2)
            
            dados_grafico['Teste Depressão (PHQ-9)']['data'].append({
                'x': data_str,
                'y': y_phq9,
                'original_value': round(avg_phq9, 2),
                'max_value': 27
            })

    # Adicionar dados do GAD-7 (Ansiedade)
    gad7_query = GAD7Teste.query.filter_by(paciente_id=paciente_id)
    if data_inicio_calculada:
        gad7_query = gad7_query.filter(GAD7Teste.data_realizacao >= data_inicio_calculada)
    if data_fim_param:
        try:
            data_fim_obj = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
            gad7_query = gad7_query.filter(GAD7Teste.data_realizacao <= datetime.combine(data_fim_obj, datetime.max.time()))
        except:
            pass

    gad7_tests = gad7_query.order_by(GAD7Teste.data_realizacao).all()

    if gad7_tests:
        gad7_agg = defaultdict(list)
        for teste in gad7_tests:
            data_str = teste.data_realizacao.date().isoformat()
            gad7_agg[data_str].append(teste.pontuacao_total)
        
        dados_grafico['Teste Ansiedade (GAD-7)'] = {'label': 'Teste Ansiedade (GAD-7)', 'data': []}

        for data_str in sorted(gad7_agg.keys()):
            avg_gad7 = sum(gad7_agg[data_str]) / len(gad7_agg[data_str])
            y_gad7 = round((avg_gad7 / 21) * 10, 2)

            dados_grafico['Teste Ansiedade (GAD-7)']['data'].append({
                'x': data_str,
                'y': y_gad7,
                'original_value': round(avg_gad7, 2),
                'max_value': 21
            })
    
    # Ordenar os dados de cada sintoma por data para garantir ordem cronológica crescente
    for sintoma_nome in dados_grafico:
        dados_grafico[sintoma_nome]['data'].sort(key=lambda x: x['x'])
    
    return jsonify({
        'dados_grafico': list(dados_grafico.values())
    }), 200
