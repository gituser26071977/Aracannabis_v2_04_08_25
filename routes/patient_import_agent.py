import os
import re
import json
import logging
import base64
import shutil
import threading
import uuid
import zipfile
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
import pytesseract
from PIL import Image
import pdf2image
from services.ai_agents import ai_manager

# Configurar logger
logger = logging.getLogger(__name__)

patient_import_bp = Blueprint('patient_import', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'zip'}

# In-memory Job Store (Simples para esta instância)
IMPORT_JOBS = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang='por')
    except Exception as e:
        logger.error(f"Erro no OCR: {str(e)}")
        return ""

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        # Converter PDF para imagens
        images = pdf2image.convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img, lang='por') + "\n"
    except Exception as e:
        logger.error(f"Erro no OCR PDF: {str(e)}")
        # Fallback ou erro
    return text

def parse_patient_data_regex(text):
    """
    Tenta extrair dados do paciente usando Regex (Heurística)
    """
    data = {}
    
    # Normalizar texto
    text_clean = text.replace('\n', ' ').replace('  ', ' ')
    
    # Nome
    nome_match = re.search(r'(?:Nome|Paciente|Para):\s*([A-Za-zÀ-ÖØ-öø-ÿ\s]+)', text, re.IGNORECASE)
    if nome_match:
        data['nome'] = nome_match.group(1).strip()
    
    # CPF
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text)
    if cpf_match:
        data['cpf'] = cpf_match.group(0)
        
    # Data de Nascimento
    nasc_match = re.search(r'(?:Nasc\.?|Nascimento|D\.N\.?):\s*(\d{2}/\d{2}/\d{4})', text_clean, re.IGNORECASE)
    if not nasc_match:
         nasc_match = re.search(r'(\d{2}/\d{2}/\d{4})', text) 
    
    if nasc_match:
        try:
            data['data_nascimento'] = datetime.strptime(nasc_match.group(1), '%d/%m/%Y').strftime('%Y-%m-%d')
        except:
            pass

    # Diagnóstico / CID
    cid_match = re.search(r'(?:CID|H.D.|Diagnóstico):\s*([A-Z]\d{2}(?:\.\d)?)', text, re.IGNORECASE)
    if cid_match:
        data['diagnostico'] = f"CID {cid_match.group(1)}"
        
    # Medicamentos
    medicamentos = []
    keywords = ['Cannabis', 'CBD', 'THC', 'Óleo', 'Extrato', 'Canabidiol']
    for line in text.split('\n'):
        if any(key in line for key in keywords):
            medicamentos.append(line.strip())
            
    if medicamentos:
        data['observacoes'] = "Possível prescrição: " + "; ".join(medicamentos)
        
    return data

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_document_with_ai(image_path):
    """
    Envia a imagem para o AI Manager para extração inteligente usando o modelo configurado
    """
    prompt = """
    Você é um assistente médico administrativo especializado em digitalizar documentos médicos (receitas, laudos, identidades).
    Analise esta imagem com extrema atenção e extraia todos os dados disponíveis para cadastro do paciente.
    
    Campos de interesse:
    1. Dados Pessoais: Nome completo, CPF, RG, Data de Nascimento, Endereço completo, Telefone, Email.
    2. Dados Médicos: Diagnóstico principal, CID, Associação de Pacientes (ex: ABRACE, AMA+MA, etc).
    3. Prescrição: Lista de medicamentos, óleos ou extratos com nome, concentração e posologia (gotas, frequência).

    Retorne APENAS um objeto JSON válido neste formato:
    {
      "nome": "Nome completo",
      "data_nascimento": "YYYY-MM-DD",
      "cpf": "000.000.000-00",
      "rg": "Número do RG (se disponível)",
      "endereco": "Endereço completo",
      "telefone": "Telefone de contato",
      "email": "Email de contato",
      "associacao": "Nome da Associação",
      "diagnostico": "Descrição do diagnóstico e CID",
      "medicamentos": [
        {
          "nome": "Nome do medicamento",
          "concentracao": "Ex: 50mg/ml",
          "posologia": "Ex: 5 gotas 2x ao dia",
          "frequencia_diaria": 2,
          "dose_quantidade": 5
        }
      ],
      "observacoes": "Outros detalhes relevantes",
      "confianca": 0-100 // Sua estimativa de precisão na extração
    }

    Se algum campo não estiver visível, use null. Não invente dados. 
    Se a imagem for de um documento de identidade, foque nos dados pessoais.
    Se for uma receita, foque no nome, diagnóstico e medicamentos.
    """

    try:
        # Codificar imagem em base64
        with open(image_path, "rb") as image_file:
            b64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Usar o ai_manager que centraliza as chamadas a LLMs (Ollama, OpenAI, Gemini, etc)
        # Tenta usar o provedor multimodal configurado
        response = ai_manager.vision_completion(
            prompt=prompt,
            image_data=b64_image,
            provider=ai_manager.default_multimodal_provider,
            model=ai_manager.default_multimodal_model
        )
        
        response_text = response.get('content', '')
        
        try:
            # Tentar extrair JSON de blocos de código se existirem
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1).strip()
            else:
                cleaned_text = response_text.strip()
                
            data = json.loads(cleaned_text)
            
            if not data.get('nome'): 
                 return None
            
            data['metodo_analise'] = f"IA_{response.get('provider')}_{response.get('model')}"
            return data
        except json.JSONDecodeError:
            logger.error(f"Erro ao decodificar JSON da IA: {response_text}")
            return None
            
    except Exception as e:
        logger.error(f"Falha na análise via AI Manager: {str(e)}")
        return None

def process_single_file(file_path, original_filename):
    """Lógica isolada de processamento de 1 arquivo"""
    try:
        image_for_analysis = file_path
        
        if original_filename.lower().endswith('.pdf'):
            try:
                images = pdf2image.convert_from_path(file_path, first_page=1, last_page=1)
                if images:
                    image_path_jpg = file_path + ".jpg"
                    images[0].save(image_path_jpg, 'JPEG')
                    image_for_analysis = image_path_jpg
            except Exception as e:
                logger.error(f"Erro ao converter PDF: {e}")
        
        extracted_data = analyze_document_with_ai(image_for_analysis)
        
        # Limpar jpg temporário
        if original_filename.lower().endswith('.pdf') and image_for_analysis != file_path:
             if os.path.exists(image_for_analysis):
                os.remove(image_for_analysis)

        if not extracted_data:
            text = ""
            if original_filename.lower().endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            else:
                text = extract_text_from_image(file_path)
            
            extracted_data = parse_patient_data_regex(text)
            extracted_data['metodo_analise'] = 'OCR_REGEX'
        
        extracted_data['temp_file_path'] = os.path.basename(file_path) # Usar nome do arquivo no disco
        extracted_data['original_filename'] = original_filename
        
        return extracted_data
    except Exception as e:
        logger.error(f"Erro process single file: {e}")
        return {
            'nome': '', 
            'observacoes': f'Erro na análise: {str(e)}',
            'original_filename': original_filename,
            'temp_file_path': os.path.basename(file_path)
        }

def process_zip_background(job_id, zip_path, temp_dir):
    """Processa ZIP em background e atualiza status no IMPORT_JOBS"""
    job = IMPORT_JOBS[job_id]
    extract_path = os.path.join(temp_dir, f"ext_{job_id}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
            
        # Listar todos arquivos validos primeiro para saber o total
        files_to_process = []
        for root, dirs, files in os.walk(extract_path):
            for f in files:
                if allowed_file(f) and not f.lower().endswith('.zip'):
                    files_to_process.append(os.path.join(root, f))
        
        job['total'] = len(files_to_process)
        job['status'] = 'processing'
        
        logging.info(f"JOB {job_id}: Iniciando processamento de {job['total']} arquivos.")
        
        for full_path in files_to_process:
            filename = os.path.basename(full_path)
            try:
                # Processar
                res = process_single_file(full_path, filename)
                if res:
                    job['results'].append(res)
            except Exception as e:
                logger.error(f"Erro processando {filename}: {e}")
                job['errors'].append(f"{filename}: {str(e)}")
            
            job['processed'] += 1
            
        job['status'] = 'completed'
        
    except Exception as e:
        logger.error(f"Erro fatal no job {job_id}: {e}")
        job['status'] = 'failed'
        job['error'] = str(e)
    finally:
        pass

@patient_import_bp.route('/analyze', methods=['POST'])
@jwt_required()
def analyze_document():
    logger.info("Recebida requisição de análise.")
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_base = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        temp_dir = os.path.join(upload_base, 'temp_import')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        temp_path = os.path.join(temp_dir, unique_filename)
        
        logger.info(f"Salvando arquivo {filename} em {temp_path}")
        file.save(temp_path)
        
        if filename.lower().endswith('.zip'):
            logger.info("Arquivo ZIP detectado. Iniciando job async.")
            # Iniciar processamento ASSÍNCRONO
            job_id = str(uuid.uuid4())
            IMPORT_JOBS[job_id] = {
                'id': job_id,
                'status': 'pending',
                'processed': 0,
                'total': 0,
                'results': [],
                'errors': [],
                'created_at': datetime.now().isoformat()
            }
            
            thread = threading.Thread(target=process_zip_background, args=(job_id, temp_path, temp_dir))
            thread.daemon = True # Morre se o processo principal morrer
            thread.start()
            
            return jsonify({
                'success': True,
                'is_async': True,
                'job_id': job_id,
                'message': 'Processamento em background iniciado'
            })
            
        else:
             logger.info("Arquivo único (não-ZIP). Processando sync.")
             # Arquivo único SÍNCRONO (mantendo compatibilidade)
             res = process_single_file(temp_path, filename)
             return jsonify({
                'success': True,
                'is_batch': False,
                'data': res
            })

    logger.error(f"Arquivo não permitido: {file.filename}")
    return jsonify({'error': 'Tipo de arquivo inválido'}), 400

@patient_import_bp.route('/status/<job_id>', methods=['GET'])
@jwt_required()
def check_job_status(job_id):
    job = IMPORT_JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'Job não encontrado'}), 404
    return jsonify(job)


@patient_import_bp.route('/batch-create', methods=['POST'])
@jwt_required()
def batch_create_patients():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    patients_data = data.get('patients', [])
    created_count = 0
    errors = []
    
    upload_base = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
    temp_dir = os.path.join(upload_base, 'temp_import')
    
    for pt in patients_data:
        try:
            if not pt.get('nome'):
                errors.append("Paciente sem nome ignorado.")
                continue
                
            dt_nasc = None
            if pt.get('data_nascimento'):
                try:
                    dt_nasc = datetime.strptime(pt.get('data_nascimento'), '%Y-%m-%d').date()
                except:
                    pass
            
            if not dt_nasc:
                dt_nasc = datetime(2000, 1, 1).date() 

            new_patient = Paciente(
                nome=pt.get('nome'),
                cpf=pt.get('cpf'),
                data_nascimento=dt_nasc,
                profissional_responsavel_id=current_user_id,
                diagnostico=pt.get('diagnostico', 'Aguardando avaliação'),
                endereco=pt.get('endereco'),
                telefone=pt.get('telefone'),
                email=pt.get('email'),
                observacoes=f"Importado via Agente Cadastrador ({pt.get('metodo_analise', 'Unknown')}). {pt.get('observacoes', '')}",
                created_at=datetime.utcnow(),
                associacao_id=pt.get('associacao_id') 
            )
            
            db.session.add(new_patient)
            db.session.flush() 
            
            # --- Processar Medicamentos ---
            medicamentos = pt.get('medicamentos', [])
            if medicamentos:
                for med in medicamentos:
                    nome_med = med.get('nome', 'Medicamento Desconhecido')
                    freq = int(med.get('frequencia_diaria') or 1)
                    try:
                       dose = int(med.get('dose_quantidade') or 0)
                    except:
                       dose = 0
                    conc_str = med.get('concentracao', '')
                    
                    # 1. Criar Dosagem
                    nova_dosagem = Dosagem(
                        paciente_id=new_patient.id,
                        data=datetime.now().date(),
                        dosagem=f"{nome_med} ({conc_str})", # Nome composto
                        gotas=dose,
                        frequencia_diaria=freq,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(nova_dosagem)
                    
                    # 2. Verificar/Criar Produto
                    prod_existente = Produto.query.filter(Produto.nome.ilike(nome_med)).first()
                    if not prod_existente:
                        novo_produto = Produto(
                            nome=nome_med,
                            descricao=f"Importado automaticamente. Concentração: {conc_str}",
                            tipo='oleo', 
                            ativo=True,
                            data_registro=datetime.now().date(),
                            created_at=datetime.utcnow()
                        )
                        db.session.add(novo_produto)
            
            # Mover arquivo
            temp_filename = pt.get('temp_file_path')
            if temp_filename:
                src_path = os.path.join(temp_dir, temp_filename)
                if os.path.exists(src_path):
                    exame = Exame(
                        paciente_id=new_patient.id,
                        profissional_id=current_user_id,
                        data_exame=datetime.now().date(),
                        tipo_exame='arquivo',
                        titulo='Prescrição Original',
                        descricao='Documento importado via Agente Cadastrador',
                        created_at=datetime.utcnow()
                    )
                    db.session.add(exame)
                    db.session.flush()
                    
                    dest_path = os.path.join(upload_base, temp_filename)
                    shutil.move(src_path, dest_path)
                    
                    exame_img = ExameImagem(
                        exame_id=exame.id,
                        arquivo_nome=temp_filename,
                        arquivo_caminho=temp_filename,
                        laudo=f"Documento original importado em {datetime.now().strftime('%d/%m/%Y')}",
                        created_at=datetime.utcnow()
                    )
                    db.session.add(exame_img)
            
            created_count += 1
            
        except Exception as e:
            errors.append(f"Erro ao criar {pt.get('nome', 'Desconhecido')}: {str(e)}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao salvar lote no banco: {str(e)}'}), 500
        
    return jsonify({
        'success': True,
        'created_count': created_count,
        'errors': errors
    })
