from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID, JSONB
from models import db

class AIClinicalRequest(db.Model):
    """
    Tabela de auditoria técnica para todas as requisições de IA Clínica.
    Focada em rastreabilidade, custos e performance, sem armazenar dados sensíveis brutos.
    """
    __tablename__ = 'ai_clinical_requests'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    
    # Contexto
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    
    # Detalhes da Execução
    provider = db.Column(db.String(50), nullable=False)  # ex: 'openai', 'deepseek'
    model = db.Column(db.String(100), nullable=False)    # ex: 'gpt-4', 'deepseek-chat'
    endpoint = db.Column(db.String(200))                 # ex: '/v1/chat/completions'
    
    # Métricas (Auditáveis)
    tokens_input = db.Column(db.Integer, default=0)
    tokens_output = db.Column(db.Integer, default=0)
    processing_time_ms = db.Column(db.Integer, default=0)
    cost_estimate = db.Column(db.Float, default=0.0)
    
    # Status
    status = db.Column(db.String(20), default='pending') # pending, success, error, blocked
    error_message = db.Column(db.Text)
    
    # Metadados de Compliance
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    consulta = db.relationship('Consulta', backref='ai_requests')
    paciente = db.relationship('Paciente', backref='ai_requests')
    profissional = db.relationship('Profissional', backref='ai_requests')
    outputs = db.relationship('AIClinicalOutput', backref='request', lazy=True)
    anonymization_maps = db.relationship('AnonymizationMap', backref='request', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'consultation_id': self.consultation_id,
            'patient_id': self.patient_id,
            'professional_id': self.professional_id,
            'provider': self.provider,
            'model': self.model,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'processing_time_ms': self.processing_time_ms,
            'cost_estimate': self.cost_estimate,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class AIClinicalOutput(db.Model):
    """
    Armazena o resultado processado e higienizado da IA.
    NUNCA deve conter dados brutos não estruturados que não passaram por validação.
    """
    __tablename__ = 'ai_clinical_outputs'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('ai_clinical_requests.id'), nullable=False)
    
    # Conteúdo
    soap_summary = db.Column(db.Text)  # Resumo SOAP (Subjective, Objective, Assessment, Plan)
    structured_data = db.Column(db.JSON) # JSONB no Postgres
    
    # Segurança
    validation_hash = db.Column(db.String(64)) # Hash SHA-256 do conteúdo para garantir integridade
    is_reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'request_id': self.request_id,
            'soap_summary': self.soap_summary,
            'structured_data': self.structured_data,
            'is_reviewed': self.is_reviewed,
            'created_at': self.created_at.isoformat()
        }

class AnonymizationMap(db.Model):
    """
    Tabela de ALTA SEGURANÇA.
    Armazena o mapeamento entre tokens anonimizados e dados reais.
    Deve ter acesso restrito e auditoria severa de leitura.
    """
    __tablename__ = 'anonymization_maps'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('ai_clinical_requests.id'), nullable=False)
    
    # Mapeamento
    token = db.Column(db.String(100), nullable=False) # Ex: 'PACIENTE_01', 'DATE_01'
    original_value_encrypted = db.Column(db.Text, nullable=False) # Valor criptografado (AES-256)
    entity_type = db.Column(db.String(50)) # PERSON, DATE, LOC, ORG
    
    # Metadados de Criptografia
    encryption_key_id = db.Column(db.String(50)) # ID da chave usada (p/ rotação)
    iv = db.Column(db.String(50)) # Initialization Vector (se não estiver embutido no texto cifrado)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PatientConsent(db.Model):
    """
    Registro de consentimento do paciente para processamento de dados por IA.
    Requisito LGPD/GDPR.
    """
    __tablename__ = 'patient_consents'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    
    # Escopo
    ai_processing_allowed = db.Column(db.Boolean, default=False, nullable=False)
    purpose = db.Column(db.String(100), default='clinical_assistance') 
    
    # Auditoria
    signed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Versionamento
    policy_version = db.Column(db.String(20), default='1.0')
    
    is_active = db.Column(db.Boolean, default=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    
    paciente = db.relationship('Paciente', backref='consents')

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'ai_processing_allowed': self.ai_processing_allowed,
            'purpose': self.purpose,
            'signed_at': self.signed_at.isoformat(),
            'policy_version': self.policy_version,
            'is_active': self.is_active
        }
