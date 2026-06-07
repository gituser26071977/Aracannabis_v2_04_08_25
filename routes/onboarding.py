from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Profissional
from models_extra import OnboardingProgress
from services.feature_flag_service import FeatureFlagService
import logging

logger = logging.getLogger(__name__)
onboarding_bp = Blueprint('onboarding', __name__)


def _get_or_create_progress(user_id):
    progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
    if not progress:
        progress = OnboardingProgress(user_id=user_id, current_step=1)
        db.session.add(progress)
        db.session.commit()
    return progress


@onboarding_bp.route('/api/onboarding/status', methods=['GET'])
@jwt_required()
def get_status():
    if not FeatureFlagService.is_enabled('onboarding_wizard'):
        return jsonify({'error': 'Feature não disponível'}), 403

    user_id = int(get_jwt_identity())
    profissional = Profissional.query.get(user_id)
    if not profissional:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
    return jsonify({
        'onboarding_required': not profissional.onboarding_completed,
        'onboarding_completed': profissional.onboarding_completed,
        'current_step': progress.current_step if progress else 1,
        'progress': progress.to_dict() if progress else None,
        'user': {
            'id': profissional.id,
            'nome': profissional.nome,
            'email': profissional.email,
            'onboarding_step': profissional.onboarding_step,
            'onboarding_completed': profissional.onboarding_completed,
        }
    }), 200


@onboarding_bp.route('/api/onboarding/step/<int:step_number>', methods=['POST'])
@jwt_required()
def save_step(step_number):
    if not FeatureFlagService.is_enabled('onboarding_wizard'):
        return jsonify({'error': 'Feature não disponível'}), 403

    if step_number < 1 or step_number > 4:
        return jsonify({'error': 'Passo inválido'}), 400

    user_id = int(get_jwt_identity())
    profissional = Profissional.query.get(user_id)
    if not profissional:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json() or {}
    progress = _get_or_create_progress(user_id)

    # Salvar dados do passo específico
    step_data = data.get('data', {})
    if step_number == 1:
        progress.step_1_data = step_data
        # Atualizar profissional com dados pessoais
        if step_data.get('nome'):
            profissional.nome = step_data['nome']
        if step_data.get('cpf'):
            # CPF não existe no modelo Profissional, salvar apenas no progresso
            pass
        if step_data.get('crm'):
            profissional.crm = step_data['crm']
        if step_data.get('uf_crm'):
            profissional.uf_crm = step_data['uf_crm']
        if step_data.get('especialidade'):
            # especialidade não existe diretamente no modelo Profissional
            pass
    elif step_number == 2:
        progress.step_2_data = step_data
    elif step_number == 3:
        progress.step_3_data = step_data
    elif step_number == 4:
        progress.step_4_data = step_data
        progress.completed = True
        profissional.onboarding_completed = True

    # Avançar para o próximo passo (ou manter no atual se for o 4)
    if step_number > progress.current_step:
        progress.current_step = step_number
    if step_number < 4:
        progress.current_step = step_number + 1

    profissional.onboarding_step = progress.current_step

    try:
        db.session.commit()
        return jsonify({
            'message': f'Passo {step_number} salvo com sucesso',
            'current_step': progress.current_step,
            'completed': progress.completed,
            'progress': progress.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar onboarding: {e}")
        return jsonify({'error': f'Erro ao salvar progresso: {str(e)}'}), 500


@onboarding_bp.route('/api/onboarding/skip', methods=['POST'])
@jwt_required()
def skip_onboarding():
    if not FeatureFlagService.is_enabled('onboarding_wizard'):
        return jsonify({'error': 'Feature não disponível'}), 403

    user_id = int(get_jwt_identity())
    profissional = Profissional.query.get(user_id)
    if not profissional:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    profissional.onboarding_completed = True
    progress = OnboardingProgress.query.filter_by(user_id=user_id).first()
    if progress:
        progress.completed = True
        progress.current_step = 4

    try:
        db.session.commit()
        return jsonify({'message': 'Onboarding concluído'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
