from datetime import datetime
from models import db, Profissional, Produto, Prescricoes, Paciente

# Novas models para suportar inventory, pharmacy dispenses e audit

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
    dispensado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    itens = db.Column(db.JSON, nullable=False)  # lista de {produto_id, quantidade, lote}
    observacoes = db.Column(db.Text)
    data_dispensacao = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescricao = db.relationship('Prescricoes', foreign_keys=[prescricao_id], backref='dispensas')
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
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
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
