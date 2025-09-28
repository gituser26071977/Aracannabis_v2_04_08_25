from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Exame, Paciente, Profissional
from datetime import datetime, date
import os
import hashlib
import uuid
from werkzeug.utils import secure_filename
import mimetypes

exames_bp = Blueprint('exames', __name__)

# Configurações de upload
UPLOAD_FOLDER = 'uploads/exames'
ALLOWED_EXTENSIONS = {
    'pdf': ['application/pdf'],
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
    'gif': ['image/gif'],
    'bmp': ['image/bmp'],
    'tiff': ['image/tiff'],
    'webp': ['image/webp'],
    'wep': ['image/wep']  # Adicionado suporte ao formato .wep
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename, mimetype):
    """Verifica se o arquivo é permitido"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False
    
    allowed_mimetypes = ALLOWED_EXTENSIONS[extension]
    # Se for .wep, aceita qualquer mimetype
    if extension == 'wep':
        return True
    return mimetype in allowed_mimetypes

def calculate_file_hash(file_path):
    """Calcula hash MD5 do arquivo"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def ensure_upload_folder():
    """Garante que o diretório de upload existe"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@exames_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_exames_paciente(paciente_id):
    """Lista todos os exames de um paciente"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(paciente_id)
        
        # Buscar exames do paciente
        exames = Exame.query.filter_by(paciente_id=paciente_id).order_by(Exame.data_exame.desc()).all()
        
        return jsonify({
            'success': True,
            'exames': [exame.to_dict() for exame in exames],
            'total': len(exames)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar exames do paciente {paciente_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/', methods=['POST'])
@jwt_required()
def criar_exame():
    """Cria um novo exame com upload de arquivo"""
    try:
        # Verificar se há arquivo no request
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar tamanho do arquivo
        arquivo.seek(0, os.SEEK_END)
        file_size = arquivo.tell()
        arquivo.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False, 
                'error': f'Arquivo muito grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Verificar tipo de arquivo
        mimetype = arquivo.mimetype
        if not allowed_file(arquivo.filename, mimetype):
            return jsonify({
                'success': False, 
                'error': 'Tipo de arquivo não permitido. Permitidos: PDF, JPG, PNG, GIF, BMP, TIFF, WEBP'
            }), 400
        
        # Obter dados do formulário
        data = request.form.to_dict()
        
        # Validar campos obrigatórios
        required_fields = ['paciente_id', 'tipo_exame', 'data_exame']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'Campo obrigatório: {field}'}), 400
        
        # Verificar se o paciente existe
        paciente = Paciente.query.get(data['paciente_id'])
        if not paciente:
            return jsonify({'success': False, 'error': 'Paciente não encontrado'}), 404
        
        # Obter profissional atual
        current_user = get_jwt_identity()
        profissional = Profissional.query.filter_by(usuario=current_user).first()
        
        # Garantir que o diretório de upload existe
        ensure_upload_folder()
        
        # Gerar nome único para o arquivo
        file_extension = arquivo.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Salvar arquivo
        arquivo.save(file_path)
        
        # Calcular hash do arquivo
        file_hash = calculate_file_hash(file_path)
        
        # Converter datas
        try:
            data_exame = datetime.strptime(data['data_exame'], '%Y-%m-%d').date()
        except ValueError:
            os.remove(file_path)  # Remover arquivo se houver erro
            return jsonify({'success': False, 'error': 'Formato de data inválido para data_exame'}), 400
        
        data_resultado = None
        if data.get('data_resultado'):
            try:
                data_resultado = datetime.strptime(data['data_resultado'], '%Y-%m-%d').date()
            except ValueError:
                os.remove(file_path)  # Remover arquivo se houver erro
                return jsonify({'success': False, 'error': 'Formato de data inválido para data_resultado'}), 400
        
        # Criar exame
        exame = Exame(
            paciente_id=int(data['paciente_id']),
            profissional_id=profissional.id if profissional else None,
            tipo_exame=data['tipo_exame'],
            data_exame=data_exame,
            data_resultado=data_resultado,
            observacoes=data.get('observacoes', ''),
            arquivo_nome=arquivo.filename,
            arquivo_path=file_path,
            arquivo_tipo=mimetype,
            arquivo_tamanho=file_size,
            arquivo_hash=file_hash
        )
        
        db.session.add(exame)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exame criado com sucesso',
            'exame': exame.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar exame: {str(e)}")
        
        # Remover arquivo se foi salvo
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/<int:exame_id>', methods=['GET'])
@jwt_required()
def obter_exame(exame_id):
    """Obtém detalhes de um exame específico"""
    try:
        exame = Exame.query.get_or_404(exame_id)
        return jsonify({
            'success': True,
            'exame': exame.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter exame {exame_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/<int:exame_id>', methods=['PUT'])
@jwt_required()
def atualizar_exame(exame_id):
    """Atualiza um exame existente"""
    try:
        exame = Exame.query.get_or_404(exame_id)
        data = request.get_json()
        
        # Atualizar campos permitidos
        if 'tipo_exame' in data:
            exame.tipo_exame = data['tipo_exame']
        
        if 'data_exame' in data:
            try:
                exame.data_exame = datetime.strptime(data['data_exame'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Formato de data inválido para data_exame'}), 400
        
        if 'data_resultado' in data:
            if data['data_resultado']:
                try:
                    exame.data_resultado = datetime.strptime(data['data_resultado'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'success': False, 'error': 'Formato de data inválido para data_resultado'}), 400
            else:
                exame.data_resultado = None
        
        if 'observacoes' in data:
            exame.observacoes = data['observacoes']
        
        exame.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exame atualizado com sucesso',
            'exame': exame.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar exame {exame_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/<int:exame_id>', methods=['DELETE'])
@jwt_required()
def deletar_exame(exame_id):
    """Deleta um exame e seu arquivo"""
    try:
        exame = Exame.query.get_or_404(exame_id)
        
        # Remover arquivo do sistema de arquivos
        if exame.arquivo_path and os.path.exists(exame.arquivo_path):
            os.remove(exame.arquivo_path)
        
        db.session.delete(exame)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exame deletado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao deletar exame {exame_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/<int:exame_id>/download', methods=['GET'])
@jwt_required()
def download_arquivo_exame(exame_id):
    """Faz download do arquivo de um exame"""
    try:
        exame = Exame.query.get_or_404(exame_id)
        
        if not exame.arquivo_path or not os.path.exists(exame.arquivo_path):
            return jsonify({'success': False, 'error': 'Arquivo não encontrado'}), 404
        
        # Verificar integridade do arquivo
        current_hash = calculate_file_hash(exame.arquivo_path)
        if current_hash != exame.arquivo_hash:
            current_app.logger.warning(f"Hash do arquivo {exame_id} não confere. Possível corrupção.")
        
        return send_file(
            exame.arquivo_path,
            as_attachment=True,
            download_name=exame.arquivo_nome,
            mimetype=exame.arquivo_tipo
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro ao fazer download do arquivo do exame {exame_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/tipos', methods=['GET'])
@jwt_required()
def listar_tipos_exames():
    """Lista os tipos de exames disponíveis"""
    tipos_exames = [
        'Hemograma Completo',
        'Glicemia',
        'Colesterol Total',
        'Triglicerídeos',
        'Ureia',
        'Creatinina',
        'TGO/AST',
        'TGP/ALT',
        'Raio-X de Tórax',
        'Raio-X de Coluna',
        'Ultrassonografia Abdominal',
        'Tomografia Computadorizada',
        'Ressonância Magnética',
        'Eletrocardiograma',
        'Ecocardiograma',
        'Endoscopia',
        'Colonoscopia',
        'Mamografia',
        'Papanicolau',
        'Biópsia',
        'Outros'
    ]
    
    return jsonify({
        'success': True,
        'tipos_exames': tipos_exames
    })

@exames_bp.route('/buscar/<int:paciente_id>', methods=['GET'])
@jwt_required()
def buscar_exames(paciente_id):
    """Busca exames de um paciente com filtros"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(paciente_id)
        
        # Obter parâmetros de busca
        termo_busca = request.args.get('q', '').strip()
        tipo_exame = request.args.get('tipo', '').strip()
        data_inicio = request.args.get('data_inicio', '').strip()
        data_fim = request.args.get('data_fim', '').strip()
        
        # Construir query base
        query = Exame.query.filter_by(paciente_id=paciente_id)
        
        # Aplicar filtros
        if termo_busca:
            # Buscar em tipo_exame, observacoes e arquivo_nome
            query = query.filter(
                db.or_(
                    Exame.tipo_exame.ilike(f'%{termo_busca}%'),
                    Exame.observacoes.ilike(f'%{termo_busca}%'),
                    Exame.arquivo_nome.ilike(f'%{termo_busca}%')
                )
            )
        
        if tipo_exame:
            query = query.filter(Exame.tipo_exame == tipo_exame)
        
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(Exame.data_exame >= data_inicio_obj)
            except ValueError:
                return jsonify({'success': False, 'error': 'Formato de data_inicio inválido'}), 400
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(Exame.data_exame <= data_fim_obj)
            except ValueError:
                return jsonify({'success': False, 'error': 'Formato de data_fim inválido'}), 400
        
        # Ordenar por data mais recente
        exames = query.order_by(Exame.data_exame.desc()).all()
        
        return jsonify({
            'success': True,
            'exames': [exame.to_dict() for exame in exames],
            'total': len(exames),
            'filtros_aplicados': {
                'termo_busca': termo_busca,
                'tipo_exame': tipo_exame,
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar exames do paciente {paciente_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@exames_bp.route('/estatisticas/<int:paciente_id>', methods=['GET'])
@jwt_required()
def estatisticas_exames_paciente(paciente_id):
    """Obtém estatísticas dos exames de um paciente"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(paciente_id)
        
        # Contar exames por tipo
        exames = Exame.query.filter_by(paciente_id=paciente_id).all()
        
        tipos_count = {}
        total_exames = len(exames)
        
        for exame in exames:
            tipo = exame.tipo_exame
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
        
        # Exames mais recentes
        exames_recentes = Exame.query.filter_by(paciente_id=paciente_id)\
                                   .order_by(Exame.data_exame.desc())\
                                   .limit(5).all()
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_exames': total_exames,
                'tipos_count': tipos_count,
                'exames_recentes': [exame.to_dict() for exame in exames_recentes]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter estatísticas de exames do paciente {paciente_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
