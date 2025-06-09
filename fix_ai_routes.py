#!/usr/bin/env python3
"""
Script para corrigir problemas de network error nas rotas que usam IA
"""

import os
import shutil
from datetime import datetime

def backup_original_files():
    """Cria backup dos arquivos originais"""
    print("=== CRIANDO BACKUP DOS ARQUIVOS ORIGINAIS ===")
    
    files_to_backup = [
        'routes/evolucoes.py',
        'routes/import_export.py',
        'routes/ai_config.py'
    ]
    
    backup_dir = f"backup_routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backup criado: {backup_path}")
    
    print(f"✅ Backup completo em: {backup_dir}")
    print()

def create_optimized_evolucoes_route():
    """Cria versão otimizada da rota de evoluções"""
    print("=== CRIANDO ROTA DE EVOLUÇÕES OTIMIZADA ===")
    
    optimized_content = '''from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Evolucao, Paciente, Profissional, LogAtividade, Dosagem
from datetime import datetime
import os
import tempfile
from werkzeug.utils import secure_filename
import traceback
import time

evolucoes_bp = Blueprint('evolucoes', __name__)

def safe_ai_processing(text_input, llm_provider=None, llm_model_name=None, timeout=30):
    """Processamento seguro com IA incluindo fallback e timeout"""
    try:
        # Importar apenas quando necessário para evitar erros de inicialização
        from services.ai_agents_optimized import process_evolution_input_optimized
        
        current_app.logger.info(f"EVOLUCOES_SAFE_AI: Iniciando processamento com timeout {timeout}s")
        
        result = process_evolution_input_optimized(
            evolution_text_input=text_input,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            timeout=timeout
        )
        
        current_app.logger.info(f"EVOLUCOES_SAFE_AI: Processamento concluído com sucesso")
        return result
        
    except ImportError as e:
        current_app.logger.warning(f"EVOLUCOES_SAFE_AI: Módulo otimizado não encontrado, usando original: {str(e)}")
        try:
            from services.ai_agents import process_evolution_input
            return process_evolution_input(
                evolution_text_input=text_input,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name
            )
        except Exception as fallback_error:
            current_app.logger.error(f"EVOLUCOES_SAFE_AI: Fallback também falhou: {str(fallback_error)}")
            return {
                'narrative_evolution': text_input,
                'dosage_info': None,
                'error': f'IA indisponível: {str(fallback_error)}'
            }
    except Exception as e:
        current_app.logger.error(f"EVOLUCOES_SAFE_AI: Erro no processamento: {str(e)}")
        return {
            'narrative_evolution': text_input,
            'dosage_info': None,
            'error': f'Erro de rede na IA: {str(e)}'
        }

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
        query = query.filter(Evolucao.nota_evolucao.ilike(f'%{termo_busca}%'))
    
    # Ordenar por data decrescente
    evolucoes = query.order_by(Evolucao.data_evolucao.desc()).all()
    
    # Registrar atividade
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Consulta',
        detalhes=f'Listagem de evoluções do paciente ID {paciente_id}'
    )
    db.session.add(log)
    db.session.commit()
    
    # Preparar dados
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
    llm_provider = data.get('llm_provider', 'groq')  # Padrão Groq (mais rápido)
    llm_model_name = data.get('llm_model_name')
    
    # Data da evolução
    data_evolucao_str = data.get('data_evolucao')
    if not data_evolucao_str:
        data_evolucao_str = datetime.utcnow().strftime('%Y-%m-%d')
    else:
        try:
            datetime.strptime(data_evolucao_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data_evolucao inválido. Use YYYY-MM-DD'}), 400

    try:
        current_app.logger.info(f"EVOLUCOES_ROUTE: Recebido para paciente {paciente_id}")

        # Processamento com IA (opcional e com timeout)
        use_ai_processing = data.get('use_ai_processing', False)
        ai_timeout = int(data.get('ai_timeout', 30))  # Timeout configurável
        
        narrative_evolution = input_text
        dosage_info = None
        ai_processed = False
        ai_error = None

        if use_ai_processing:
            current_app.logger.info(f"EVOLUCOES_ROUTE: Processamento com IA solicitado (timeout: {ai_timeout}s)")
            
            ai_analysis_result = safe_ai_processing(
                text_input=input_text,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                timeout=ai_timeout
            )
            
            if ai_analysis_result.get('error'):
                ai_error = ai_analysis_result.get('error')
                current_app.logger.warning(f"EVOLUCOES_ROUTE: IA com erro, mantendo texto original: {ai_error}")
            else:
                narrative_evolution = ai_analysis_result.get('summary') or ai_analysis_result.get('narrative_evolution', input_text)
                dosage_info = ai_analysis_result.get('dosage_info')
                ai_processed = True
                current_app.logger.info(f"EVOLUCOES_ROUTE: IA processou com sucesso")

        # Salvar evolução no banco
        from services.db_tools import save_evolution_to_db
        evolution_save_result = save_evolution_to_db(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            narrative_evolution=narrative_evolution,
            data_evolucao_str=data_evolucao_str
        )

        if not evolution_save_result.get("success"):
            current_app.logger.error(f"EVOLUCOES_ROUTE: Falha ao salvar evolução: {evolution_save_result.get('error')}")
            return jsonify({'error': f"Falha ao salvar evolução: {evolution_save_result.get('error')}"}), 500
        
        saved_evolucao_id = evolution_save_result.get("evolucao_id")
        nova_evolucao = Evolucao.query.get(saved_evolucao_id)
        
        if not nova_evolucao:
             return jsonify({'error': "Falha ao buscar evolução após salvar."}), 500

        # Salvar dosagem se extraída pela IA
        saved_dosage_details_msg = "Nenhuma informação de dosagem processada."
        if dosage_info and isinstance(dosage_info, dict) and dosage_info.get('dosage_text'):
            from services.db_tools import save_dosage_to_db
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
            
            if dosage_save_result.get("success"):
                saved_dosage_details_msg = f"Dosagem extraída salva (ID: {dosage_save_result.get('dosagem_id')})."
            else:
                saved_dosage_details_msg = f"Falha ao salvar dosagem: {dosage_save_result.get('error')}"
        
        # Log da atividade
        ai_status = "Sim" if ai_processed else ("Erro" if ai_error else "Não")
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Registro',
            detalhes=f'Nova evolução para paciente {paciente_id}. IA: {ai_status}. {saved_dosage_details_msg}'
        )
        db.session.add(log)
        db.session.commit()
        
        # Preparar resposta
        response_data = {
            'message': 'Evolução registrada com sucesso. ' + saved_dosage_details_msg,
            'evolucao': nova_evolucao.to_dict(),
            'ai_processed': ai_processed
        }
        
        if ai_error:
            response_data['ai_warning'] = f"IA indisponível: {ai_error}"
        
        return jsonify(response_data), 201
        
    except Exception as e:
        current_app.logger.error(f"EVOLUCOES_ROUTE: Exceção geral: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@evolucoes_bp.route('/processar-ia', methods=['POST'])
@jwt_required()
def processar_texto_ia():
    """Endpoint otimizado para processar texto com IA"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    data = request.get_json()
    
    # Validar dados
    if 'texto' not in data or not data['texto'].strip():
        return jsonify({'error': 'Texto é obrigatório'}), 400
    
    if 'paciente_id' not in data:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400
    
    texto = data['texto'].strip()
    paciente_id = data['paciente_id']
    
    # Verificar paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({'error': 'Paciente não encontrado'}), 404
    
    try:
        current_app.logger.info(f"EVOLUCOES_IA: Processando texto para paciente {paciente_id}")
        
        # Configurações de IA
        llm_provider = data.get('llm_provider', 'groq')
        llm_model_name = data.get('llm_model_name')
        ai_timeout = int(data.get('timeout', 30))
        
        # Processar com IA de forma segura
        ai_result = safe_ai_processing(
            text_input=texto,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
            timeout=ai_timeout
        )
        
        # Registrar atividade
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Processamento IA',
            detalhes=f'Texto processado para paciente {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        # Preparar resposta
        response_data = {
            'texto_melhorado': ai_result.get('summary') or ai_result.get('narrative_evolution', texto),
            'sugestoes': [],
            'processing_time': ai_result.get('processing_time', 'N/A')
        }
        
        # Adicionar sugestões se disponíveis
        if ai_result.get('dosage_info'):
            dosage_info = ai_result.get('dosage_info')
            if dosage_info.get('dosage_text'):
                response_data['sugestoes'].append(f"Dosagem: {dosage_info.get('dosage_text')}")
            if dosage_info.get('drops'):
                response_data['sugestoes'].append(f"Gotas: {dosage_info.get('drops')}")
            if dosage_info.get('daily_frequency'):
                response_data['sugestoes'].append(f"Frequência: {dosage_info.get('daily_frequency')}x/dia")
        
        # Incluir aviso se houve erro
        if ai_result.get('error'):
            response_data['warning'] = f"IA com limitações: {ai_result.get('error')}"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"EVOLUCOES_IA: Exceção: {str(e)}")
        return jsonify({
            'error': f'Erro no processamento: {str(e)}',
            'texto_melhorado': texto,  # Fallback para texto original
            'sugestoes': []
        }), 500

# Manter outras rotas inalteradas
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
    
    if evolucao.profissional_id != profissional_id:
        return jsonify({'error': 'Sem permissão para editar'}), 403
    
    data = request.get_json()
    
    if 'nota_evolucao' not in data or not data['nota_evolucao'].strip():
        return jsonify({'error': 'Nota de evolução é obrigatória'}), 400
    
    try:
        evolucao.nota_evolucao = data['nota_evolucao'].strip()
        db.session.commit()
        
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
        return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500

@evolucoes_bp.route('/<int:evolucao_id>', methods=['DELETE'])
@jwt_required()
def excluir_evolucao(evolucao_id):
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    evolucao = Evolucao.query.get(evolucao_id)
    
    if not evolucao:
        return jsonify({'error': 'Evolução não encontrada'}), 404
    
    if evolucao.profissional_id != profissional_id:
        return jsonify({'error': 'Sem permissão para excluir'}), 403
    
    try:
        paciente_id = evolucao.paciente_id
        db.session.delete(evolucao)
        
        log = LogAtividade(
            profissional_id=profissional_id,
            acao='Exclusão',
            detalhes=f'Evolução excluída: ID {evolucao_id} do paciente {paciente_id}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Evolução excluída com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao excluir: {str(e)}'}), 500

@evolucoes_bp.route('/busca', methods=['GET'])
@jwt_required()
def buscar_evolucoes():
    """Buscar evoluções por texto"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    termo_busca = request.args.get('termo', '')
    
    if not termo_busca:
        return jsonify({'error': 'Termo de busca não fornecido'}), 400
    
    evolucoes = Evolucao.query.filter(
        Evolucao.nota_evolucao.ilike(f'%{termo_busca}%')
    ).order_by(Evolucao.data_evolucao.desc()).all()
    
    log = LogAtividade(
        profissional_id=profissional_id,
        acao='Busca',
        detalhes=f'Busca por: "{termo_busca}"'
    )
    db.session.add(log)
    db.session.commit()
    
    resultados = []
    for evolucao in evolucoes:
        evolucao_dict = evolucao.to_dict()
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
'''
    
    with open('routes/evolucoes_optimized.py', 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    print("✅ Rota de evoluções otimizada criada: routes/evolucoes_optimized.py")
    print()

def create_optimized_import_export_route():
    """Cria versão otimizada da rota de import/export"""
    print("=== CRIANDO ROTA DE IMPORT/EXPORT OTIMIZADA ===")
    
    # Criar versão simplificada focada em estabilidade
    optimized_content = '''from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import csv
import io
import pandas as pd
from datetime import datetime
from models import db, Paciente, Evolucao, Dosagem, Sintoma
import tempfile
import os
import traceback

import_export_bp = Blueprint('import_export', __name__)

def safe_ai_import_processing(text_content, patient_id, timeout=30):
    """Processamento seguro de importação com IA"""
    try:
        # Tentar usar versão otimizada primeiro
        try:
            from services.ai_agents_optimized import process_evolution_input_optimized
            return process_evolution_input_optimized(
                evolution_text_input=text_content,
                timeout=timeout
            )
        except ImportError:
            # Fallback para versão original
            from services.ai_agents import process_import_data
            return process_import_data(text_content, patient_id)
            
    except Exception as e:
        return {
            'tipo': 'evolucao',
            'data': None,
            'evolucoes': [{'descricao': text_content, 'observacoes': ''}],
            'dosagens': [],
            'sintomas': [],
            'confianca': 0,
            'error': f'IA indisponível: {str(e)}'
        }

@import_export_bp.route('/export/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_data(patient_id):
    """Exporta dados do paciente em JSON"""
    try:
        paciente = Paciente.query.get_or_404(patient_id)
        
        evolucoes = Evolucao.query.filter_by(paciente_id=patient_id).order_by(Evolucao.data_evolucao.desc()).all()
        dosagens = Dosagem.query.filter_by(paciente_id=patient_id).order_by(Dosagem.data.desc()).all()
        sintomas = Sintoma.query.filter_by(paciente_id=patient_id).order_by(Sintoma.data.desc()).all()
        
        export_data = {
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'data_nascimento': paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
                'cpf': paciente.cpf,
                'telefone': paciente.telefone,
                'email': paciente.email,
                'endereco': paciente.endereco,
                'condicao_medica': getattr(paciente, 'condicao_medica', paciente.diagnostico),
                'created_at': paciente.created_at.isoformat() if paciente.created_at else None
            },
            'evolucoes': [
                {
                    'id': ev.id,
                    'data': ev.data_evolucao.isoformat(),
                    'descricao': ev.nota_evolucao,
                    'created_at': ev.data_evolucao.isoformat()
                } for ev in evolucoes
            ],
            'dosagens': [
                {
                    'id': dos.id,
                    'data': dos.data.isoformat(),
                    'dosagem': dos.dosagem,
                    'gotas': dos.gotas,
                    'frequencia_diaria': dos.frequencia_diaria,
                    'concentracao_cbd': dos.concentracao_cbd,
                    'concentracao_thc': dos.concentracao_thc,
                    'created_at': dos.created_at.isoformat() if dos.created_at else None
                } for dos in dosagens
            ],
            'sintomas': [
                {
                    'id': sint.id,
                    'data': sint.data.isoformat(),
                    'sintoma': sint.sintoma,
                    'intensidade': sint.intensidade,
                    'created_at': sint.created_at.isoformat() if sint.created_at else None
                } for sint in sintomas
            ],
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'exported_by': get_jwt_identity(),
                'total_evolucoes': len(evolucoes),
                'total_dosagens': len(dosagens),
                'total_sintomas': len(sintomas)
            }
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        json.dump(export_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        filename = f"paciente_{paciente.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': f'Erro ao exportar: {str(e)}'}), 500

@import_export_bp.route('/import/patient/<int:patient_id>', methods=['POST'])
@jwt_required()
def import_patient_data(patient_id):
    """Importa dados com processamento IA otimizado"""
    try:
        paciente = Paciente.query.get_or_404(patient_id)
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Configurações de IA
        use_ai = request.form.get('use_ai', 'false').lower() == 'true'
        ai_timeout = int(request.form.get('ai_timeout', 30))
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            filename = file.filename.lower()
            
            if filename.endswith('.json'):
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                result = process_json_import(patient_id, data)
                
            elif filename.endswith('.csv'):
                df = pd.read_csv(temp_file.name)
                result = process_csv_import(patient_id, df, use_ai, ai_timeout)
                
            elif filename.endswith(('.txt', '.md')):
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                result = process_text_import(patient_id, text_content, use_ai, ai_timeout)
                
            else:
                return jsonify({'error': 'Formato não suportado. Use JSON, CSV ou TXT'}), 400
                
        finally:
            os.unlink(temp_file.name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Erro na importação: {str(e)}'}), 500

def process_json_import(patient_id, data):
    """Processa importação JSON"""
    results = {
        'evolucoes_criadas': 0,
        'dosagens_criadas': 0,
        'sintomas_criados': 0,
        'erros': []
    }
    
    try:
        if 'evolucoes' in data:
            for ev_data in data['evolucoes']:
                try:
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.fromisoformat(ev_data['data']),
                        nota_evolucao=ev_data['descricao']
                    )
                    db.session.add(evolucao)
                    results['evolucoes_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro na evolução: {str(e)}')
        
        if 'dosagens' in data:
            for dos_data in data['dosagens']:
                try:
                    dosagem = Dosagem(
                        paciente_id=patient_id,
                        data=datetime.fr
