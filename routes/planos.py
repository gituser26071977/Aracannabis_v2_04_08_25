from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Plano, Profissional
from functools import wraps

planos_bp = Blueprint('planos', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = Profissional.query.get(current_user_id)
        if not user or user.role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Acesso negado. Requer privilégios de administrador ou superadministrador.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Rota Pública ---

@planos_bp.route('/', methods=['GET'])
def listar_planos_publicos():
    """Lista planos ativos para exibição na página de vendas"""
    planos = Plano.query.filter_by(ativo=True).order_by(Plano.preco_mensal.asc()).all()
    return jsonify([p.to_dict() for p in planos]), 200

# --- Rotas Administrativas ---

@planos_bp.route('/admin', methods=['GET'])
@jwt_required()
@admin_required
def listar_todos_planos():
    """Gestão: Lista todos os planos (ativos e inativos)"""
    planos = Plano.query.order_by(Plano.preco_mensal.asc()).all()
    return jsonify([p.to_dict() for p in planos]), 200

@planos_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required
def criar_plano():
    data = request.get_json()
    
    # Validação básica
    required_fields = ['nome', 'preco_mensal']
    if not all(k in data for k in required_fields):
        return jsonify({'error': 'Campos obrigatórios ausentes'}), 400
        
    novo_plano = Plano(
        nome=data['nome'],
        descricao=data.get('descricao', ''),
        preco_mensal=float(data['preco_mensal']),
        limite_pacientes=int(data.get('limite_pacientes', 50)),
        limite_agentes_ia=int(data.get('limite_agentes_ia', 0)),
        limite_armazenamento_mb=int(data.get('limite_armazenamento_mb', 1024)),
        cor=data.get('cor', '#1976d2'),
        is_popular=bool(data.get('is_popular', False)),
        ativo=bool(data.get('ativo', True))
    )
    
    db.session.add(novo_plano)
    db.session.commit()
    
    return jsonify(novo_plano.to_dict()), 201

@planos_bp.route('/<int:plano_id>', methods=['PUT'])
@jwt_required()
@admin_required
def atualizar_plano(plano_id):
    plano = Plano.query.get_or_404(plano_id)
    data = request.get_json()
    
    if 'nome' in data: plano.nome = data['nome']
    if 'descricao' in data: plano.descricao = data['descricao']
    if 'preco_mensal' in data: plano.preco_mensal = float(data['preco_mensal'])
    if 'limite_pacientes' in data: plano.limite_pacientes = int(data['limite_pacientes'])
    if 'limite_agentes_ia' in data: plano.limite_agentes_ia = int(data['limite_agentes_ia'])
    if 'limite_armazenamento_mb' in data: plano.limite_armazenamento_mb = int(data['limite_armazenamento_mb'])
    if 'cor' in data: plano.cor = data['cor']
    if 'is_popular' in data: plano.is_popular = bool(data['is_popular'])
    if 'ativo' in data: plano.ativo = bool(data['ativo'])
    
    db.session.commit()
    return jsonify(plano.to_dict()), 200

@planos_bp.route('/<int:plano_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def deletar_plano(plano_id):
    """Soft delete (desativar) ou Hard delete se não tiver assinaturas"""
    plano = Plano.query.get_or_404(plano_id)
    
    # Verificar vínculos (futuro: if plano.assinaturas.count() > 0 ...)
    # Por enquanto, apenas desativa para segurança
    plano.ativo = False
    db.session.commit()
    return jsonify({'message': 'Plano desativado com sucesso'}), 200

@planos_bp.route('/init-defaults', methods=['POST'])
@jwt_required()
@admin_required
def seed_planos():
    """Cria os planos padrão se a tabela estiver vazia"""
    if Plano.query.count() > 0:
        return jsonify({'message': 'Planos já existem'}), 200
        
    plano_sem_ia = Plano(
        nome='Plano Sem IA',
        descricao='Prontuário completo sem recursos de IA',
        preco_mensal=99.00,
        limite_pacientes=999999,
        limite_agentes_ia=0,
        cor='#1976d2',
        is_popular=False,
        ativo=True
    )
    
    plano_com_ia = Plano(
        nome='Plano Com IA',
        descricao='Prontuário com recursos de IA assistiva',
        preco_mensal=250.00,
        limite_pacientes=999999,
        limite_agentes_ia=10,
        cor='#2e7d32',
        is_popular=True,
        ativo=True
    )
    
    db.session.add(plano_sem_ia)
    db.session.add(plano_com_ia)
    db.session.commit()

    return jsonify({'message': 'Planos padrão criados com sucesso'}), 201


# --- Plano do usuário autenticado (para gating de features no front) ---
@planos_bp.route('/meu-plano', methods=['GET'])
@jwt_required()
def meu_plano():
    """Retorna o plano do usuário autenticado + assinatura ativa.

    Se o user não tem assinatura (trial), retorna o plano premium como
    default (trial dá acesso a todos os recursos; bloqueio só após expirar).
    """
    from models import Assinatura
    from sqlalchemy import text
    user_id = get_jwt_identity()

    # Admin/superadmin: retorna plano enterprise (acesso total)
    user = Profissional.query.get(user_id)
    if user and user.role in ('admin', 'superadmin'):
        plano = Plano.query.filter_by(slug='enterprise').first() or Plano.query.first()
        return jsonify({
            'plano': plano.to_dict() if plano else None,
            'assinatura': None,
            'is_admin': True,
            'in_trial': False,
        }), 200

    # Query manual para evitar colunas fora de sync com migrations
    row = db.session.execute(
        text("""
            SELECT a.id, a.status, a.trial_ends_at, a.renovacao_em, a.plano_id
            FROM assinaturas a
            WHERE a.profissional_id = :uid
            ORDER BY a.id DESC
            LIMIT 1
        """),
        {"uid": int(user_id)},
    ).first()

    if not row:
        # Sem assinatura: usuário em trial (criou conta mas não assinou)
        # Trial dá acesso a todos os recursos
        plano = Plano.query.filter_by(slug='premium').first() or Plano.query.first()
        return jsonify({
            'plano': plano.to_dict() if plano else None,
            'assinatura': None,
            'is_admin': False,
            'in_trial': True,
        }), 200

    plano = Plano.query.get(row.plano_id) if row.plano_id else None
    return jsonify({
        'plano': plano.to_dict() if plano else None,
        'assinatura': {
            'id': row.id,
            'status': row.status,
            'trial_ends_at': row.trial_ends_at.isoformat() if row.trial_ends_at else None,
            'renovacao_em': row.renovacao_em.isoformat() if row.renovacao_em else None,
        },
        'is_admin': False,
        'in_trial': False,
    }), 200
