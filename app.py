import os
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from config import get_config

def create_app():
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(get_config())
    
    # Inicializar extensões
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Configurar JWT para aceitar tokens em cookies, headers ou query string
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        return False  # Implementar verificação de token bloqueado se necessário
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'status': 401,
            'sub_status': 42,
            'msg': 'O token expirou'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'status': 401,
            'sub_status': 43,
            'msg': 'Token inválido: ' + str(error)
        }), 401
    
    # Rota raiz para verificar se o servidor está funcionando
    @app.route('/')
    def index():
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aracannabis API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2e7d32; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Aracannabis API</h1>
            <p>O servidor da API está funcionando corretamente!</p>
            <h2>Endpoints disponíveis:</h2>
            <div class="endpoint">
                <code>GET /api/status</code> - Verifica o status da API
            </div>
            <div class="endpoint">
                <code>GET /api/auth</code> - Endpoints de autenticação
            </div>
            <div class="endpoint">
                <code>GET /api/pacientes</code> - Gerenciamento de pacientes
            </div>
            <div class="endpoint">
                <code>GET /api/sintomas</code> - Registro de sintomas
            </div>
            <div class="endpoint">
                <code>GET /api/dosagens</code> - Controle de dosagens
            </div>
            <div class="endpoint">
                <code>GET /api/evolucoes</code> - Histórico de evolução
            </div>
            <p>Para acessar o frontend, abra <a href="http://localhost:3000">http://localhost:3000</a> em seu navegador.</p>
        </body>
        </html>
        '''
        return render_template_string(html)
    
    # Rota de status da API
    @app.route('/api/status')
    def status():
        return jsonify({
            'status': 'online',
            'message': 'API Aracannabis funcionando corretamente'
        })
    
    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.pacientes import pacientes_bp
    from routes.sintomas import sintomas_bp
    from routes.dosagens import dosagens_bp
    from routes.evolucoes import evolucoes_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(sintomas_bp, url_prefix='/api/sintomas')
    app.register_blueprint(dosagens_bp, url_prefix='/api/dosagens')
    app.register_blueprint(evolucoes_bp, url_prefix='/api/evolucoes')
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
