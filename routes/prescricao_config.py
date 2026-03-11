from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, ConfiguracaoPrescricao, Profissional
import os
from werkzeug.utils import secure_filename
from datetime import datetime

prescricao_config_bp = Blueprint('prescricao_config', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'uploads/logos'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@prescricao_config_bp.route('/', methods=['GET'])
@jwt_required()
def obter_configuracao():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    config = ConfiguracaoPrescricao.query.filter_by(profissional_id=profissional_id).first()
    
    if not config:
        # Retorna config vazia caso não exista
        return jsonify({
            'config': {
                'logo_clinica': None,
                'logo_profissional': None,
                'usar_assinatura_digital': False,
                'modo_consultor_ia': False,
                'cabecalho_personalizado': '',
                'rodape_personalizado': ''
            }
        }), 200

    return jsonify({'config': config.to_dict()}), 200


@prescricao_config_bp.route('/', methods=['POST', 'PUT'])
@jwt_required()
def salvar_configuracao():
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)
    
    config = ConfiguracaoPrescricao.query.filter_by(profissional_id=profissional_id).first()
    if not config:
        config = ConfiguracaoPrescricao(profissional_id=profissional_id)
        db.session.add(config)
        
    # Verificar caminhos
    upload_path = os.path.join(current_app.root_path, '..', UPLOAD_FOLDER)
    os.makedirs(upload_path, exist_ok=True)
    
    # Processar Arquivos (se existirem)
    if 'logo_clinica' in request.files:
        file = request.files['logo_clinica']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"clinica_{profissional_id}_{int(datetime.now().timestamp())}.{file.filename.split('.')[-1]}")
            file.save(os.path.join(upload_path, filename))
            config.logo_clinica = filename

    if 'logo_profissional' in request.files:
        file = request.files['logo_profissional']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"prof_{profissional_id}_{int(datetime.now().timestamp())}.{file.filename.split('.')[-1]}")
            file.save(os.path.join(upload_path, filename))
            config.logo_profissional = filename
            
    # Obter dados string
    # Como FormData manda booleanos como string 'true'/'false'
    def parse_bool(val):
        if not val: return False
        return str(val).lower() in ('true', '1')

    if 'usar_assinatura_digital' in request.form:
        config.usar_assinatura_digital = parse_bool(request.form.get('usar_assinatura_digital'))
        
    if 'modo_consultor_ia' in request.form:
        config.modo_consultor_ia = parse_bool(request.form.get('modo_consultor_ia'))
        
    if 'cabecalho_personalizado' in request.form:
        config.cabecalho_personalizado = request.form.get('cabecalho_personalizado')
        
    if 'rodape_personalizado' in request.form:
        config.rodape_personalizado = request.form.get('rodape_personalizado')
        
    # Se for JSON no PUT sem files (apenas updates textos)
    if request.is_json:
        data = request.json
        if 'usar_assinatura_digital' in data:
            config.usar_assinatura_digital = data['usar_assinatura_digital']
        if 'modo_consultor_ia' in data:
            config.modo_consultor_ia = data['modo_consultor_ia']
        if 'cabecalho_personalizado' in data:
            config.cabecalho_personalizado = data['cabecalho_personalizado']
        if 'rodape_personalizado' in data:
            config.rodape_personalizado = data['rodape_personalizado']

    db.session.commit()
    return jsonify({'config': config.to_dict(), 'message': 'Configuração salva com sucesso!'}), 200

@prescricao_config_bp.route('/logo/<filename>')
def serve_logo(filename):
    upload_path = os.path.join(current_app.root_path, '..', UPLOAD_FOLDER)
    return send_from_directory(upload_path, filename)
