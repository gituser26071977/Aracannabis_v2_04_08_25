from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Prescricao
from services.prescription_service import PrescriptionService
from routes.auth_decorators import require_permission
from araos.platform.identity.permissions import Permission
import os

prescricoes_bp = Blueprint('prescricoes', __name__)
service = PrescriptionService()


@prescricoes_bp.route('/gerar-base', methods=['POST'])
@jwt_required()
@require_permission(Permission.PRESCRIPTION_WRITE)
def gerar_prescricao_base():
    """Gera receituário base (prontuário clínico geral).

    Aceita medicamentos livres com posologia textual — sem depender de
    dosagens canaboides. Usado pelo módulo base (todas as especialidades).
    """
    data = request.get_json() or {}
    profissional_id = get_jwt_identity()
    paciente_id = data.get('paciente_id')
    observacoes = data.get('observacoes', '')
    medicamentos = data.get('medicamentos', []) or []

    if not paciente_id:
        return jsonify({'error': 'paciente_id é obrigatório'}), 400

    try:
        prescricao = service.gerar_prescricao_pdf(
            profissional_id=profissional_id,
            paciente_id=paciente_id,
            observacoes=observacoes,
            medicamentos_livres=medicamentos,
        )
        return jsonify({
            'success': True,
            'message': 'Receituário gerado com sucesso',
            'data': prescricao.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar receituário base: {e}")
        return jsonify({'error': str(e)}), 500


@prescricoes_bp.route('/gerar', methods=['POST'])
@jwt_required()
@require_permission(Permission.PRESCRIPTION_WRITE)
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

        # F2 — wrap: emite Clinical Event canônico (nunca bloqueia o fluxo)
        try:
            from models import Paciente
            from services.araos_event_emitter import default_emitter

            paciente = Paciente.query.get(paciente_id)
            default_emitter().emit(
                event_type="PRESCRIPTION_ISSUED",
                patient_id=paciente_id,
                tenant_id=str(paciente.associacao_id or "default") if paciente else "default",
                source_id=prescricao.id if hasattr(prescricao, "id") else None,
                payload={
                    "prescricao_id": prescricao.id if hasattr(prescricao, "id") else None,
                    "paciente_id": paciente_id,
                    "n_medicamentos": len(dosagens_ids),
                    "data_emissao": (
                        prescricao.data_emissao.strftime("%Y-%m-%d")
                        if hasattr(prescricao, "data_emissao") and prescricao.data_emissao
                        else None
                    ),
                },
                metadata={"professional_id": str(profissional_id)},
            )
        except Exception as exc:  # noqa: BLE001 — wrap nunca quebra o fluxo
            current_app.logger.warning("prescricao_event_emit_failed: %s", exc)

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
