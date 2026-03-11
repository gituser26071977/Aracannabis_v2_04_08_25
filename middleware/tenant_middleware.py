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

            # 1. Try to get Association ID from Header
            assoc_id = request.headers.get('X-Association-ID')

            if assoc_id:
                # Validate if user belongs to this association
                link = UsuarioAssociacao.query.filter_by(
                    profissional_id=user_id,
                    associacao_id=int(assoc_id)
                ).first()

                if link and link.status == 'active':
                    g.current_association = link.associacao
                    g.user_role = link.role
                    return # Sucesso
                else:
                    return jsonify({'error': 'Acesso negado a esta associação'}), 403
            
            # 2. Se não houver header, verificar papel global do usuário
            profissional = Profissional.query.get(user_id)
            if profissional:
                g.user_role = profissional.role
                if profissional.role == 'superadmin':
                    g.is_superadmin = True
                    g.current_association = None
                    return # Superadmin pode operar sem associação específica

            # 3. Fallback para a primeira associação ativa encontrada para usuários comuns
            link = UsuarioAssociacao.query.filter_by(profissional_id=user_id, status='active').first()
            if link:
                g.current_association = link.associacao
                g.user_role = link.role
            else:
                 # Usuário sem associação? Caso especial, talvez superadmin (já tratado acima) ou aguardando aprovação.
                 g.current_association = None
                 # We don't block here, we let the route handle if it needs association
                 
        except Exception:
            # app.logger.error(f"Tenant Middleware Error: {e}")
            pass # Fail open or closed? Safe to fail open if protected routes check data.
