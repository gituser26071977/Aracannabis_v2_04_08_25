from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Profissional(db.Model):
    __tablename__ = 'profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    crm = db.Column(db.String, unique=True, nullable=False)
    usuario = db.Column(db.String, unique=True, nullable=False)
    senha = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    evolucoes = db.relationship('Evolucao', backref='profissional', lazy=True)
    logs = db.relationship('LogAtividade', backref='profissional', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'crm': self.crm,
            'usuario': self.usuario,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    telefone = db.Column(db.String)
    email = db.Column(db.String)
    em_tratamento = db.Column(db.Boolean, default=False, nullable=False)
    composicao = db.Column(db.String)
    dosagem = db.Column(db.String)
    horarios = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sintomas = db.relationship('Sintoma', backref='paciente', lazy=True, cascade="all, delete-orphan")
    dosagens = db.relationship('Dosagem', backref='paciente', lazy=True, cascade="all, delete-orphan")
    evolucoes = db.relationship('Evolucao', backref='paciente', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'telefone': self.telefone,
            'email': self.email,
            'em_tratamento': self.em_tratamento,
            'composicao': self.composicao,
            'dosagem': self.dosagem,
            'horarios': self.horarios,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Sintoma(db.Model):
    __tablename__ = 'sintomas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    sintoma = db.Column(db.String, nullable=False)
    intensidade = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('paciente_id', 'data', 'sintoma', name='uq_paciente_data_sintoma'),
        db.CheckConstraint('intensidade >= 0 AND intensidade <= 10', name='check_intensidade_range'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'data': self.data.isoformat() if self.data else None,
            'sintoma': self.sintoma,
            'intensidade': self.intensidade,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Dosagem(db.Model):
    __tablename__ = 'dosagens'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    dosagem = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'data': self.data.isoformat() if self.data else None,
            'dosagem': self.dosagem,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Evolucao(db.Model):
    __tablename__ = 'evolucoes'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    data_evolucao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    nota_evolucao = db.Column(db.Text, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'profissional_id': self.profissional_id,
            'data_evolucao': self.data_evolucao.isoformat() if self.data_evolucao else None,
            'nota_evolucao': self.nota_evolucao,
            'profissional_nome': self.profissional.nome if self.profissional else None
        }

class LogAtividade(db.Model):
    __tablename__ = 'logs_atividades'
    
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    acao = db.Column(db.String, nullable=False)
    detalhes = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'profissional_id': self.profissional_id,
            'profissional_nome': self.profissional.nome if self.profissional else None,
            'acao': self.acao,
            'detalhes': self.detalhes,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }
