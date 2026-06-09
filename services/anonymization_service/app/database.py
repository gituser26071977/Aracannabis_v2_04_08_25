from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Conectar ao mesmo banco da aplicação principal para compartilhar dados de consentimento e mapas
# Em produção, pode ser um esquema separado, mas aqui precisamos acessar patient_consents
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../../araos.db")

# Ajuste para SQLite relativo se necessário
if DATABASE_URL.startswith("sqlite"):
    # Se for SQLite, garantir path absoluto ou relativo correto
    pass

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
