import os
from dotenv import load_dotenv
from flask import Flask
from models import db
from models_ai_compliance import AIClinicalRequest, AIClinicalOutput, AnonymizationMap, PatientConsent

# Carregar variáveis de ambiente
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///aracannabis.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def init_compliance_tables():
    app = create_app()
    with app.app_context():
        print("🔒 Iniciando criação de tabelas de Compliance e Auditoria de IA...")
        
        # Criar tabelas
        try:
            # SQLAlchemy cria apenas as tabelas que ainda não existem
            db.create_all()
            print("✅ Tabelas criadas com sucesso:")
            print("   - ai_clinical_requests (Auditoria)")
            print("   - ai_clinical_outputs (Resultados Sanitizados)")
            print("   - anonymization_maps (Mapas de Criptografia)")
            print("   - patient_consents (LGPD)")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            
if __name__ == "__main__":
    init_compliance_tables()
