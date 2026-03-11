from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import csv
import io
import pandas as pd
from datetime import datetime
from models import db, Paciente, Evolucao, Dosagem, Sintoma
# IA imports removed to prevent network errors
import tempfile


def safe_ai_import_processing(text_content, patient_id, timeout=30):
    """Processamento seguro de importação com IA"""
    try:
        # Tentar usar versão otimizada primeiro
        try:
            from services.ai_agents_optimized import process_evolution_input_optimized
            result = process_evolution_input_optimized(
                evolution_text_input=text_content,
                timeout=timeout
            )
            # Converter para formato de importação
            return {
                'tipo': 'evolucao',
                'data': None,
                'evolucoes': [{'descricao': result.get('narrative_evolution', text_content), 'observacoes': ''}],
                'dosagens': [],
                'sintomas': [],
                'confianca': 80,
                'ai_processed': True
            }
        except ImportError:
            pass
            
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

import_export_bp = Blueprint('import_export', __name__)

@import_export_bp.route('/export/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_data(patient_id):
    """Exporta todos os dados de um paciente específico"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(patient_id)
        
        # Buscar todos os dados do paciente
        evolucoes = Evolucao.query.filter_by(paciente_id=patient_id).order_by(Evolucao.data_evolucao.desc()).all()
        dosagens = Dosagem.query.filter_by(paciente_id=patient_id).order_by(Dosagem.data.desc()).all()
        sintomas = Sintoma.query.filter_by(paciente_id=patient_id).order_by(Sintoma.data.desc()).all()
        
        # Estruturar dados para exportação
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
                    'observacoes': '',
                    'created_at': ev.data_evolucao.isoformat() if ev.data_evolucao else None
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
                    'concentracao_cbg': dos.concentracao_cbg,
                    'concentracao_cbn': dos.concentracao_cbn,
                    'gotas_por_ml': dos.gotas_por_ml,
                    'created_at': dos.created_at.isoformat() if dos.created_at else None
                } for dos in dosagens
            ],
            'sintomas': [
                {
                    'id': sint.id,
                    'data': sint.data.isoformat(),
                    'sintoma': sint.sintoma,
                    'intensidade': sint.intensidade,
                    'observacoes': getattr(sint, 'observacoes', ''),
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
        
        # Criar arquivo temporário
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
        return jsonify({'error': f'Erro ao exportar dados: {str(e)}'}), 500

@import_export_bp.route('/export/csv/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def export_patient_csv(patient_id):
    """Exporta dados do paciente em formato CSV"""
    try:
        paciente = Paciente.query.get_or_404(patient_id)
        export_type = request.args.get('type', 'all')  # all, evolucoes, dosagens, sintomas
        
        if export_type == 'evolucoes':
            evolucoes = Evolucao.query.filter_by(paciente_id=patient_id).order_by(Evolucao.data_evolucao.desc()).all()
            data = [
                {
                    'Data': ev.data_evolucao.strftime('%Y-%m-%d'),
                    'Descrição': ev.nota_evolucao,
                    'Observações': ''
                } for ev in evolucoes
            ]
            filename = f"evolucoes_{paciente.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
            
        elif export_type == 'dosagens':
            dosagens = Dosagem.query.filter_by(paciente_id=patient_id).order_by(Dosagem.data.desc()).all()
            data = [
                {
                    'Data': dos.data.strftime('%Y-%m-%d'),
                    'Produto': dos.dosagem,
                    'Gotas': dos.gotas or '',
                    'Frequência Diária': dos.frequencia_diaria or '',
                    'CBD (mg/ml)': dos.concentracao_cbd or '',
                    'THC (mg/ml)': dos.concentracao_thc or '',
                    'CBG (mg/ml)': dos.concentracao_cbg or '',
                    'CBN (mg/ml)': dos.concentracao_cbn or '',
                    'Gotas por ML': dos.gotas_por_ml or 30
                } for dos in dosagens
            ]
            filename = f"dosagens_{paciente.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
            
        elif export_type == 'sintomas':
            sintomas = Sintoma.query.filter_by(paciente_id=patient_id).order_by(Sintoma.data.desc()).all()
            data = [
                {
                    'Data': sint.data.strftime('%Y-%m-%d'),
                    'Sintoma': sint.sintoma,
                    'Intensidade': sint.intensidade,
                    'Observações': getattr(sint, 'observacoes', '')
                } for sint in sintomas
            ]
            filename = f"sintomas_{paciente.nome.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Criar CSV
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(output.getvalue())
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({'error': f'Erro ao exportar CSV: {str(e)}'}), 500

@import_export_bp.route('/import/patient/<int:patient_id>', methods=['POST'])
@jwt_required()
def import_patient_data(patient_id):
    """Importa dados para um paciente específico com análise de IA"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(patient_id)
        
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Salvar arquivo temporariamente
        import tempfile
        import os
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        try:
            # Processar arquivo baseado na extensão
            filename = file.filename.lower()
            
            if filename.endswith('.json'):
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                result = process_json_import(patient_id, data)
            elif filename.endswith('.csv'):
                df = pd.read_csv(temp_file.name)
                result = process_csv_import(patient_id, df)
            elif filename.endswith(('.txt', '.md')):
                # Processamento direto de texto sem IA
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                try:
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.now(),
                        nota_evolucao=text_content[:2000]
                    )
                    db.session.add(evolucao)
                    db.session.commit()
                    
                    result = {
                        'evolucoes_criadas': 1,
                        'dosagens_criadas': 0,
                        'sintomas_criados': 0,
                        'erros': [],
                        'message': 'Arquivo TXT importado com sucesso'
                    }
                except Exception as e:
                    result = {
                        'evolucoes_criadas': 0,
                        'dosagens_criadas': 0,
                        'sintomas_criados': 0,
                        'erros': [f'Erro: {str(e)}']
                    }
            elif filename.endswith('.pdf'):
                result = {
                    'evolucoes_criadas': 0,
                    'dosagens_criadas': 0,
                    'sintomas_criados': 0,
                    'erros': ['PDF temporariamente indisponível. Use TXT, CSV ou JSON.']
                }
            elif filename.endswith(('.doc', '.docx', '.rtf', '.odt')):
                result = {
                    'evolucoes_criadas': 0,
                    'dosagens_criadas': 0,
                    'sintomas_criados': 0,
                    'erros': ['Documentos temporariamente indisponível. Use TXT, CSV ou JSON.']
                }
            elif filename.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                result = {
                    'evolucoes_criadas': 0,
                    'dosagens_criadas': 0,
                    'sintomas_criados': 0,
                    'erros': ['Áudio temporariamente indisponível. Use TXT, CSV ou JSON.']
                }
            elif filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                result = {
                    'evolucoes_criadas': 0,
                    'dosagens_criadas': 0,
                    'sintomas_criados': 0,
                    'erros': ['Vídeo temporariamente indisponível. Use TXT, CSV ou JSON.']
                }
            else:
                return jsonify({'error': 'Formato de arquivo não suportado. Use JSON, CSV, TXT, PDF, DOC, DOCX, MP3, WAV, MP4, AVI'}), 400
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_file.name)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao importar dados: {str(e)}'}), 500

def process_json_import(patient_id, data):
    """Processa importação de arquivo JSON"""
    results = {
        'evolucoes_criadas': 0,
        'dosagens_criadas': 0,
        'sintomas_criados': 0,
        'erros': []
    }
    
    try:
        # Importar evoluções se existirem
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
                    results['erros'].append(f'Erro ao importar evolução: {str(e)}')
        
        # Importar dosagens se existirem
        if 'dosagens' in data:
            for dos_data in data['dosagens']:
                try:
                    dosagem = Dosagem(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(dos_data['data']).date(),
                        dosagem=dos_data['dosagem'],
                        gotas=dos_data.get('gotas'),
                        frequencia_diaria=dos_data.get('frequencia_diaria'),
                        concentracao_cbd=dos_data.get('concentracao_cbd'),
                        concentracao_thc=dos_data.get('concentracao_thc'),
                        concentracao_cbg=dos_data.get('concentracao_cbg'),
                        concentracao_cbn=dos_data.get('concentracao_cbn'),
                        gotas_por_ml=dos_data.get('gotas_por_ml', 30)
                    )
                    db.session.add(dosagem)
                    results['dosagens_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao importar dosagem: {str(e)}')
        
        # Importar sintomas se existirem
        if 'sintomas' in data:
            for sint_data in data['sintomas']:
                try:
                    sintoma = Sintoma(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(sint_data['data']).date(),
                        sintoma=sint_data['sintoma'],
                        intensidade=sint_data['intensidade']
                    )
                    db.session.add(sintoma)
                    results['sintomas_criados'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao importar sintoma: {str(e)}')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['erros'].append(f'Erro geral na importação: {str(e)}')
    
    return results

def process_csv_import(patient_id, df):
    """Processa importação de arquivo CSV com análise de IA"""
    results = {
        'evolucoes_criadas': 0,
        'dosagens_criadas': 0,
        'sintomas_criados': 0,
        'erros': [],
        'ai_analysis': []
    }
    
    try:
        # Detectar tipo de dados baseado nas colunas
        columns = [col.lower() for col in df.columns]
        
        for index, row in df.iterrows():
            try:
                # Usar IA para analisar cada linha
                row_text = ' '.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                ai_result = safe_ai_import_processing(row_text, patient_id)
                
                results['ai_analysis'].append({
                    'linha': index + 1,
                    'analise': ai_result
                })
                
                # Criar registros baseados na análise da IA
                if ai_result.get('tipo') == 'evolucao':
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.fromisoformat(ai_result.get('data', datetime.now().isoformat())) if ai_result.get('data') else datetime.now(),
                        nota_evolucao=ai_result.get('descricao', row_text)
                    )
                    db.session.add(evolucao)
                    results['evolucoes_criadas'] += 1
                    
                elif ai_result.get('tipo') == 'dosagem':
                    dosagem = Dosagem(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(ai_result.get('data', datetime.now().isoformat())).date() if ai_result.get('data') else datetime.now().date(),
                        dosagem=ai_result.get('produto', 'Produto importado'),
                        gotas=ai_result.get('gotas'),
                        frequencia_diaria=ai_result.get('frequencia'),
                        concentracao_cbd=ai_result.get('cbd'),
                        concentracao_thc=ai_result.get('thc'),
                        concentracao_cbg=ai_result.get('cbg'),
                        concentracao_cbn=ai_result.get('cbn'),
                        gotas_por_ml=ai_result.get('gotas_por_ml', 30)
                    )
                    db.session.add(dosagem)
                    results['dosagens_criadas'] += 1
                    
            except Exception as e:
                results['erros'].append(f'Erro na linha {index + 1}: {str(e)}')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['erros'].append(f'Erro geral na importação CSV: {str(e)}')
    
    return results

def process_text_import(patient_id, text_content):
    """Processa importação de arquivo de texto com análise de IA"""
    results = {
        'evolucoes_criadas': 0,
        'dosagens_criadas': 0,
        'ai_analysis': None,
        'erros': []
    }
    
    try:
        # Usar IA para analisar o texto completo
        ai_result = safe_ai_import_processing(text_content, patient_id)
        results['ai_analysis'] = ai_result
        
        # Criar registros baseados na análise da IA
        if ai_result.get('evolucoes'):
            for ev_data in ai_result['evolucoes']:
                try:
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.fromisoformat(ev_data.get('data', datetime.now().isoformat())) if ev_data.get('data') else datetime.now(),
                        nota_evolucao=ev_data.get('descricao', '')
                    )
                    db.session.add(evolucao)
                    results['evolucoes_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao criar evolução: {str(e)}')
        
        if ai_result.get('dosagens'):
            for dos_data in ai_result['dosagens']:
                try:
                    dosagem = Dosagem(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(dos_data.get('data', datetime.now().isoformat())).date() if dos_data.get('data') else datetime.now().date(),
                        dosagem=dos_data.get('produto', 'Produto importado'),
                        gotas=dos_data.get('gotas'),
                        frequencia_diaria=dos_data.get('frequencia'),
                        concentracao_cbd=dos_data.get('cbd'),
                        concentracao_thc=dos_data.get('thc'),
                        concentracao_cbg=dos_data.get('cbg'),
                        concentracao_cbn=dos_data.get('cbn'),
                        gotas_por_ml=dos_data.get('gotas_por_ml', 30)
                    )
                    db.session.add(dosagem)
                    results['dosagens_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao criar dosagem: {str(e)}')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['erros'].append(f'Erro na análise de texto: {str(e)}')
    
    return results

@import_export_bp.route('/chat/patient/<int:patient_id>', methods=['POST'])
@jwt_required()
def chat_with_patient_data(patient_id):
    """Permite conversar com os dados do paciente usando IA"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'Pergunta não fornecida'}), 400
        
        # Buscar dados do paciente
        paciente = Paciente.query.get_or_404(patient_id)
        evolucoes = Evolucao.query.filter_by(paciente_id=patient_id).order_by(Evolucao.data_evolucao.desc()).all()
        dosagens = Dosagem.query.filter_by(paciente_id=patient_id).order_by(Dosagem.data.desc()).all()
        sintomas = Sintoma.query.filter_by(paciente_id=patient_id).order_by(Sintoma.data.desc()).all()
        
        # Preparar contexto para a IA
        context = {
            'paciente': {
                'nome': paciente.nome,
                'condicao_medica': getattr(paciente, 'condicao_medica', paciente.diagnostico)
            },
            'evolucoes': [
                {
                    'data': ev.data_evolucao.isoformat(),
                    'descricao': ev.nota_evolucao,
                    'observacoes': ''
                } for ev in evolucoes[:10]  # Últimas 10 evoluções
            ],
            'dosagens': [
                {
                    'data': dos.data.isoformat(),
                    'produto': dos.dosagem,
                    'gotas': dos.gotas,
                    'frequencia': dos.frequencia_diaria,
                    'cbd': dos.concentracao_cbd,
                    'thc': dos.concentracao_thc
                } for dos in dosagens[:10]  # Últimas 10 dosagens
            ],
            'sintomas': [
                {
                    'data': sint.data.isoformat(),
                    'sintoma': sint.sintoma,
                    'intensidade': sint.intensidade
                } for sint in sintomas[:20]  # Últimos 20 sintomas
            ]
        }
        
        # Usar IA para responder à pergunta
        try:
            from services.ai_agents import chat_with_data
        except ImportError:
            def chat_with_data(question, context):
                return {
                    'resposta': 'IA temporariamente indisponível. Tente novamente mais tarde.',
                    'dados_citados': [],
                    'insights': [],
                    'sugestoes': [],
                    'error': 'Módulo de IA não disponível'
                }
        response = chat_with_data(question, context)
        
        return jsonify({
            'question': question,
            'response': response,
            'context_summary': {
                'evolucoes_analisadas': len(context['evolucoes']),
                'dosagens_analisadas': len(context['dosagens']),
                'sintomas_analisados': len(context['sintomas'])
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro no chat: {str(e)}'}), 500

def convert_ai_result_to_import_result(patient_id, ai_result):
    """Converte resultado da IA para formato de importação e salva no banco"""
    results = {
        'evolucoes_criadas': 0,
        'dosagens_criadas': 0,
        'sintomas_criados': 0,
        'erros': [],
        'ai_analysis': ai_result
    }
    
    try:
        if 'error' in ai_result:
            results['erros'].append(ai_result['error'])
            return results
        
        # Processar texto extraído como evolução se não houver estrutura específica
        extracted_text = ai_result.get('extracted_text', ai_result.get('transcribed_text', ''))
        
        if extracted_text and not ai_result.get('evolucoes') and not ai_result.get('dosagens'):
            # Criar evolução com o texto extraído
            try:
                evolucao = Evolucao(
                    paciente_id=patient_id,
                    data_evolucao=datetime.now(),
                    nota_evolucao=extracted_text[:2000]  # Limitar tamanho
                )
                db.session.add(evolucao)
                results['evolucoes_criadas'] += 1
            except Exception as e:
                results['erros'].append(f'Erro ao criar evolução: {str(e)}')
        
        # Processar evoluções estruturadas se existirem
        if ai_result.get('evolucoes'):
            for ev_data in ai_result['evolucoes']:
                try:
                    evolucao = Evolucao(
                        paciente_id=patient_id,
                        data_evolucao=datetime.fromisoformat(ev_data.get('data', datetime.now().isoformat())) if ev_data.get('data') else datetime.now(),
                        nota_evolucao=ev_data.get('descricao', '')
                    )
                    db.session.add(evolucao)
                    results['evolucoes_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao criar evolução: {str(e)}')
        
        # Processar dosagens se existirem
        if ai_result.get('dosagens'):
            for dos_data in ai_result['dosagens']:
                try:
                    dosagem = Dosagem(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(dos_data.get('data', datetime.now().isoformat())).date() if dos_data.get('data') else datetime.now().date(),
                        dosagem=dos_data.get('produto', 'Produto importado'),
                        gotas=dos_data.get('gotas'),
                        frequencia_diaria=dos_data.get('frequencia'),
                        concentracao_cbd=dos_data.get('cbd'),
                        concentracao_thc=dos_data.get('thc'),
                        concentracao_cbg=dos_data.get('cbg'),
                        concentracao_cbn=dos_data.get('cbn'),
                        gotas_por_ml=dos_data.get('gotas_por_ml', 30)
                    )
                    db.session.add(dosagem)
                    results['dosagens_criadas'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao criar dosagem: {str(e)}')
        
        # Processar sintomas se existirem
        if ai_result.get('sintomas'):
            for sint_data in ai_result['sintomas']:
                try:
                    sintoma = Sintoma(
                        paciente_id=patient_id,
                        data=datetime.fromisoformat(sint_data.get('data', datetime.now().isoformat())).date() if sint_data.get('data') else datetime.now().date(),
                        sintoma=sint_data.get('sintoma', ''),
                        intensidade=sint_data.get('intensidade', 5)
                    )
                    db.session.add(sintoma)
                    results['sintomas_criados'] += 1
                except Exception as e:
                    results['erros'].append(f'Erro ao criar sintoma: {str(e)}')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        results['erros'].append(f'Erro geral na conversão: {str(e)}')
    
    return results
