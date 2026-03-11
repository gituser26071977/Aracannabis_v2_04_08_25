from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime
from app.database import Base

# Modelos replicados para interagir com o banco principal
# IMPORTANTE: Devem coincidir com a definição no models_ai_compliance.py

class AnonymizationMap(Base):
    __tablename__ = 'anonymization_maps'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, index=True) # Ligado ao ai_clinical_requests (não tem FK aqui para desacoplar ou usar só INT)
    # No service isolado, manteremos apenas o ID inteiro por simplicidade, ou FK se compartilharmos o ORM
    
    token = Column(String(100), nullable=False) # Ex: 'PACIENTE_01', 'DATE_01'
    original_value_encrypted = Column(Text, nullable=False) # Valor criptografado (AES-256)
    entity_type = Column(String(50)) # PERSON, DATE, LOC, ORG
    
    encryption_key_id = Column(String(50)) # ID da chave usada (p/ rotação)
    iv = Column(String(50)) # Initialization Vector
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientConsent(Base):
    __tablename__ = 'patient_consents'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, nullable=False)
    
    ai_processing_allowed = Column(Boolean, default=False, nullable=False)
    purpose = Column(String(100), default='clinical_assistance')
    
    signed_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    policy_version = Column(String(20), default='1.0')
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime, nullable=True)

# Pydantic Schemas

from pydantic import BaseModel
from typing import List

class AnonymizeRequest(BaseModel):
    consultation_id: int
    patient_id: int
    text: str

class AnonymizeResponse(BaseModel):
    anonymized_text: str
    map_ids: List[int] # Lista de IDs criados
    risk_score: float
    status: str
