from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Prescricao
from services.prescription_service import PrescriptionService
from routes.auth_decorators import require_role
import os

prescricoes_bp = Blueprint('prescricoes', __name__)
service = PrescriptionService()

@prescricoes_bp.route('/gerar', methods=['POST'])
@jwt_required()
@require_role('admin', 'profissional', 'manager', 'superadmin')  # bloqueia secretary
def gerar_prescricao():
    data = request.get_json()
    profissional_id = get_jwt_identity()
    paciente_id = data.get('paciente_id')
    dosagens_ids = data.get('dosagens_ids', []) # Lista de IDs
    novos_medicamentos = data.get('novos_medicamentos', []) # Lista de formatações do AI
    novos_exames = data.get('novos_exames', []) # Lista de exames da AI
    observacoes = data.get('observacoes', '')
    
    from models import db, Dosagem, SolicitacaoExame
    
    # Se existirem novos medicamentos ditados pelo medico, cria as dosagens fisicas antes de gerar impressao
    if novos_medicamentos:
        for med in novos_medicamentos:
            nova_dose = Dosagem(
                paciente_id=paciente_id,
                data=datetime.utcnow().date(),
                dosagem=med.get('nome_medicamento', 'Prescrição AI'),
                via_administracao=med.get('via_administracao', 'Oral'),
                gotas=med.get('gotas_por_dose', 0),
                frequencia_diaria=med.get('frequencia_diaria', 1),
                concentracao_cbd=med.get('concentracao_cbd', 0.0),
                concentracao_thc=med.get('concentracao_thc', 0.0),
                instrucoes_uso=f"Formato: {med.get('posologia_texto', '')} | Rec: {med.get('instrucoes', '')}"
            )
            db.session.add(nova_dose)
            db.session.flush() # obtem o ID
            dosagens_ids.append(nova_dose.id)
        db.session.commit()
        
    # Se existirem novos exames, cria o bloco de solicitacao física
    if novos_exames:
        nova_solicitacao = SolicitacaoExame(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            data_solicitacao=datetime.utcnow(),
            exames_solicitados=novos_exames,
            observacoes="Solicitado via Consultor IA",
            status='pendente'
        )
        db.session.add(nova_solicitacao)
        db.session.commit()
    
    try:
        prescricao = service.gerar_prescricao_pdf(profissional_id, paciente_id, dosagens_ids, observacoes)
        return jsonify({
            'success': True,
            'message': 'Prescrição gerada com sucesso',
            'data': prescricao.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from services.prescription_ai_service import PrescriptionAIService

@prescricoes_bp.route('/assistente', methods=['POST'])
@jwt_required()
@require_role('admin', 'profissional', 'manager', 'superadmin')  # bloqueia secretary
def assistente_prescricao():
    data = request.get_json()
    texto_livre = data.get('texto_livre', '')
    
    # Check if the user has the 'Modo Consultor (IA)' activated
    # Let's fetch it from ConfiguraçãoPrescrição
    from models import ConfiguracaoPrescricao
    profissional_id = get_jwt_identity()
    config = ConfiguracaoPrescricao.query.filter_by(profissional_id=profissional_id).first()
    modo_consultor = config.modo_consultor_ia if config else False
    
    ai_svc = PrescriptionAIService()
    try:
        resultado = ai_svc.process_free_text(texto_livre, modo_consultor)
        return jsonify({
            'success': True,
            'medicamentos': resultado.get('medicamentos', []),
            'exames': resultado.get('exames', []),
            'modo_consultor': modo_consultor
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@prescricoes_bp.route('/paciente/<int:paciente_id>', methods=['GET'])
@jwt_required()
def listar_prescricoes(paciente_id):
    prescricoes = Prescricao.query.filter_by(paciente_id=paciente_id).order_by(Prescricao.data_emissao.desc()).all()
    return jsonify([p.to_dict() for p in prescricoes])

@prescricoes_bp.route('/<code>/download', methods=['GET'])
@jwt_required()
def download_prescricao(id):
    prescricao = Prescricao.query.get_or_404(id)
    # Verificar permissão (profissional responsável ou compartilhado) - MVP skip
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
    file_path = os.path.join(upload_folder, prescricao.arquivo_path)
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=f"Prescricao_{prescricao.data_emissao.strftime('%Y%m%d')}.pdf")
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404
