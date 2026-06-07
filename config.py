from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()
print(f"CONFIG.PY: DATABASE_URL lida do .env AQUI: {os.getenv('DATABASE_URL')}") # Log de depuração

class Config:
    # Configuração do banco de dados (Postgres porta 5434)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5434/aracannabis')
    print(f"CONFIG.PY: SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração do JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'REDACTED')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas em segundos
    
    # Configuração geral
    SECRET_KEY = os.getenv('SECRET_KEY', 'REDACTED')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Configuração CORS
    CORS_HEADERS = 'Content-Type'
    
    # Configuração de upload de arquivos
    UPLOAD_FOLDER_EXAMES = os.path.join(os.getcwd(), 'uploads', 'exames')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    # Em produção, certifique-se de que as chaves secretas estão definidas no ambiente
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
# Dicionário de configurações
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Função para obter a configuração atual
def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name[env]
