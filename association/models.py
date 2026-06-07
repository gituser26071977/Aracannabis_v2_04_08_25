from datetime import datetime
from models import db

class Associacao(db.Model):
    __tablename__ = 'associacoes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=True) # Nullable for migration, will be enforced later
    cnpj = db.Column(db.String, unique=True, nullable=False)
    endereco = db.Column(db.String)
    telefone = db.Column(db.String)
    email = db.Column(db.String)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    membros = db.relationship('Membro', backref='associacao', lazy=True)
    estoque = db.relationship('Estoque', backref='associacao', lazy=True)
    usuarios_vinculados = db.relationship('UsuarioAssociacao', back_populates='associacao', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'cnpj': self.cnpj,
            'email': self.email,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat()
        }

class Membro(db.Model):
    __tablename__ = 'membros_associacao'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id'), nullable=False)
    
    # Core linkage
    cpf = db.Column(db.String, index=True, nullable=False) # Logical Key
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=True) # Optional physical link
    
    # Profile fields
    nome = db.Column(db.String, nullable=False) # Copied for independence or validation
    data_nascimento = db.Column(db.Date, nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    telefone = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    rg = db.Column(db.String, nullable=True)
    nome_responsavel = db.Column(db.String, nullable=True)  # For minors
    observacoes = db.Column(db.Text, nullable=True)
    
    # Membership info
    data_filiacao = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String, default='ativo') # ativo, suspenso, inativo
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dispensacoes = db.relationship('Dispensacao', backref='membro', lazy=True)
    paciente = db.relationship('Paciente', foreign_keys=[paciente_id])
    documentos = db.relationship('DocumentoMembro', backref='membro', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('associacao_id', 'cpf', name='uq_assoc_cpf'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'cpf': self.cpf,
            'paciente_id': self.paciente_id,
            'paciente_nome': self.paciente.nome if self.paciente else None,
            'nome': self.nome,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'endereco': self.endereco,
            'telefone': self.telefone,
            'email': self.email,
            'rg': self.rg,
            'nome_responsavel': self.nome_responsavel,
            'observacoes': self.observacoes,
            'status': self.status,
            'data_filiacao': self.data_filiacao.isoformat() if self.data_filiacao else None,
            'data_cadastro': self.created_at.isoformat() if self.created_at else None,
            'ativo': True if self.status == 'ativo' else False
        }

class DocumentoMembro(db.Model):
    """Model for storing member documents (prescriptions, reports, exams, etc.)"""
    __tablename__ = 'documentos_membro'
    
    id = db.Column(db.Integer, primary_key=True)
    membro_id = db.Column(db.Integer, db.ForeignKey('membros_associacao.id', ondelete='CASCADE'), nullable=False)
    
    tipo_documento = db.Column(db.String(50), nullable=False)  # 'prescricao', 'exame', 'relatorio', 'laudo', 'outros'
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tamanho = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    conteudo = db.Column(db.LargeBinary)  # Binary content
    
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'membro_id': self.membro_id,
            'tipo_documento': self.tipo_documento,
            'nome_arquivo': self.nome_arquivo,
            'tamanho': self.tamanho,
            'mime_type': self.mime_type,
            'data_upload': self.data_upload.isoformat() if self.data_upload else None,
            'observacoes': self.observacoes
        }

class Estoque(db.Model):
    __tablename__ = 'estoque_associacao'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    
    quantidade = db.Column(db.Integer, default=0, nullable=False)
    lote = db.Column(db.String, nullable=False)
    validade = db.Column(db.Date, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    produto = db.relationship('Produto')

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'quantidade': self.quantidade,
            'lote': self.lote,
            'validade': self.validade.isoformat() if self.validade else None
        }

class Dispensacao(db.Model):
    __tablename__ = 'dispensacoes'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id'), nullable=False)
    membro_id = db.Column(db.Integer, db.ForeignKey('membros_associacao.id'), nullable=False)
    
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_dispensacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    prescricao_id = db.Column(db.Integer, db.ForeignKey('prescricoes.id'), nullable=True) # Optional link to prescription
    observacoes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produto = db.relationship('Produto')
    prescricao = db.relationship('Prescricao')

    def to_dict(self):
        return {
            'id': self.id,
            'membro_id': self.membro_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'quantidade': self.quantidade,
            'data_dispensacao': self.data_dispensacao.isoformat(),
            'observacoes': self.observacoes
        }
