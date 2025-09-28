import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, render_template_string, request, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from models import db, ReminderSettings
from config import get_config
from security_config import ALLOWED_ORIGINS, init_limiter, add_security_headers
import secrets

def create_app():
    app = Flask(__name__)
    
    # Carregar configurações
    current_config = get_config()
    app.config.from_object(current_config)
    
    # Configurar chave secreta para sessões
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Configurar token CSRF
    app.config['CSRF_TOKEN'] = secrets.token_hex(32)
    
    # Configurações de upload de arquivos
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['UPLOAD_FOLDER_EXAMES'] = os.path.join(os.getcwd(), 'uploads', 'exames')
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Configurações adicionais para upload
    app.config['MAX_CONTENT_PATH'] = None
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Inicializar extensões
    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate()
    migrate.init_app(app, db)

    # Inicializar rate limiter
    limiter = init_limiter(app)

    # CORS com origens permitidas
    CORS(app,
         origins=ALLOWED_ORIGINS,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
         supports_credentials=True)
    
    # Handler para arquivos muito grandes
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({
            "error": "Arquivo muito grande",
            "message": "O arquivo enviado excede o limite de 50MB",
            "max_size": "50MB",
            "status": 413
        }), 413
    
    # Rota para obter token CSRF
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        return jsonify({'csrf_token': app.config['CSRF_TOKEN']})
    
    # Rota raiz da API
    @app.route('/')
    def root():
        return redirect('/api/status', code=302)

    @app.route('/api')
    def api_root():
        return jsonify({
            'name': 'Aracannabis API',
            'version': '1.0.0',
            'status': 'online',
            'endpoints': {
                'auth': '/api/auth',
                'patients': '/api/pacientes',
                'symptoms': '/api/sintomas',
                'dosages': '/api/dosagens',
                'evolutions': '/api/evolucoes',
                'exams': '/api/exames',
                'products': '/api/produtos',
                'status': '/api/status'
            },
            'documentation': 'http://localhost:5002/api/status'
        })
    
    # Rota de status da API
    @app.route('/api/status')
    def status():
        return jsonify({
            'status': 'online',
            'message': 'API Aracannabis funcionando corretamente',
            'cors': 'Configurado com origens permitidas',
            'security': 'CSRF e rate limiting habilitados',
            'documentation': 'Swagger UI available at /api/swagger'
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
    from routes.produtos import produtos_bp
    from routes.cadastro_profissionais import cadastro_profissionais_bp as cadastro_prof_bp
    from routes.exames import exames_bp
    from routes.anuncios import anuncios_bp
    # from routes.ai_config import ai_config_bp  # TEMPORARIAMENTE DESABILITADO
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(exames_bp)
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(sintomas_bp, url_prefix='/api/sintomas')
    app.register_blueprint(dosagens_bp, url_prefix='/api/dosagens')
    app.register_blueprint(evolucoes_bp, url_prefix='/api/evolucoes')
    app.register_blueprint(lgpd_bp, url_prefix='/api/lgpd')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    from routes.import_export import import_export_bp
    app.register_blueprint(import_export_bp, url_prefix='/api/import-export')
    app.register_blueprint(produtos_bp, url_prefix='/api')
    app.register_blueprint(cadastro_prof_bp, url_prefix='/api/cadastro_profissionais')
    app.register_blueprint(anuncios_bp, url_prefix='/api')
    # app.register_blueprint(ai_config_bp, url_prefix='/api/ai-config')  # TEMPORARIAMENTE DESABILITADO

    # Adicionar headers de segurança a todas as respostas
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)

    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
        
        # Criar diretórios de upload se não existirem
        upload_dir = app.config.get('UPLOAD_FOLDER_EXAMES')
        if upload_dir and not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"📁 Diretório de upload criado: {upload_dir}")
    
    return app

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5002, help='Porta para rodar o servidor')
    args = parser.parse_args()
    
    app = create_app()
    print("🚀 SERVIDOR ARACANNABIS INICIADO!")
    print("🔒 CORS: Configurado com origens permitidas")
    print("🔑 CSRF: Habilitado")
    print("🛡️ Rate limiting: Ativo")
    print(f"📡 Porta: {args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=True)
