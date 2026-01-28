from flask import Blueprint, request, jsonify, current_app, send_from_directory
from models import db, Exame, ExameImagem, ExameLabResultado, OCRResultado, Paciente, Profissional
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
from services.email_service import EmailService
from services.ocr_service import ocr_service  # OCR service - now implemented
email_service = EmailService()  # Create an instance of the email service

exames_bp = Blueprint('exames', __name__, url_prefix='/api')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@exames_bp.route('/exames', methods=['POST'])
def criar_exame():
    data = request.form
    paciente_id = data.get('paciente_id')
    profissional_id = data.get('profissional_id')
    data_exame_str = data.get('data_exame')
    tipo_exame = data.get('tipo_exame')
    titulo = data.get('titulo')  # Novo campo para todos os tipos
    descricao = data.get('descricao')  # Campo para tipo 'texto'
    valor = data.get('valor')  # Campo para tipo 'numerico'
    unidade = data.get('unidade')  # Campo para tipo 'numerico'

    if not paciente_id:
        return jsonify({"error": "ID do paciente é obrigatório"}), 400
    if not tipo_exame or tipo_exame not in ['texto', 'arquivo', 'numerico']:
        return jsonify({"error": "Tipo de exame inválido. Deve ser 'texto', 'arquivo' ou 'numerico'"}), 400
    if not titulo:
        return jsonify({"error": "Título do exame é obrigatório"}), 400
    if tipo_exame == 'texto' and not descricao:
        return jsonify({"error": "Descrição é obrigatória para exames de texto"}), 400
    if tipo_exame == 'numerico' and not valor:
        return jsonify({"error": "Valor é obrigatório para exames numéricos"}), 400

    try:
        data_exame = datetime.strptime(data_exame_str, '%Y-%m-%d') if data_exame_str else datetime.utcnow()
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400

    # Automatically flag hemoglobin data for chart generation
    is_chartable = False
    if tipo_exame == 'numerico' and titulo and 'hemoglobina' in titulo.lower():
        is_chartable = True

    novo_exame = Exame(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        data_exame=data_exame,
        tipo_exame=tipo_exame,
        titulo=titulo,
        descricao=descricao,
        valor=valor,
        unidade=unidade,
        is_chartable=is_chartable
    )

    db.session.add(novo_exame)
    db.session.commit()

    # Processar arquivos se for exame do tipo 'arquivo'
    if tipo_exame == 'arquivo':
        if 'arquivos' not in request.files:
            return jsonify({"error": "Nenhum arquivo enviado"}), 400
            
        arquivos = request.files.getlist('arquivos')
        arquivos_processados = 0
        
        for arq in arquivos:
            if arq.filename == '':
                continue
            if arq and allowed_file(arq.filename):
                filename = secure_filename(arq.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER_EXAMES'], unique_filename)
                
                # Criar diretório se não existir
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                arq.save(filepath)
                
                nova_imagem = ExameImagem(
                    exame_id=novo_exame.id,
                    arquivo_nome=filename,
                    arquivo_caminho=unique_filename,
                    laudo=descricao or ''  # usando a descrição do exame para todos os arquivos
                )
                db.session.add(nova_imagem)
                arquivos_processados += 1
        
        if arquivos_processados == 0:
            return jsonify({"error": "Nenhum arquivo válido foi processado"}), 400
    
    # Não há processamento adicional necessário para 'texto' e 'numerico'
    # pois os dados já estão armazenados no objeto Exame

    db.session.commit()
    
    # Enviar email com resultados do exame
    try:
        # Obter paciente para email
        paciente = Paciente.query.get(paciente_id)
        if paciente and paciente.email:
            # Formatar resultados com base no tipo de exame
            if tipo_exame == 'texto':
                resultados = descricao
            elif tipo_exame == 'arquivo':
                resultados = f"{len(arquivos)} arquivo(s) anexado(s)"
            elif tipo_exame == 'numerico':
                resultados = f"{valor} {unidade}"
            else:
                resultados = "Resultados disponíveis no sistema"
            
            # Enviar email
            email_service.send_exam_email(
                to_email=paciente.email,
                paciente_nome=paciente.nome,
                exame_titulo=titulo,
                exame_data=data_exame,
                exame_resultados=resultados,
                observacoes="Resultados disponíveis no sistema"
            )
            email_status = "Email enviado com sucesso"
        else:
            email_status = "Paciente não possui email cadastrado"
    except Exception as e:
        current_app.logger.error(f"Erro ao enviar email de exame: {str(e)}")
        email_status = f"Erro ao enviar email: {str(e)}"
    
    response = novo_exame.to_dict()
    response['email_status'] = email_status
    return jsonify(response), 201

@exames_bp.route('/pacientes/<int:paciente_id>/exames', methods=['GET'])
def listar_exames_paciente(paciente_id):
    exames = Exame.query.filter_by(paciente_id=paciente_id).all()
    return jsonify([exame.to_dict() for exame in exames])

@exames_bp.route('/exames/<int:exame_id>', methods=['GET'])
def obter_exame(exame_id):
    exame = Exame.query.get_or_404(exame_id)
    return jsonify(exame.to_dict())

@exames_bp.route('/exames/<int:exame_id>/imagens', methods=['GET'])
def listar_imagens_exame(exame_id):
    imagens = ExameImagem.query.filter_by(exame_id=exame_id).all()
    return jsonify([img.to_dict() for img in imagens])

@exames_bp.route('/exames/<int:exame_id>/resultados', methods=['GET'])
def listar_resultados_exame(exame_id):
    resultados = ExameLabResultado.query.filter_by(exame_id=exame_id).all()
    return jsonify([res.to_dict() for res in resultados])

@exames_bp.route('/exames/<int:exame_id>', methods=['PUT'])
def atualizar_exame(exame_id):
    exame = Exame.query.get_or_404(exame_id)
    data = request.json
    
    if 'data_exame' in data:
        try:
            exame.data_exame = datetime.strptime(data['data_exame'], '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400
    
    if 'tipo_exame' in data:
        exame.tipo_exame = data['tipo_exame']
    
    db.session.commit()
    return jsonify(exame.to_dict())

@exames_bp.route('/exames/<int:exame_id>', methods=['DELETE'])
def excluir_exame(exame_id):
    exame = Exame.query.get_or_404(exame_id)
    
    # Delete associated images
    imagens = ExameImagem.query.filter_by(exame_id=exame_id).all()
    for img in imagens:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER_EXAMES'], img.arquivo_caminho)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(img)
    
    # Delete associated lab results
    resultados = ExameLabResultado.query.filter_by(exame_id=exame_id).all()
    for res in resultados:
        db.session.delete(res)
    
    db.session.delete(exame)
    db.session.commit()
    return jsonify({"message": "Exame e todos os dados associados excluídos com sucesso"}), 200

@exames_bp.route('/imagens/<int:imagem_id>', methods=['GET'])
def obter_imagem(imagem_id):
    imagem = ExameImagem.query.get_or_404(imagem_id)
    return jsonify(imagem.to_dict())

@exames_bp.route('/imagens/<int:imagem_id>', methods=['DELETE'])
def excluir_imagem(imagem_id):
    imagem = ExameImagem.query.get_or_404(imagem_id)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER_EXAMES'], imagem.arquivo_caminho)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(imagem)
    db.session.commit()
    return jsonify({"message": "Imagem excluída com sucesso"}), 200

@exames_bp.route('/resultados/<int:resultado_id>', methods=['PUT'])
def atualizar_resultado(resultado_id):
    resultado = ExameLabResultado.query.get_or_404(resultado_id)
    data = request.json
    resultado.teste_nome = data.get('teste_nome', resultado.teste_nome)
    resultado.valor = data.get('valor', resultado.valor)
    resultado.unidade = data.get('unidade', resultado.unidade)
    resultado.valor_referencia = data.get('valor_referencia', resultado.valor_referencia)
    db.session.commit()
    return jsonify(resultado.to_dict())

@exames_bp.route('/resultados/<int:resultado_id>', methods=['DELETE'])
def excluir_resultado(resultado_id):
    resultado = ExameLabResultado.query.get_or_404(resultado_id)
    db.session.delete(resultado)
    db.session.commit()
    return jsonify({"message": "Resultado excluído com sucesso"}), 200

# Rota para servir arquivos de exames
@exames_bp.route('/exames/arquivos/<filename>')
def servir_arquivo_exame(filename):
    try:
        # Get the full path to the uploads directory
        uploads_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER_EXAMES'])
        return send_from_directory(uploads_dir, filename)
    except FileNotFoundError:
        return jsonify({"error": "Arquivo não encontrado"}), 404

# Rota para gerar dados de gráfico para exames numéricos
@exames_bp.route('/pacientes/<int:paciente_id>/exames/chart/<titulo>', methods=['GET'])
def gerar_dados_grafico_exame(paciente_id, titulo):
    """Gerar dados para gráfico de evolução de exames numéricos"""
    try:
        # Buscar todos os exames numéricos do paciente com o título especificado
        exames = Exame.query.filter_by(
            paciente_id=paciente_id,
            tipo_exame='numerico',
            titulo=titulo
        ).order_by(Exame.data_exame).all()

        if not exames:
            return jsonify({"error": "Nenhum exame encontrado com este título"}), 404

        # Preparar dados para o gráfico
        dados_grafico = []
        unidade = None

        for exame in exames:
            if exame.valor is not None:
                try:
                    valor_numerico = float(exame.valor)
                    dados_grafico.append({
                        'data': exame.data_exame.strftime('%Y-%m-%d'),
                        'valor': valor_numerico,
                        'data_obj': exame.data_exame.isoformat()
                    })

                    # Capturar unidade do primeiro exame que tiver
                    if not unidade and exame.unidade:
                        unidade = exame.unidade

                except (ValueError, TypeError):
                    continue  # Pular valores não numéricos

        if not dados_grafico:
            return jsonify({"error": "Nenhum valor numérico válido encontrado"}), 404

        # Ordenar por data
        dados_grafico.sort(key=lambda x: x['data_obj'])

        return jsonify({
            'titulo': titulo,
            'unidade': unidade or '',
            'dados': dados_grafico,
            'total_pontos': len(dados_grafico)
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao gerar dados do gráfico: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# Rota para listar exames numéricos disponíveis para gráfico
@exames_bp.route('/pacientes/<int:paciente_id>/exames/chartable', methods=['GET'])
def listar_exames_chartable(paciente_id):
    """Listar títulos de exames numéricos disponíveis para gráfico"""
    try:
        # Buscar exames numéricos únicos por título
        exames = db.session.query(Exame.titulo, Exame.unidade).filter_by(
            paciente_id=paciente_id,
            tipo_exame='numerico'
        ).distinct().all()

        exames_chartable = []
        for titulo, unidade in exames:
            # Verificar se há pelo menos 2 exames para fazer gráfico
            count = Exame.query.filter_by(
                paciente_id=paciente_id,
                tipo_exame='numerico',
                titulo=titulo
            ).count()

            if count >= 2:
                exames_chartable.append({
                    'titulo': titulo,
                    'unidade': unidade or '',
                    'total_exames': count
                })

        return jsonify({
            'exames_chartable': exames_chartable
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames chartable: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

# Rota para processar OCR em imagens de exames
@exames_bp.route('/exames/<int:exame_id>/ocr', methods=['POST'])
def processar_ocr_exame(exame_id):
    exame = Exame.query.get_or_404(exame_id)

    if exame.tipo_exame != 'arquivo':
        return jsonify({"error": "OCR só pode ser aplicado em exames do tipo arquivo"}), 400

    # Obter imagens do exame
    imagens = ExameImagem.query.filter_by(exame_id=exame_id).all()

    if not imagens:
        return jsonify({"error": "Nenhuma imagem encontrada para este exame"}), 400

    resultados_ocr = []

    for imagem in imagens:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER_EXAMES'], imagem.arquivo_caminho)

        # Verificar se já existe resultado OCR para esta imagem
        ocr_existente = OCRResultado.query.filter_by(exame_imagem_id=imagem.id).first()

        if ocr_existente:
            # Retornar resultado existente
            resultados_ocr.append({
                'imagem_id': imagem.id,
                'arquivo_nome': imagem.arquivo_nome,
                'status': ocr_existente.status_processamento,
                'texto_extraido': ocr_existente.texto_extraido if ocr_existente.status_processamento == 'concluido' else None,
                'dados_estruturados': ocr_existente.dados_estruturados if ocr_existente.status_processamento == 'concluido' else None,
                'confianca': ocr_existente.confianca if ocr_existente.status_processamento == 'concluido' else None,
                'ja_processado': True
            })
            continue

        if os.path.exists(filepath):
            try:
                # Criar registro OCR inicial
                ocr_resultado = OCRResultado(
                    exame_imagem_id=imagem.id,
                    status_processamento='processando'
                )
                db.session.add(ocr_resultado)
                db.session.commit()

                # Processar OCR usando o serviço real
                try:
                    ocr_result = ocr_service.process_exam_image(filepath)
                    
                    if ocr_result.get('status') == 'concluido':
                        # Atualizar registro com resultados reais
                        ocr_resultado.texto_extraido = ocr_result['texto_extraido']
                        ocr_resultado.dados_estruturados = ocr_result['dados_estruturados']
                        ocr_resultado.confianca = ocr_result['confianca']
                        ocr_resultado.status_processamento = 'concluido'
                    else:
                        ocr_resultado.erro_processamento = f"Erro no OCR: {ocr_result.get('erro', 'Erro desconhecido')}"
                        ocr_resultado.status_processamento = 'erro'
                        
                except Exception as e:
                    ocr_resultado.erro_processamento = f'Erro no processamento OCR: {str(e)}'
                    ocr_resultado.status_processamento = 'erro'

                ocr_resultado.processado_em = datetime.utcnow()
                db.session.commit()

                resultados_ocr.append({
                    'imagem_id': imagem.id,
                    'arquivo_nome': imagem.arquivo_nome,
                    'status': ocr_resultado.status_processamento,
                    'texto_extraido': ocr_resultado.texto_extraido,
                    'dados_estruturados': ocr_resultado.dados_estruturados,
                    'confianca': ocr_resultado.confianca,
                    'ja_processado': False
                })

            except Exception as e:
                # Atualizar status de erro se houver
                if 'ocr_resultado' in locals():
                    ocr_resultado.status_processamento = 'erro'
                    ocr_resultado.erro_processamento = str(e)
                    ocr_resultado.processado_em = datetime.utcnow()
                    db.session.commit()

                resultados_ocr.append({
                    'imagem_id': imagem.id,
                    'arquivo_nome': imagem.arquivo_nome,
                    'erro': str(e),
                    'status': 'erro',
                    'ja_processado': False
                })
        else:
            resultados_ocr.append({
                'imagem_id': imagem.id,
                'arquivo_nome': imagem.arquivo_nome,
                'erro': 'Arquivo não encontrado',
                'status': 'erro',
                'ja_processado': False
            })

    return jsonify({
        'exame_id': exame_id,
        'resultados_ocr': resultados_ocr,
        'total_imagens': len(imagens),
        'processadas': len([r for r in resultados_ocr if r['status'] == 'concluido'])
    })

# Rota para obter nomes de exames únicos para autocomplete
@exames_bp.route('/exames/nomes-unicos', methods=['GET'])
def obter_nomes_exames_unicos():
    """Retorna lista de nomes únicos de exames para autocomplete"""
    try:
        # Buscar nomes únicos de exames ordenados por frequência de uso
        nomes_exames = db.session.query(
            Exame.titulo,
            db.func.count(Exame.titulo).label('frequencia')
        ).filter(
            Exame.titulo.isnot(None),
            Exame.titulo != ''
        ).group_by(Exame.titulo).order_by(
            db.desc('frequencia'),
            Exame.titulo
        ).all()

        # Formatar resposta
        exames_formatados = []
        for titulo, frequencia in nomes_exames:
            exames_formatados.append({
                'titulo': titulo,
                'frequencia': frequencia
            })

        return jsonify({
            'exames': exames_formatados
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao obter nomes de exames únicos: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500
