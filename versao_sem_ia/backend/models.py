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
    consultas = db.relationship('Consulta', backref='profissional', lazy=True)
    exames = db.relationship('Exame', backref='profissional', lazy=True)
    
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
    profissional_responsavel_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=False)
    nome = db.Column(db.String, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    cpf = db.Column(db.String)
    genero = db.Column(db.String)
    telefone = db.Column(db.String)
    email = db.Column(db.String)
    endereco = db.Column(db.String)
    diagnostico = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    em_tratamento = db.Column(db.Boolean, default=False, nullable=False)
    composicao = db.Column(db.String)
    dosagem = db.Column(db.String)
    horarios = db.Column(db.String)
    consentimento_lgpd = db.Column(db.Boolean, default=False)
    data_consentimento = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    profissional_responsavel = db.relationship('Profissional', foreign_keys=[profissional_responsavel_id], backref='pacientes_responsavel')
    sintomas = db.relationship('Sintoma', backref='paciente', lazy=True, cascade="all, delete-orphan")
    dosagens = db.relationship('Dosagem', backref='paciente', lazy=True, cascade="all, delete-orphan")
    evolucoes = db.relationship('Evolucao', backref='paciente', lazy=True, cascade="all, delete-orphan")
    consultas = db.relationship('Consulta', backref='paciente', lazy=True, cascade="all, delete-orphan")
    exames = db.relationship('Exame', backref='paciente', lazy=True, cascade="all, delete-orphan")
    compartilhamentos = db.relationship('CompartilhamentoPaciente', backref='paciente', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'cpf': self.cpf,
            'genero': self.genero,
            'telefone': self.telefone,
            'email': self.email,
            'endereco': self.endereco,
            'diagnostico': self.diagnostico,
            'observacoes': self.observacoes,
            'em_tratamento': self.em_tratamento,
            'composicao': self.composicao,
            'dosagem': self.dosagem,
            'horarios': self.horarios,
            'consentimento_lgpd': self.consentimento_lgpd,
            'data_consentimento': self.data_consentimento.isoformat() if self.data_consentimento else None,
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
    gotas = db.Column(db.Integer, default=0)
    frequencia_diaria = db.Column(db.Integer, default=1)  # 1, 2, 3 ou 4 vezes ao dia
    concentracao_cbd = db.Column(db.Float, default=0.0)   # em mg/ml
    concentracao_thc = db.Column(db.Float, default=0.0)   # em mg/ml
    concentracao_cbg = db.Column(db.Float, default=0.0)   # em mg/ml
    concentracao_cbn = db.Column(db.Float, default=0.0)   # em mg/ml
    gotas_por_ml = db.Column(db.Integer, default=30, nullable=False) # Novo campo, padrão 30
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calcular_dose_diaria(self):
        if not self.gotas_por_ml or self.gotas_por_ml == 0: # Evitar divisão por zero
            ml_por_gota = 0.05 # Fallback para 20 gotas/ml se não especificado ou zero
        else:
            ml_por_gota = 1 / self.gotas_por_ml
            
        ml_por_dose = self.gotas * ml_por_gota
        ml_por_dia = ml_por_dose * self.frequencia_diaria
        
        return {
            'ml_por_dia': round(ml_por_dia, 2),
            'cbd_mg': round(ml_por_dia * self.concentracao_cbd, 2),
            'thc_mg': round(ml_por_dia * self.concentracao_thc, 2),
            'cbg_mg': round(ml_por_dia * self.concentracao_cbg, 2),
            'cbn_mg': round(ml_por_dia * self.concentracao_cbn, 2),
            'canabinoides_totais': round(
                ml_por_dia * (self.concentracao_cbd + self.concentracao_thc + 
                              self.concentracao_cbg + self.concentracao_cbn), 2
            )
        }
    
    def to_dict(self):
        dose_diaria = self.calcular_dose_diaria()
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'data': self.data.isoformat() if self.data else None,
            'dosagem': self.dosagem,
            'gotas': self.gotas,
            'frequencia_diaria': self.frequencia_diaria,
            'concentracao_cbd': self.concentracao_cbd,
            'concentracao_thc': self.concentracao_thc,
            'concentracao_cbg': self.concentracao_cbg,
            'concentracao_cbn': self.concentracao_cbn,
            'gotas_por_ml': self.gotas_por_ml, # Adicionar ao dict
            'dose_diaria': dose_diaria,
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

class Consulta(db.Model):
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer, default=60, nullable=False)
    tipo_consulta = db.Column(db.String, default='presencial', nullable=False)  # presencial, telemedicina
    status = db.Column(db.String, default='agendada', nullable=False)  # agendada, confirmada, realizada, cancelada
    observacoes = db.Column(db.Text)
    google_event_id = db.Column(db.String)  # ID do evento no Google Calendar
    lembrete_email_enviado = db.Column(db.Boolean, default=False)
    lembrete_whatsapp_enviado = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        try:
            paciente_nome = self.paciente.nome if self.paciente else None
        except:
            paciente_nome = None
            
        try:
            profissional_nome = self.profissional.nome if self.profissional else None
        except:
            profissional_nome = None
            
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'paciente_nome': paciente_nome,
            'profissional_id': self.profissional_id,
            'profissional_nome': profissional_nome,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None,
            'duracao_minutos': self.duracao_minutos,
            'tipo_consulta': self.tipo_consulta,
            'status': self.status,
            'observacoes': self.observacoes,
            'google_event_id': self.google_event_id,
            'lembrete_email_enviado': self.lembrete_email_enviado,
            'lembrete_whatsapp_enviado': self.lembrete_whatsapp_enviado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Exame(db.Model):
    __tablename__ = 'exames'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    tipo_exame = db.Column(db.String, nullable=False)  # Hemograma, Raio-X, Ressonância, etc.
    data_exame = db.Column(db.Date, nullable=False)
    data_resultado = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    arquivo_nome = db.Column(db.String)  # Nome original do arquivo
    arquivo_path = db.Column(db.String)  # Caminho do arquivo no servidor
    arquivo_tipo = db.Column(db.String)  # MIME type (image/jpeg, application/pdf, etc.)
    arquivo_tamanho = db.Column(db.Integer)  # Tamanho em bytes
    arquivo_hash = db.Column(db.String)  # Hash MD5 para verificação de integridade
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'profissional_id': self.profissional_id,
            'profissional_nome': self.profissional.nome if self.profissional else None,
            'tipo_exame': self.tipo_exame,
            'data_exame': self.data_exame.isoformat() if self.data_exame else None,
            'data_resultado': self.data_resultado.isoformat() if self.data_resultado else None,
            'observacoes': self.observacoes,
            'arquivo_nome': self.arquivo_nome,
            'arquivo_tipo': self.arquivo_tipo,
            'arquivo_tamanho': self.arquivo_tamanho,
            'arquivo_hash': self.arquivo_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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

class CompartilhamentoPaciente(db.Model):
    __tablename__ = 'compartilhamentos_pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id', ondelete='CASCADE'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False)
    nivel_acesso = db.Column(db.String, default='leitura', nullable=False)  # leitura, escrita, completo
    data_compartilhamento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    compartilhado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relacionamentos
    profissional = db.relationship('Profissional', foreign_keys=[profissional_id], backref='compartilhamentos_recebidos')
    compartilhador = db.relationship('Profissional', foreign_keys=[compartilhado_por], backref='compartilhamentos_feitos')
    
    # Constraint para evitar duplicatas
    __table_args__ = (
        db.UniqueConstraint('paciente_id', 'profissional_id', name='uq_paciente_profissional'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'paciente_id': self.paciente_id,
            'profissional_id': self.profissional_id,
            'profissional_nome': self.profissional.nome if self.profissional else None,
            'nivel_acesso': self.nivel_acesso,
            'data_compartilhamento': self.data_compartilhamento.isoformat() if self.data_compartilhamento else None,
            'compartilhado_por': self.compartilhado_por,
            'compartilhador_nome': self.compartilhador.nome if self.compartilhador else None,
            'ativo': self.ativo
        }
