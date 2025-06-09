import os
from dotenv import load_dotenv # Importar load_dotenv
load_dotenv() # Carregar variáveis do .env ANTES de outras importações

from flask import Flask, jsonify, render_template_string, request, session, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from models import db
from config import get_config
from security_config import (
    init_limiter, 
    add_security_headers, 
    ALLOWED_ORIGINS, 
    LOGIN_RATE_LIMIT,
    SENSITIVE_ENDPOINTS_RATE_LIMIT,
    API_SEARCH_RATE_LIMIT,
    generate_secure_token
)
import secrets

def create_app():
    app = Flask(__name__)
    
    # Carregar configurações
    current_config = get_config()
    app.config.from_object(current_config)
    
    # Log para verificar qual URI está sendo usada
    print(f"--- CONFIGURAÇÃO DO BANCO DE DADOS UTILIZADA ---")
    print(f"FLASK_ENV: {os.getenv('FLASK_ENV', 'N/A')}")
    print(f"DATABASE_URL lida do .env (em config.py): {os.getenv('DATABASE_URL')}")
    print(f"SQLALCHEMY_DATABASE_URI no app.config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"--- FIM DA CONFIGURAÇÃO DO BANCO ---")
    
    # Configurar chave secreta para sessões
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    
    # Configurar token CSRF
    app.config['CSRF_TOKEN'] = generate_secure_token()
    
    # Inicializar extensões
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Configurar CORS com origens permitidas (mais permissivo para desenvolvimento)
    CORS(app, resources={
        r"/*": {
            "origins": ALLOWED_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token"],
            "supports_credentials": True
        }
    })
    
    # Inicializar rate limiter
    limiter = init_limiter(app)
    
    # Aplicar rate limits específicos
    limiter.limit(LOGIN_RATE_LIMIT)(app.route('/api/auth/login', methods=['POST']))
    limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)(app.route('/api/pacientes/', methods=['POST']))
    limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)(app.route('/api/pacientes/<int:paciente_id>', methods=['PUT', 'DELETE']))
    
    # Limites mais altos para rotas de busca e consulta
    limiter.limit(API_SEARCH_RATE_LIMIT)(app.route('/api/evolucoes/paciente/<int:paciente_id>', methods=['GET']))
    limiter.limit(API_SEARCH_RATE_LIMIT)(app.route('/api/evolucoes/busca', methods=['GET']))
    limiter.limit(API_SEARCH_RATE_LIMIT)(app.route('/api/pacientes/<int:paciente_id>', methods=['GET']))
    limiter.limit(API_SEARCH_RATE_LIMIT)(app.route('/api/pacientes/', methods=['GET']))
    
    # Adicionar cabeçalhos de segurança a todas as respostas
    @app.after_request
    def after_request(response):
        return add_security_headers(response)
    
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
    
    # Rota para obter token CSRF
    @app.route('/api/csrf-token', methods=['GET'])
    def get_csrf_token():
        return jsonify({'csrf_token': app.config['CSRF_TOKEN']})
    
    # Rota raiz para verificar se o servidor está funcionando
    @app.route('/')
    def index():
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aracannabis API - Versão SEM IA</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2e7d32; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; }
                .security { background: #e8f5e9; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 5px solid #2e7d32; }
                .version { background: #fff3e0; padding: 15px; margin: 20px 0; border-radius: 5px; border-left: 5px solid #ff9800; }
            </style>
        </head>
        <body>
            <h1>Aracannabis API - Versão SEM IA</h1>
            <p>O servidor da API está funcionando corretamente!</p>
            
            <div class="version">
                <h3>📋 Versão Simplificada</h3>
                <p>Esta é a versão <strong>SEM IA</strong> do sistema Aracannabis.</p>
                <p>Funcionalidades disponíveis: Pacientes, Sintomas, Dosagens, Evoluções, Consultas, LGPD, Cadastro de Profissionais e Mercado Pago.</p>
                <p><strong>Funcionalidades de IA desabilitadas:</strong> Import/Export com IA, Configuração de IA.</p>
            </div>
            
            <div class="security">
                <h3>🔒 Sistema Seguro e Compatível com LGPD</h3>
                <p>Não se preocupe. Seus dados estão seguros. O sistema é completamente compatível com a LGPD!</p>
                <p>Implementamos medidas avançadas de segurança para proteger seus dados.</p>
            </div>
            
            <h2>Endpoints disponíveis:</h2>
            <div class="endpoint">
                <code>GET /api/status</code> - Verifica o status da API
            </div>
            <div class="endpoint">
                <code>GET /api/csrf-token</code> - Obtém token CSRF para requisições
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
            <div class="endpoint">
                <code>GET /api/consultas</code> - Agendamento de consultas
            </div>
            <div class="endpoint">
                <code>GET /api/lgpd</code> - Conformidade com LGPD
            </div>
            <div class="endpoint">
                <code>POST /api/cadastro-profissionais</code> - Cadastro de profissionais
            </div>
            <div class="endpoint">
                <code>POST /api/mercadopago</code> - Integração com Mercado Pago
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
            'message': 'API Aracannabis (SEM IA) funcionando corretamente',
            'version': 'sem_ia',
            'security': {
                'csrf_protection': True,
                'rate_limiting': True,
                'secure_headers': True,
                'lgpd_compliant': True
            },
            'features': {
                'ai_enabled': False,
                'import_export_ai': False,
                'ai_config': False,
                'cadastro_profissionais': True,
                'mercadopago_integration': True
            }
        })
    
    # Registrar blueprints (SEM IA)
    from routes.auth import auth_bp
    from routes.pacientes import pacientes_bp
    from routes.sintomas import sintomas_bp
    from routes.dosagens import dosagens_bp
    from routes.evolucoes import evolucoes_bp
    from routes.lgpd import lgpd_bp
    from routes.consultas import consultas_bp
    from routes.exames import exames_bp
    from routes.cadastro_profissionais import cadastro_profissionais_bp
    from routes.mercadopago import mercadopago_bp
    # REMOVIDO: import_export_bp e ai_config_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(sintomas_bp, url_prefix='/api/sintomas')
    app.register_blueprint(dosagens_bp, url_prefix='/api/dosagens')
    app.register_blueprint(evolucoes_bp, url_prefix='/api/evolucoes')
    app.register_blueprint(lgpd_bp, url_prefix='/api/lgpd')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(exames_bp, url_prefix='/api/exames')
    app.register_blueprint(cadastro_profissionais_bp, url_prefix='/api/cadastro-profissionais')
    app.register_blueprint(mercadopago_bp, url_prefix='/api/mercadopago')
    # REMOVIDO: app.register_blueprint(import_export_bp, url_prefix='/api/import-export')
    # REMOVIDO: app.register_blueprint(ai_config_bp, url_prefix='/api/ai-config')
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5010))  # Porta diferente para não conflitar
    
    # Configurar HTTPS em produção
    if os.environ.get('FLASK_ENV') == 'production':
        # Em produção, usar certificados SSL
        context = ('cert.pem', 'key.pem')
        app.run(host='0.0.0.0', port=port, ssl_context=context)
    else:
        # Em desenvolvimento, executar sem SSL
        app.run(host='0.0.0.0', port=port, debug=True)
