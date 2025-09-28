from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()
print(f"CONFIG.PY: DATABASE_URL lida do .env AQUI: {os.getenv('DATABASE_URL')}") # Log de depuração

class Config:
    # Configuração do banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/aracannabis') # Restaurada linha original
    print(f"CONFIG.PY: SQLALCHEMY_DATABASE_URI (from getenv/default): {SQLALCHEMY_DATABASE_URI}") # Log ajustado
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração do JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'chave-secreta-temporaria-deve-ser-alterada-em-producao')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas em segundos
    
    # Configuração geral
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-temporaria-deve-ser-alterada-em-producao')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Configuração CORS
    CORS_HEADERS = 'Content-Type'

class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    # Em produção, certifique-se de que as chaves secretas estão definidas no ambiente
    
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/aracannabis_test'
    
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
