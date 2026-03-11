from app.database import SessionLocal
from app.models import PatientConsent

class ConsentManager:
    """Verifica e gerencia o consentimento do paciente."""
    
    def __init__(self, db_session = None):
        if db_session:
            self.db = db_session
        else:
            self.db = SessionLocal()

    def check_consent(self, patient_id: int) -> bool:
        """Retorna True se o paciente permitiu processamento de IA."""
        consent = self.db.query(PatientConsent).filter_by(patient_id=patient_id, is_active=True, ai_processing_allowed=True).first()
        # Se não tiver, verifica se foi revogado
        # Por padrão, se não existir, é False (Opt-in)
        if consent:
            return True
        return False
        
    def close(self):
        if self.db:
            self.db.close()
