from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AnonymizeRequest, AnonymizeResponse
from app.anonymizer import Anonymizer
from app.consent import ConsentManager
import logging
import time

# Inicializar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anonymization_service")

# Criar tabelas se não existirem (apenas se rodando isolado)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aracannabis Anonymization Service", version="1.0.0")

# Inicializar Core Services
anonymizer = Anonymizer()

@app.on_event("startup")
def startup_event():
    # Pré-carregar spaCy para não atrasar primeira request
    try:
        anonymizer.load_nlp()
    except Exception as e:
        logger.error(f"Erro ao carregar modelo spaCy no startup: {e}")

@app.post("/anonymize", response_model=AnonymizeResponse)
def anonymize_data(request: AnonymizeRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    # 1. Verificar Consentimento
    consent_mgr = ConsentManager(db)
    has_consent = consent_mgr.check_consent(request.patient_id)
    
    if not has_consent:
        logger.warning(f"Tentativa de anonimização sem consentimento. Patient: {request.patient_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Paciente não consentiu com o processamento de IA."
        )
    
    # 2. Executar Anonimização
    try:
        anonymized_text, map_ids, risk_score = anonymizer.anonymize_text(
            text=request.text, 
            consultation_id=request.consultation_id, 
            db_session=db
        )
    except Exception as e:
        logger.error(f"Erro interno de anonimização: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no processamento de anonimização.")
    
    # 3. Log Seguro (Metadados apenas)
    process_time = time.time() - start_time
    logger.info(
        f"Anonimização concluída. "
        f"Consultation: {request.consultation_id}, "
        f"Patient: {request.patient_id}, "
        f"Time: {process_time:.4f}s, "
        f"Risk: {risk_score}"
    )
    
    return AnonymizeResponse(
        anonymized_text=anonymized_text,
        map_ids=map_ids,
        risk_score=risk_score,
        status="success"
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "anonymization_service"}

from app.models_rehydrate import RehydrateRequest, RehydrateResponse

@app.post("/rehydrate", response_model=RehydrateResponse)
def rehydrate_data(request: RehydrateRequest, db: Session = Depends(get_db)):
    try:
        original_text = anonymizer.rehydrate_text(
            anonymized_text=request.text, 
            consultation_id=request.consultation_id, 
            db_session=db
        )
        return RehydrateResponse(original_text=original_text, status="success")
    except Exception as e:
        logger.error(f"Erro ao reidratar texto: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno na reidratação.")
