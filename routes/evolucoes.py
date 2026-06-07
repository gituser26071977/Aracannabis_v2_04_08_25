from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Evolucao, Paciente, Profissional, LogAtividade, Exame
from datetime import datetime
# Removido import json e process_evolution_input daqui, pois a lógica de IA será chamada de forma diferente
# Agora importamos as db_tools e o processador de IA de forma separada
# from services.ai_agents import process_evolution_input, process_audio_file, process_video_file # IA para análise de texto - TEMPORARIAMENTE DESABILITADO
from services.db_tools import save_evolution_to_db, save_dosage_to_db # Ferramentas de BD
import os
import tempfile
from werkzeug.utils import secure_filename


def safe_ai_processing(text_input, llm_provider=None, llm_model_name=None, timeout=30):
    """Processamento seguro com IA incluindo fallback e timeout - TEMPORARIAMENTE DESABILITADO"""
    current_app.logger.warning("SAFE_AI: IA temporariamente desabilitada para testes")
    return {
        'narrative_evolution': text_input,
        'dosage_info': None,
        'error': 'IA temporariamente desabilitada para testes'
    }

evolucoes_bp = Blueprint('evolucoes', __name__)

@evolucoes_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_evolucoes(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    # Parâmetros de busca
    termo_busca = request.args.get('busca', '')
    
    # Construir a consulta base
    query = Evolucao.query.filter_by(paciente_id=paciente_id)
    
    # Aplicar filtro de busca se fornecido
    if termo_busca:
        # Busca case-insensitive usando LIKE
        query = query.filter(Evolucao.nota_evolucao.ilike(f'%{termo_busca}%'))
    
    # Ordenar por data decrescente
    evolucoes = query.order_by(Evolucao.data_evolucao.desc()).all()
    
    # Buscar exames do paciente
    exames = Exame.query.filter_by(paciente_id=paciente_id).order_by(Exame.data_exame.desc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Listagem de evoluções e exames do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    # Preparar dados com nome do profissional
    evolucoes_data = []
    for evolucao in evolucoes:
        evolucao_dict = evolucao.to_dict()
        evolucoes_data.append(evolucao_dict)
    
    # Preparar dados dos exames
    exames_data = []
    for exame in exames:
        exame_dict = exame.to_dict()
        exames_data.append(exame_dict)
    
    return jsonify({
        'evolucoes': evolucoes_data,
        'exames': exames_data
    }), 200

@evolucoes_bp.route('/paciente/<int:paciente_id>', methods=['POST'])
@jwt_required()
def registrar_evolucao(paciente_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'nota_evolucao' not in data or not data['nota_evolucao'].strip():
        return jsonify({'error': 'Nota de evolução é obrigatória'}), 400
    
    input_text = data['nota_evolucao'].strip()
    llm_provider = data.get('llm_provider') # Novo: ex: "ollama", "groq", "openai"
    llm_model_name = data.get('llm_model_name') # Novo: ex: "llama3:8b-instruct-q4_1", "gpt-4-turbo"
    
    # Data da evolução (pode vir do payload ou ser a data atual)
    data_evolucao_str = data.get('data_evolucao')
    if not data_evolucao_str:
        data_evolucao_str = datetime.utcnow().strftime('%Y-%m-%d')
    else:
        # Validar formato da data se fornecida
        try:
            datetime.strptime(data_evolucao_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data_evolucao inválido. Use YYYY-MM-DD'}), 400

    try:
        current_app.logger.info(f"EVOLUCOES_ROUTE: Recebido para paciente {paciente_id}: nota='{input_text}', provider='{llm_provider}', model='{llm_model_name}', data='{data_evolucao_str}'")

        # Por padrão, para entrada de texto simples, não chamaremos a IA por enquanto.
        # A chamada à IA pode ser reativada sob uma condição específica ou em outro endpoint.
        use_ai_processing = data.get('use_ai_processing', False)
        ai_timeout = int(data.get('ai_timeout', 30))  # Timeout configurável # Novo parâmetro, default False

        narrative_evolution = input_text
        dosage_info = None
        ai_processed = False

        if use_ai_processing: # Somente processa com IA se explicitamente solicitado
            current_app.logger.info("EVOLUCOES_ROUTE: Processamento com IA solicitado.")
            # 1. Processar o texto com IA para análise
            ai_analysis_result = safe_ai_processing(
                evolution_text_input=input_text,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name
                # image_extracted_text não está sendo passado aqui, adicionar se necessário
            )
            current_app.logger.info(f"EVOLUCOES_ROUTE: Resultado da análise da IA: {ai_analysis_result}")
            
            if ai_analysis_result.get('error'):
                current_app.logger.error(f"EVOLUCOES_ROUTE: Erro da IA ao processar evolução: {ai_analysis_result.get('error')}")
                # Mantém narrative_evolution como input_text original
            else:
                # Se a IA retornar um 'summary' (da task simplificada) ou 'narrative_evolution' (da task completa)
                narrative_evolution = ai_analysis_result.get('summary') or ai_analysis_result.get('narrative_evolution', input_text)
                dosage_info = ai_analysis_result.get('dosage_info')
            ai_processed = True
        else:
            current_app.logger.info("EVOLUCOES_ROUTE: Processamento com IA NÃO solicitado. Salvando texto original.")
            # narrative_evolution já é input_text, dosage_info já é None

        # 2. Salvar a evolução no banco de dados
        evolution_save_result = save_evolution_to_db(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            narrative_evolution=narrative_evolution,
            data_evolucao_str=data_evolucao_str
        )
        current_app.logger.info(f"EVOLUCOES_ROUTE: Resultado do salvamento da evolução: {evolution_save_result}")

        if not evolution_save_result.get("success"):
            current_app.logger.error(f"EVOLUCOES_ROUTE: Falha ao salvar evolução no BD: {evolution_save_result.get('error')}")
            return jsonify({'error': f"Falha ao salvar evolução: {evolution_save_result.get('error')}"}), 500
        
        saved_evolucao_id = evolution_save_result.get("evolucao_id")
        # Precisamos buscar a nova_evolucao para retornar no to_dict()
        nova_evolucao = Evolucao.query.get(saved_evolucao_id)
        if not nova_evolucao: # Checagem de segurança
             current_app.logger.error(f"EVOLUCOES_ROUTE: Evolução salva (ID: {saved_evolucao_id}) não encontrada no BD após salvar.")
             return jsonify({'error': "Falha ao buscar evolução após salvar."}), 500


        # 3. Se a IA extraiu informações de dosagem, salvar no banco de dados
        saved_dosage_details_msg = "Nenhuma informação de dosagem processada."
        if dosage_info and isinstance(dosage_info, dict) and dosage_info.get('dosage_text'):
            current_app.logger.info(f"EVOLUCOES_ROUTE: Tentando salvar dosagem: {dosage_info}")
            dosage_save_result = save_dosage_to_db(
                paciente_id=paciente_id,
                data_dosagem_str=data_evolucao_str, 
                dosage_text=dosage_info.get('dosage_text'),
                drops=dosage_info.get('drops'),
                daily_frequency=dosage_info.get('daily_frequency'),
                cbd_concentration_mg_ml=dosage_info.get('cbd_concentration_mg_ml'),
                thc_concentration_mg_ml=dosage_info.get('thc_concentration_mg_ml'),
                cbg_concentration_mg_ml=dosage_info.get('cbg_concentration_mg_ml'),
                cbn_concentration_mg_ml=dosage_info.get('cbn_concentration_mg_ml')
            )
            current_app.logger.info(f"EVOLUCOES_ROUTE: Resultado do salvamento da dosagem: {dosage_save_result}")
            if not dosage_save_result.get("success"):
                saved_dosage_details_msg = f"Evolução salva (ID: {saved_evolucao_id}), mas falha ao salvar dosagem extraída: {dosage_save_result.get('error')}"
                current_app.logger.warning(saved_dosage_details_msg)
            else:
                saved_dosage_details_msg = f"Dosagem extraída salva com sucesso (ID: {dosage_save_result.get('dosagem_id')})."
        
        # Registrar atividade de log principal para a evolução
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Registro',
            detalhes=f'Nova evolução registrada para paciente ID {paciente_id}. IA processou: {"Sim" if ai_processed else "Não"}. {saved_dosage_details_msg}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Evolução registrada com sucesso. ' + saved_dosage_details_msg,
            'evolucao': nova_evolucao.to_dict() 
        }), 201
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"EVOLUCOES_ROUTE: Exceção geral ao registrar evolução: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Erro interno ao registrar evolução: {str(e)}'}), 500

@evolucoes_bp.route('/<int:evolucao_id>', methods=['GET'])
@jwt_required()
def obter_evolucao(evolucao_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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

@evolucoes_bp.route('/busca', methods=['GET'])
@jwt_required()
def buscar_evolucoes():
    """Endpoint para buscar evoluções por texto em todos os pacientes"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Parâmetros de busca
    termo_busca = request.args.get('termo', '')
    
    if not termo_busca:
        return jsonify({'error': 'Termo de busca não fornecido'}), 400
    
    # Buscar evoluções que contenham o termo de busca
    evolucoes = Evolucao.query.filter(
        Evolucao.nota_evolucao.ilike(f'%{termo_busca}%')
    ).order_by(Evolucao.data_evolucao.desc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Busca',
        detalhes=f'Busca por evoluções com o termo: "{termo_busca}"'
    )
    db.session.add(log)
    db.session.commit()
    
    # Preparar dados com informações do paciente
    resultados = []
    for evolucao in evolucoes:
        evolucao_dict = evolucao.to_dict()
        
        # Adicionar informações do paciente
        paciente = Paciente.query.get(evolucao.paciente_id)
        if paciente:
            evolucao_dict['paciente'] = {
                'id': paciente.id,
                'nome': paciente.nome
            }
        
        resultados.append(evolucao_dict)
    
    return jsonify({
        'resultados': resultados,
        'total': len(resultados),
        'termo_busca': termo_busca
    }), 200

@evolucoes_bp.route('/logs', methods=['GET'])
@jwt_required()
def listar_logs():
    """Endpoint para listar logs de atividades (para administradores)"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
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

@evolucoes_bp.route('/processar-ia', methods=['POST'])
@jwt_required()
def processar_texto_ia():
    """Endpoint para processar texto com IA e retornar sugestões"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    
    # Validar dados obrigatórios
    if 'texto' not in data or not data['texto'].strip():
        return jsonify({'error': 'Texto é obrigatório'}), 400
    
    if 'paciente_id' not in data:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400
    
    texto = data['texto'].strip()
    paciente_id = data['paciente_id']
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    try:
        current_app.logger.info(f"EVOLUCOES_IA: Processando texto com IA para paciente {paciente_id}")
        
        # Processar texto com IA
        ai_result = safe_ai_processing(
            evolution_text_input=texto,
            llm_provider=data.get('llm_provider', 'groq'),
            llm_model_name=data.get('llm_model_name', 'llama3-8b-8192')
        )
        
        if ai_result.get('error'):
            current_app.logger.error(f"EVOLUCOES_IA: Erro da IA: {ai_result.get('error')}")
            return jsonify({'error': f"Erro ao processar com IA: {ai_result.get('error')}"}), 500
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Processamento IA',
            detalhes=f'Texto processado com IA para paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        # Preparar resposta
        response_data = {
            'texto_melhorado': ai_result.get('summary') or ai_result.get('narrative_evolution', texto),
            'sugestoes': []
        }
        
        # Adicionar sugestões se disponíveis
        if ai_result.get('dosage_info'):
            dosage_info = ai_result.get('dosage_info')
            if dosage_info.get('dosage_text'):
                response_data['sugestoes'].append(f"Dosagem identificada: {dosage_info.get('dosage_text')}")
            if dosage_info.get('drops'):
                response_data['sugestoes'].append(f"Gotas: {dosage_info.get('drops')}")
            if dosage_info.get('daily_frequency'):
                response_data['sugestoes'].append(f"Frequência: {dosage_info.get('daily_frequency')}x ao dia")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"EVOLUCOES_IA: Exceção ao processar com IA: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Erro interno ao processar com IA: {str(e)}'}), 500

@evolucoes_bp.route('/upload-arquivo', methods=['POST'])
@jwt_required()
def upload_arquivo():
    """Endpoint para upload e processamento de arquivos com IA"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    # Verificar se arquivo foi enviado
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    # Obter dados do formulário
    paciente_id = request.form.get('paciente_id')
    file_type = request.form.get('file_type')
    
    if not paciente_id:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400
    
    # Verificar se o paciente existe
    paciente = Paciente.query.get(int(paciente_id))
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    try:
        # Salvar arquivo temporariamente
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        current_app.logger.info(f"UPLOAD: Arquivo {filename} salvo em {temp_path}, tipo: {file_type}")
        
        # Processar arquivo baseado no tipo
        if file_type == 'text':
            # Ler arquivo de texto
            with open(temp_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Processar com IA
            ai_result = safe_ai_processing(
                evolution_text_input=text_content,
                llm_provider='groq',
                llm_model_name='llama3-8b-8192'
            )
            
        elif file_type == 'audio':
            # Processar arquivo de áudio - TEMPORARIAMENTE DESABILITADO
            ai_result = {
                'narrative_evolution': 'Processamento de áudio temporariamente desabilitado',
                'transcribed_text': 'Funcionalidade de IA desabilitada',
                'source': 'audio',
                'error': 'IA temporariamente desabilitada'
            }
            
        elif file_type == 'video':
            # Processar arquivo de vídeo - TEMPORARIAMENTE DESABILITADO
            ai_result = {
                'narrative_evolution': 'Processamento de vídeo temporariamente desabilitado',
                'transcribed_text': 'Funcionalidade de IA desabilitada',
                'source': 'video',
                'error': 'IA temporariamente desabilitada'
            }
            
        else:
            return jsonify({'error': 'Tipo de arquivo não suportado'}), 400
        
        # Limpar arquivo temporário
        os.remove(temp_path)
        os.rmdir(temp_dir)
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Upload e Processamento IA',
            detalhes=f'Arquivo {filename} ({file_type}) processado com IA para paciente ID {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        # Preparar resposta
        response_data = {
            'texto_melhorado': ai_result.get('summary') or ai_result.get('narrative_evolution', ''),
            'transcribed_text': ai_result.get('transcribed_text', ''),
            'source': ai_result.get('source', file_type),
            'sugestoes': []
        }
        
        # Adicionar sugestões se disponíveis
        if ai_result.get('dosage_info'):
            dosage_info = ai_result.get('dosage_info')
            if dosage_info.get('dosage_text'):
                response_data['sugestoes'].append(f"Dosagem identificada: {dosage_info.get('dosage_text')}")
            if dosage_info.get('drops'):
                response_data['sugestoes'].append(f"Gotas: {dosage_info.get('drops')}")
            if dosage_info.get('daily_frequency'):
                response_data['sugestoes'].append(f"Frequência: {dosage_info.get('daily_frequency')}x ao dia")
        
        if ai_result.get('error'):
            response_data['error'] = ai_result.get('error')
        
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"UPLOAD: Exceção ao processar arquivo: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Limpar arquivos temporários em caso de erro
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass
        
        return jsonify({'error': f'Erro interno ao processar arquivo: {str(e)}'}), 500
