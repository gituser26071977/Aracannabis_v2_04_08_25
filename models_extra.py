from datetime import datetime
from models import db

# Novas models para suportar inventory, pharmacy dispenses e audit

class UsuarioAssociacao(db.Model):
    __tablename__ = 'usuarios_associacoes'

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False)
    associacao_id = db.Column(db.String(36), db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String, default='member') # 'admin', 'member', 'viewer'
    status = db.Column(db.String, default='active') # 'active', 'suspended', 'pending'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profissional = db.relationship('Profissional', backref='associacoes_vinculadas')
    associacao = db.relationship('Associacao', back_populates='usuarios_vinculados') # Backref in Associacao needs update or use back_populates if defined there, or just simple backref here.
    # Associacao model already has 'membros' and 'estoque', let's stick to simple relationship here or modify Associacao.
    # Associacao definition: `membros = db.relationship('Membro', backref='associacao', lazy=True)`
    # I will rely on this relationship here to access Assoc from UserAssoc.
    
    __table_args__ = (
        db.UniqueConstraint('profissional_id', 'associacao_id', name='uq_profissional_associacao'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'profissional_id': self.profissional_id,
            'associacao_id': self.associacao_id,
            'associacao_nome': self.associacao.nome if self.associacao else None,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id', ondelete='CASCADE'))
    lote = db.Column(db.String(100))
    quantidade = db.Column(db.Integer, default=0, nullable=False)
    localizacao = db.Column(db.String(255))
    validade = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    produto = db.relationship('Produto', backref='inventory_items')

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'lote': self.lote,
            'quantidade': self.quantidade,
            'localizacao': self.localizacao,
            'validade': self.validade.isoformat() if self.validade else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PharmacyDispense(db.Model):
    __tablename__ = 'pharmacy_dispenses'

    id = db.Column(db.Integer, primary_key=True)
    prescricao_id = db.Column(db.Integer, db.ForeignKey('prescricoes.id', ondelete='SET NULL'))
    tenant_id = db.Column(db.Integer, nullable=False)
    dispensado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    itens = db.Column(db.JSON, nullable=False)  # lista de {produto_id, quantidade, lote}
    observacoes = db.Column(db.Text)
    data_dispensacao = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescricao = db.relationship('Prescricao', foreign_keys=[prescricao_id], backref='dispensas')
    profissional = db.relationship('Profissional', foreign_keys=[dispensado_por])

    def to_dict(self):
        return {
            'id': self.id,
            'prescricao_id': self.prescricao_id,
            'tenant_id': self.tenant_id,
            'dispensado_por': self.dispensado_por,
            'dispensador_nome': self.profissional.nome if self.profissional else None,
            'itens': self.itens,
            'observacoes': self.observacoes,
            'data_dispensacao': self.data_dispensacao.isoformat() if self.data_dispensacao else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    action = db.Column(db.String(150), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.String(100))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Profissional', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'user_nome': self.user.nome if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# --- WebhookLog para idempotência e audit ---
class WebhookLog(db.Model):
    __tablename__ = 'webhook_logs'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)  # mercadopago, stripe, asaas
    event_type = db.Column(db.String(100), nullable=False)
    provider_event_id = db.Column(db.String(255), nullable=False, index=True)  # idempotência
    payload = db.Column(db.JSON)
    processed = db.Column(db.Boolean, default=False)
    fatura_id = db.Column(db.Integer, db.ForeignKey('faturas.id'), nullable=True)
    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinaturas.id'), nullable=True)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_event_id', name='uq_webhook_provider_event'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'event_type': self.event_type,
            'provider_event_id': self.provider_event_id,
            'processed': self.processed,
            'fatura_id': self.fatura_id,
            'assinatura_id': self.assinatura_id,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CatalogoImportLog(db.Model):
    __tablename__ = 'catalogo_import_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    detected_count = db.Column(db.Integer, default=0)
    imported_count = db.Column(db.Integer, default=0)
    errors = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Profissional', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_nome': self.user.nome if self.user else None,
            'filename': self.filename,
            'detected_count': self.detected_count,
            'imported_count': self.imported_count,
            'errors': self.errors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(128), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class OnboardingProgress(db.Model):
    __tablename__ = 'onboarding_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False, unique=True)
    current_step = db.Column(db.Integer, default=1, nullable=False)
    steps_data = db.Column(db.JSON, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_step': self.current_step,
            'steps_data': self.steps_data,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Helper para criar entrada de audit log em rotas
def create_audit_entry(tenant_id, user_id, action, resource_type=None, resource_id=None, details=None, ip=None):
    try:
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            ip_address=ip
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception:
        db.session.rollback()
        raise
