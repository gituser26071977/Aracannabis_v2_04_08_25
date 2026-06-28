from flask import request, g, jsonify
from models_extra import UsuarioAssociacao
from models import Profissional
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

class TenantMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Allow health checks and static files to bypass
        path = environ.get('PATH_INFO', '')
        if path.startswith('/api/status') or path.startswith('/static'):
            return self.app(environ, start_response)

        # For API requests, we might want to check tenant, but we need request context.
        # WSGI middleware is too low level for Flask's g and database access easily without application context.
        # So we will use a before_request hook instead of pure WSGI middleware for logic that needs DB.
        return self.app(environ, start_response)

def register_tenant_middleware(app):
    @app.before_request
    def check_tenant():
        # Inicializar flags padrão
        g.is_superadmin = False
        g.current_association = None
        g.user_role = None
        
        # Bypass for options and public routes (auth, status)
        if request.method == 'OPTIONS':
            return
            
        if request.path.startswith('/api/auth') or \
           request.path.startswith('/api/status') or \
           request.path.startswith('/api/public'):
            return

        try:
            # Verify JWT to get user identity (if present)
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            
            if not identity:
                # If endpoint requires auth, @jwt_required will catch it. 
                # If it's public but not in bypass list, we proceed without tenant or use default.
                return 

            user_id = int(identity)

            # P0-12 (Missão 18): tenant vem EXCLUSIVAMENTE do JWT.
            # O header X-Association-ID NÃO é mais lido para escolher tenant.
            # Esse vetor permitia spoof cross-tenant (atacante enviava
            # X-Association-ID: <id_de_outra_assoc>).
            #
            # Ordem de resolução (somente JWT):
            #   1. role global == 'superadmin' → g.is_superadmin = True
            #   2. primeira UsuarioAssociacao ativa do profissional
            profissional = Profissional.query.get(user_id)
            if profissional:
                g.user_role = profissional.role
                if profissional.role == 'superadmin':
                    g.is_superadmin = True
                    g.current_association = None
                    return

            link = UsuarioAssociacao.query.filter_by(
                profissional_id=user_id, status='active'
            ).first()
            if link:
                g.current_association = link.associacao
                g.user_role = link.role
            else:
                g.current_association = None
                 
        except Exception:
            # app.logger.error(f"Tenant Middleware Error: {e}")
            pass # Fail open or closed? Safe to fail open if protected routes check data.
