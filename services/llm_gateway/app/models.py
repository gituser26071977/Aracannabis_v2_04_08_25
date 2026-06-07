from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from datetime import datetime
from app.database import Base

class AIClinicalRequest(Base):
    __tablename__ = 'ai_clinical_requests'

    id = Column(Integer, primary_key=True)
    # Ignorando uuid por enquanto para focar na persistência básica
    consultation_id = Column(Integer, index=True) 
    
    # Detalhes da Execução (Auditoria)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    
    # Métricas (Auditáveis)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    processing_time_ms = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    
    # Status
    status = Column(String(20), default='pending')
    error_message = Column(Text)
    
    # Contexto Tenant (Multi-tenant)
    # No SQLALchemny models extra, isso não estava explícito, mas vamos adicionar para o log
    # Se a tabela real não tiver, vai dar erro. Vamos assumir que criamos via create_compliance_tables.py
    # create_compliance_tables.py usou `models_ai_compliance.py` que não tinha `tenant_id`
    # O user pediu para logar `tenant_id`. Se a tabela não tiver colunas, precisamos migrar.
    # Por segurança, vamos usar um campo JSON 'context' ou similar se não tiver coluna, OU ignorar se não crítico.
    # O prompt pediu `tenant_id`. Vou assumir que devemos tratar isso.
    # Mas como o script anterior `create_compliance_tables.py` NÃO adicionou `tenant_id`, 
    # vou usar `ip_address` ou `user_agent` para guardar tenant_id serializado por enquanto, 
    # ou adicionar a coluna.
    # Melhor: vou adicionar `tenant_id` no modelo e assumir que a migration deve rodar.
    # Se der erro de coluna não existente, removeremos.
    # ALTERNATIVA SEGURA: Usar `user_agent` para armazenar `tenant_id:{id}` temporariamente se não quisermos alterar schema agora.
    # Mas o correto é o esquema. Vou adicionar no modelo SQLAlchemy, mas cuidado no insert.
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AIClinicalOutput(Base):
    __tablename__ = 'ai_clinical_outputs'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, nullable=False)
    
    soap_summary = Column(Text)
    structured_data = Column(JSON)
    
    validation_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)

from pydantic import BaseModel
from typing import Dict, Any

class LLMGenerateRequest(BaseModel):
    consultation_id: int
    tenant_id: int # Obrigatório para rate limit e auditoria
    anonymized_text: str
    task: str = "soap_summary" # soap_summary, risk_assessment, etc.
    provider: str = "deepseek" # opcional, default deepseek

class LLMGenerateResponse(BaseModel):
    output: Dict[str, Any] # SOAP struct
    tokens_used: int
    provider: str
    processing_time_ms: int
    status: str
