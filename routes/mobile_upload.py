import os
import uuid
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, UploadSession

mobile_upload_bp = Blueprint('mobile_upload', __name__)
logger = logging.getLogger(__name__)

# Configuração de upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'mp3', 'wav', 'ogg', 'm4a', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@mobile_upload_bp.route('/mobile/start', methods=['POST'])
def start_session():
    """Inicia uma nova sessão de upload mobile"""
    try:
        data = request.get_json() or {}
        context = data.get('context', 'exam')  # 'exam' or 'product'
        
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=15) # Token válido por 15 minutos
        
        session = UploadSession(
            token=token,
            status='pending',
            context=context,
            expires_at=expires_at
        )
        
        db.session.add(session)
        db.session.commit()
        
        # URL que o celular deve acessar
        # Em produção, deve ser o domínio público. Em dev local, pode ser o IP da máquina.
        upload_url = f"/mobile-upload/{token}" 
        
        return jsonify({
            'token': token,
            'upload_url': upload_url,
            'expires_at': expires_at.isoformat()
        }), 201
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão mobile: {str(e)}")
        return jsonify({'error': 'Erro ao iniciar sessão'}), 500

@mobile_upload_bp.route('/mobile/status/<token>', methods=['GET'])
def check_status(token):
    """Verifica o status da sessão (usado pelo PC via polling)"""
    try:
        session = UploadSession.query.filter_by(token=token).first()
        
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
            
        if session.expires_at < datetime.utcnow():
            return jsonify({'status': 'expired', 'error': 'Sessão expirada'}), 410
            
        response = {
            'status': session.status,
            'created_at': session.created_at.isoformat()
        }
        
        if session.status == 'completed':
            # Se for imagem, pode retornar URL direta para exibição
            # Aqui estamos retornando metadados para o frontend baixar ou exibir
            response['file_url'] = f"/uploads/{os.path.basename(session.file_path)}"
            response['file_type'] = session.file_type
            response['original_filename'] = session.original_filename
            response['context'] = session.context
            if session.ai_result:
                response['ai_result'] = session.ai_result
            
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500

@mobile_upload_bp.route('/mobile/upload/<token>', methods=['POST'])
def upload_file(token):
    """Rota usada pelo celular para enviar o arquivo"""
    try:
        session = UploadSession.query.filter_by(token=token).first()
        
        if not session:
            return jsonify({'error': 'Sessão inválida'}), 404
            
        if session.expires_at < datetime.utcnow():
            return jsonify({'error': 'Sessão expirada'}), 410
            
        if session.status == 'completed':
            return jsonify({'error': 'Sessão já utilizada'}), 400
            
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Adicionar timestamp para evitar colisão
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Usar pasta de uploads configurada no app
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Atualizar sessão
            session.file_path = file_path
            session.file_type = file.content_type
            session.original_filename = filename
            session.status = 'completed'
            db.session.commit()
            
            return jsonify({'message': 'Upload realizado com sucesso!', 'filename': unique_filename}), 200
        else:
            return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
            
    except Exception as e:
        logger.error(f"Erro no upload mobile: {str(e)}")
        return jsonify({'error': f'Erro ao salvar arquivo: {str(e)}'}), 500

@mobile_upload_bp.route('/mobile/process-product/<token>', methods=['POST'])
def process_product(token):
    """Processa produto usando IA após upload mobile"""
    try:
        from services.product_intake import product_intake_service
        
        session = UploadSession.query.filter_by(token=token).first()
        
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
            
        if session.context != 'product':
            return jsonify({'error': 'Sessão não é de produto'}), 400
            
        if not session.file_path or not os.path.exists(session.file_path):
            return jsonify({'error': 'Arquivo não encontrado'}), 404
            
        # Processar com IA
        ia_result = product_intake_service.process_input(
            file_path=session.file_path,
            filename=session.original_filename
        )
        
        # Armazenar resultado na sessão
        session.ai_result = ia_result
        db.session.commit()
        
        return jsonify({
            'message': 'Produto processado com sucesso',
            'produto_sugerido': ia_result.get('produto_sugerido', {}),
            'fonte': ia_result.get('fonte'),
            'texto_processado': ia_result.get('texto_processado')
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar produto: {str(e)}")
        return jsonify({'error': f'Erro ao processar produto: {str(e)}'}), 500
