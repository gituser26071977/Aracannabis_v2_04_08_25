import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from config import get_config
import secrets

def create_app():
    app = Flask(__name__)
    
    # Carregar configurações
    current_config = get_config()
    app.config.from_object(current_config)
    
    # Configurar chave secreta para sessões
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Configurar token CSRF
    app.config['CSRF_TOKEN'] = 'test-csrf-token-123'
    
    # Inicializar extensões
    db.init_app(app)
    jwt = JWTManager(app)
    
    # CORS TOTALMENTE LIVRE PARA TESTE
    CORS(app, 
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
         supports_credentials=False)
    
    # Rota para obter token CSRF
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        return jsonify({'csrf_token': app.config['CSRF_TOKEN']})
    
    # Rota de status da API
    @app.route('/api/status')
    def status():
        return jsonify({
            'status': 'online',
            'message': 'API Aracannabis funcionando corretamente - CORS LIVRE',
            'cors': 'TOTALMENTE LIVRE PARA TESTE'
        })
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.pacientes import pacientes_bp
    from routes.sintomas import sintomas_bp
    from routes.dosagens import dosagens_bp
    from routes.evolucoes import evolucoes_bp
    from routes.lgpd import lgpd_bp
    from routes.consultas import consultas_bp
    from routes.import_export import import_export_bp
    from routes.ai_config import ai_config_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(sintomas_bp, url_prefix='/api/sintomas')
    app.register_blueprint(dosagens_bp, url_prefix='/api/dosagens')
    app.register_blueprint(evolucoes_bp, url_prefix='/api/evolucoes')
    app.register_blueprint(lgpd_bp, url_prefix='/api/lgpd')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(import_export_bp, url_prefix='/api/import-export')
    app.register_blueprint(ai_config_bp, url_prefix='/api/ai-config')
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🚀 SERVIDOR COM CORS LIVRE INICIADO!")
    print("🔓 CORS: Totalmente permissivo para teste")
    print("🔑 CSRF: Desabilitado para teste")
    print("📡 Porta: 5002")
    app.run(host='0.0.0.0', port=5002, debug=True)
