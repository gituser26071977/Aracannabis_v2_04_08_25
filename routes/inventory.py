from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Profissional, Produto
from models_extra import InventoryItem, create_audit_entry
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')


def get_current_profissional():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return None
    return Profissional.query.get(int(current_user_id))


@inventory_bp.route('/', methods=['GET'])
@jwt_required()
def list_inventory():
    user = get_current_profissional()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tenant_id = getattr(user, 'tenant_id', None)
    if tenant_id is None:
        # fallback: list all items if tenant is not defined (legacy)
        items = InventoryItem.query.order_by(InventoryItem.created_at.desc()).all()
    else:
        items = InventoryItem.query.filter_by(tenant_id=tenant_id).order_by(InventoryItem.created_at.desc()).all()

    return jsonify([i.to_dict() for i in items]), 200


@inventory_bp.route('/', methods=['POST'])
@jwt_required()
def create_inventory_item():
    user = get_current_profissional()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json() or {}
    produto_id = data.get('produto_id')
    quantidade = int(data.get('quantidade', 0))
    lote = data.get('lote')
    localizacao = data.get('localizacao')
    validade = data.get('validade')  # expect YYYY-MM-DD or None

    if not produto_id:
        return jsonify({'error': 'produto_id é obrigatório'}), 400

    produto = Produto.query.get(produto_id)
    if not produto:
        return jsonify({'error': 'Produto não encontrado'}), 404

    tenant_id = getattr(user, 'tenant_id', None)

    item = InventoryItem(
        tenant_id=tenant_id,
        produto_id=produto_id,
        lote=lote,
        quantidade=quantidade,
        localizacao=localizacao,
        validade=(datetime.strptime(validade, '%Y-%m-%d').date() if validade else None)
    )

    try:
        db.session.add(item)
        db.session.commit()

        # audit
        try:
            create_audit_entry(tenant_id=tenant_id, user_id=user.id, action='create_inventory_item', resource_type='inventory_items', resource_id=item.id, details=item.to_dict())
        except Exception:
            db.session.rollback()

        return jsonify({'inventory_item': item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar item de inventário: {str(e)}'}), 500


@inventory_bp.route('/<int:item_id>/adjust', methods=['PATCH'])
@jwt_required()
def adjust_inventory(item_id):
    user = get_current_profissional()
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    data = request.get_json() or {}
    delta = data.get('quantidade_delta')
    if delta is None:
        return jsonify({'error': 'quantidade_delta é obrigatório'}), 400

    try:
        delta = int(delta)
    except ValueError:
        return jsonify({'error': 'quantidade_delta deve ser inteiro'}), 400

    item = InventoryItem.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item de inventário não encontrado'}), 404

    # Optionally check tenant
    tenant_id = getattr(user, 'tenant_id', None)
    if tenant_id is not None and item.tenant_id != tenant_id:
        return jsonify({'error': 'Acesso negado ao item de inventário'}), 403

    try:
        item.quantidade = max(0, item.quantidade + delta)
        item.updated_at = datetime.utcnow()
        db.session.commit()

        # audit
        try:
            create_audit_entry(tenant_id=item.tenant_id, user_id=user.id, action='adjust_inventory_item', resource_type='inventory_items', resource_id=item.id, details={'delta': delta, 'new_quantidade': item.quantidade})
        except Exception:
            db.session.rollback()

        return jsonify({'inventory_item': item.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao ajustar inventário: {str(e)}'}), 500
