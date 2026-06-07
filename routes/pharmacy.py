from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Profissional
from models_extra import InventoryItem, PharmacyDispense, create_audit_entry
from datetime import datetime

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/api/pharmacy')


def get_current_profissional():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return None
    return Profissional.query.get(int(current_user_id))


@pharmacy_bp.route('/dispense', methods=['POST'])
@jwt_required()
def dispense_prescription():
    """Dispensa medicamentos a partir de uma prescrição.
    Body: { prescricao_id (optional), itens: [ {produto_id, quantidade, lote (optional)} ], observacoes }
    """
    user = get_current_profissional()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json() or {}
    prescricao_id = data.get('prescricao_id')
    itens = data.get('itens') or []
    observacoes = data.get('observacoes')

    if not itens or not isinstance(itens, list):
        return jsonify({'error': 'itens é obrigatório e deve ser uma lista'}), 400

    tenant_id = getattr(user, 'tenant_id', None)

    # Begin transaction
    try:
        dispensed_items = []

        for it in itens:
            produto_id = it.get('produto_id')
            qty = int(it.get('quantidade', 0))
            lote = it.get('lote')

            if qty <= 0:
                return jsonify({'error': 'quantidade deve ser > 0'}), 400

            # Try to find inventory items for this produto (and lote if provided)
            query = InventoryItem.query.filter_by(produto_id=produto_id)
            if tenant_id is not None:
                query = query.filter_by(tenant_id=tenant_id)
            if lote:
                query = query.filter_by(lote=lote)

            # Order by validade asc to use earliest expiry first
            inv = query.order_by(InventoryItem.validade.asc().nulls_last()).all()

            remaining = qty
            used = []

            for slot in inv:
                if remaining <= 0:
                    break
                take = min(remaining, slot.quantidade)
                if take <= 0:
                    continue
                slot.quantidade = slot.quantidade - take
                slot.updated_at = datetime.utcnow()
                remaining -= take
                used.append({'inventory_item_id': slot.id, 'produto_id': produto_id, 'quantidade': take, 'lote': slot.lote})

            if remaining > 0:
                # rollback and return error: insufficient stock
                db.session.rollback()
                return jsonify({'error': f'Estoque insuficiente para produto {produto_id}. falta {remaining}'}), 400

            dispensed_items.extend(used)

        # If all items available, persist inventory updates
        db.session.commit()

        # Create PharmacyDispense record
        pd = PharmacyDispense(
            prescricao_id=prescricao_id,
            tenant_id=tenant_id,
            dispensado_por=user.id,
            itens=dispensed_items,
            observacoes=observacoes,
            data_dispensacao=datetime.utcnow()
        )
        db.session.add(pd)
        db.session.commit()

        # Audit entry
        try:
            create_audit_entry(tenant_id=tenant_id, user_id=user.id, action='pharmacy_dispense', resource_type='pharmacy_dispenses', resource_id=pd.id, details={'prescricao_id': prescricao_id, 'itens': dispensed_items})
        except Exception:
            db.session.rollback()

        return jsonify({'pharmacy_dispense': pd.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao processar dispensa: {str(e)}'}), 500
