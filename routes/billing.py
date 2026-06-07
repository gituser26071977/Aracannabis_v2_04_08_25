from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Plano, Assinatura, Fatura, Profissional
from services.billing_service import billing_service
from services.billing_service_v2 import billing_service_v2
from services.payment_service import payment_service
from services.feature_flag_service import FeatureFlagService

billing_bp = Blueprint('billing', __name__)


def admin_required():
    current_user_id = int(get_jwt_identity())
    profissional = Profissional.query.get(current_user_id)
    if not profissional or profissional.role not in ['admin', 'superadmin']:
        return False
    return True


@billing_bp.route('/plans', methods=['GET'])
@jwt_required()
def listar_planos():
    planos = Plano.query.filter_by(ativo=True).order_by(Plano.preco_mensal.asc()).all()
    return jsonify({'planos': [p.to_dict() for p in planos]})


@billing_bp.route('/plans', methods=['POST'])
@jwt_required()
def criar_plano():
    if not admin_required():
        return jsonify({'error': 'Acesso negado'}), 403
    data = request.get_json() or {}
    required = ['nome', 'preco_mensal']
    if not all(field in data for field in required):
        return jsonify({'error': f'Campos obrigatórios: {required}'}), 400
    plano = Plano(
        nome=data['nome'],
        descricao=data.get('descricao'),
        preco_mensal=float(data['preco_mensal']),
        limite_pacientes=data.get('limite_pacientes', 0),
        limite_agentes_ia=data.get('limite_agentes_ia'),
        limite_armazenamento_mb=data.get('limite_armazenamento_mb', 5120),
        ativo=True
    )
    db.session.add(plano)
    db.session.commit()
    return jsonify({'plano': plano.to_dict()}), 201


@billing_bp.route('/subscribe', methods=['POST'])
@jwt_required()
def assinar_plano():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    plano_id = data.get('plano_id')
    metodo = data.get('metodo', 'pix')
    periodicidade = data.get('periodicidade', 'mensal')

    if not plano_id:
        return jsonify({'error': 'plano_id é obrigatório'}), 400

    # Feature flag new_billing_v2
    if FeatureFlagService.is_enabled('new_billing_v2'):
        result = billing_service_v2.criar_assinatura(
            current_user_id, plano_id, metodo, periodicidade
        )
    else:
        result = billing_service.criar_assinatura(current_user_id, plano_id, metodo)

    if result.get('error'):
        return jsonify(result), 400
    return jsonify(result), 201


@billing_bp.route('/invoices', methods=['GET'])
@jwt_required()
def listar_faturas():
    current_user_id = int(get_jwt_identity())

    if FeatureFlagService.is_enabled('new_billing_v2'):
        faturas = billing_service_v2.listar_faturas_profissional(current_user_id)
        return jsonify({'faturas': faturas})

    assinaturas_ids = [a.id for a in Assinatura.query.filter_by(profissional_id=current_user_id).all()]
    faturas = Fatura.query.filter(Fatura.assinatura_id.in_(assinaturas_ids)).order_by(Fatura.created_at.desc()).all()
    return jsonify({'faturas': [f.to_dict() for f in faturas]})


@billing_bp.route('/invoices/<int:fatura_id>/pay', methods=['POST'])
@jwt_required()
def pagar_fatura(fatura_id):
    if FeatureFlagService.is_enabled('new_billing_v2'):
        result = billing_service_v2.pagar_fatura(fatura_id)
    else:
        result = billing_service.pagar_fatura(fatura_id)

    if result.get('error'):
        return jsonify(result), 404
    return jsonify(result), 200


@billing_bp.route('/payments/<string:cobranca_id>', methods=['GET'])
@jwt_required()
def status_pagamento(cobranca_id):
    try:
        return jsonify(payment_service.get_status(cobranca_id))
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@billing_bp.route('/payments/<string:cobranca_id>/status', methods=['PUT'])
@jwt_required()
def atualizar_status_pagamento(cobranca_id):
    if not admin_required():
        return jsonify({'error': 'Acesso negado'}), 403
    data = request.get_json() or {}
    status = data.get('status')
    if not status:
        return jsonify({'error': 'status é obrigatório'}), 400
    try:
        return jsonify(payment_service.update_status(cobranca_id, status))
    except Exception as e:
        return jsonify({'error': str(e)}), 404


# --- Novos endpoints v2 ---

@billing_bp.route('/subscription/<int:assinatura_id>/cancel', methods=['POST'])
@jwt_required()
def cancelar_assinatura(assinatura_id):
    if not FeatureFlagService.is_enabled('new_billing_v2'):
        return jsonify({'error': 'Feature new_billing_v2 desativada'}), 403
    result = billing_service_v2.cancelar_assinatura(assinatura_id)
    if result.get('error'):
        return jsonify(result), 400
    return jsonify(result), 200


@billing_bp.route('/providers', methods=['GET'])
@jwt_required()
def listar_provedores():
    if not FeatureFlagService.is_enabled('multi_payment_provider'):
        return jsonify({'error': 'Feature multi_payment_provider desativada'}), 403
    from services.payment_provider_factory import PaymentProviderFactory
    return jsonify({'providers': PaymentProviderFactory.list_providers()})
