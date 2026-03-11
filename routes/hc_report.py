from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.hc_report_service import HCReportService
import os

hc_report_bp = Blueprint('hc_report', __name__)
service = HCReportService()

@hc_report_bp.route('/generate', methods=['POST'])
@jwt_required()
def gerar_laudo_hc():
    data = request.get_json()
    profissional_id = get_jwt_identity()
    paciente_id = data.get('paciente_id')
    justificativa = data.get('justificativa_medica') # Opcional, se o médico quiser escrever ele mesmo
    
    if not paciente_id:
        return jsonify({'error': 'ID do paciente é obrigatório'}), 400
        
    try:
        # Gerar PDF
        filename = service.gerar_laudo_hc(profissional_id, paciente_id, justificativa)
        
        # Caminho do arquivo
        upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        return jsonify({
            'success': True,
            'message': 'Laudo de HC gerado com sucesso',
            'filename': filename,
            'url': f'/api/reports/hc/download/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@hc_report_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_laudo(filename):
    upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404
