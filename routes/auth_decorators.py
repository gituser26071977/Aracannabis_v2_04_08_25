"""
Decoradores de autorização padronizados para o Aracannabis SIAP.

Uso:
    from routes.auth_decorators import admin_required

    @admin_required
    def minha_rota_admin():
        ...
"""
from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt


def admin_required(f):
    """
    Decorator para verificar se o usuário é administrador ou superadmin.

    Prioridades de verificação:
        1. g.user_role (definido pelo TenantMiddleware baseado na associação atual)
        2. Claims do token JWT (fallback)
        3. Role global no banco de dados (fallback final)

    Requer que a rota já esteja protegida por @jwt_required() ou adiciona
    automaticamente.
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        effective_role = None

        # 1. Verificar role na associação atual (setado pelo middleware)
        try:
            effective_role = getattr(g, 'user_role', None)
        except Exception:
            pass

        # 2. Fallback para token claims
        if not effective_role:
            try:
                claims = get_jwt()
                effective_role = claims.get('role')
            except Exception:
                pass

        # 3. Fallback final: role global no banco
        if not effective_role:
            try:
                current_user_id = get_jwt_identity()
                if current_user_id is not None:
                    from models import Profissional
                    profissional = Profissional.query.get(int(current_user_id))
                    if profissional:
                        effective_role = profissional.role
            except Exception:
                pass

        if effective_role not in ['admin', 'superadmin']:
            return jsonify({
                'error': 'Acesso negado. Permissão de administrador ou superadministrador necessária.'
            }), 403

        return f(*args, **kwargs)

    return decorated_function
