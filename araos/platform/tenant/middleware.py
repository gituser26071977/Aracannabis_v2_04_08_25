"""
AraOS Platform — Tenant Middleware.

Injeta automaticamente request.tenant_context em todas as requisições.

Suporta:
    - Flask (SIAP)
    - FastAPI (Voice, Smart Flow)

Uso:
    # Flask
    app = Flask(__name__)
    tenant_middleware = FlaskTenantMiddleware(resolver)
    tenant_middleware.init_app(app)
    
    # FastAPI
    app = FastAPI()
    app.add_middleware(FastAPITenantMiddleware, resolver=resolver)
"""

from typing import Optional, Callable
import functools

from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import (
    TenantResolutionError,
    AuthenticationError,
    TenantNotFoundError,
)


# ═══════════════════════════════════════════════════════════════════════
# FLASK MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════

class FlaskTenantMiddleware:
    """
    Middleware para Flask.
    
    Injeta request.tenant_context após resolução.
    Requer Flask request context.
    """
    
    def __init__(
        self,
        resolver,
        app=None,
        exempt_routes: Optional[list] = None,
        exempt_prefixes: Optional[list] = None,
    ):
        """
        Args:
            resolver: TenantContextResolver instance
            app: Flask app (opcional, pode usar init_app depois)
            exempt_routes: Lista de rotas que não precisam de tenant context
            exempt_prefixes: Lista de prefixos exentos (ex: /health, /static)
        """
        self.resolver = resolver
        self.exempt_routes = set(exempt_routes or [])
        self.exempt_prefixes = tuple(exempt_prefixes or (
            "/health", "/static", "/docs", "/openapi.json", "/favicon.ico"
        ))
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Registra before_request no app Flask."""
        app.before_request(self._before_request)
    
    def _is_exempt(self, path: str) -> bool:
        """Verifica se rota está isenta de resolução de tenant."""
        if path in self.exempt_routes:
            return True
        if path.startswith(self.exempt_prefixes):
            return True
        return False
    
    def _before_request(self):
        """Executado antes de cada request."""
        from flask import request, g
        
        if self._is_exempt(request.path):
            return
        
        try:
            resolver_input = self.resolver.__class__.from_flask_request(request)
            tenant_context = self.resolver.resolve_sync(resolver_input)
            
            # Injeta no request e no g (Flask global)
            request.tenant_context = tenant_context
            g.tenant_context = tenant_context
            
        except (TenantResolutionError, AuthenticationError, TenantNotFoundError) as e:
            # Rotas públicas podem continuar sem tenant
            # Rotas protegidas devem ter @require_tenant
            request.tenant_context = None
            g.tenant_context = None


# ═══════════════════════════════════════════════════════════════════════
# FASTAPI MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════

class FastAPITenantMiddleware:
    """
    Middleware para FastAPI (ASGI).
    
    Injeta request.state.tenant_context.
    """
    
    def __init__(
        self,
        app,
        resolver,
        exempt_routes: Optional[list] = None,
        exempt_prefixes: Optional[list] = None,
    ):
        self.app = app
        self.resolver = resolver
        self.exempt_routes = set(exempt_routes or [])
        self.exempt_prefixes = tuple(exempt_prefixes or (
            "/health", "/static", "/docs", "/openapi.json", "/favicon.ico"
        ))
    
    def _is_exempt(self, path: str) -> bool:
        if path in self.exempt_routes:
            return True
        if path.startswith(self.exempt_prefixes):
            return True
        return False
    
    async def __call__(self, scope, receive, send):
        """ASGI middleware entrypoint."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        path = scope.get("path", "")
        
        if self._is_exempt(path):
            await self.app(scope, receive, send)
            return
        
        # Criar resolver input a partir do scope
        headers = dict(scope.get("headers", []))
        # headers vêm como bytes, precisam ser decodificados
        decoded_headers = {
            k.decode("latin-1") if isinstance(k, bytes) else k: 
            v.decode("latin-1") if isinstance(v, bytes) else v
            for k, v in headers.items()
        }
        
        from .resolver import ResolverInput
        resolver_input = ResolverInput(
            authorization_header=decoded_headers.get("authorization"),
            api_key_header=decoded_headers.get("x-api-key"),
            tenant_id_header=decoded_headers.get("x-tenant-id"),
            service_account_header=decoded_headers.get("x-service-account"),
            ip_address=scope.get("client", (None, None))[0],
            user_agent=decoded_headers.get("user-agent"),
            request_path=path,
        )
        
        try:
            tenant_context = await self.resolver.resolve(resolver_input)
            
            # Injeta no scope para acesso nos handlers
            scope["tenant_context"] = tenant_context
            
        except (TenantResolutionError, AuthenticationError, TenantNotFoundError):
            scope["tenant_context"] = None
        
        await self.app(scope, receive, send)


# ═══════════════════════════════════════════════════════════════════════
# DECORADORES
# ═══════════════════════════════════════════════════════════════════════

def require_tenant(func: Callable) -> Callable:
    """
    Decorador que exige tenant_context no request.
    
    Uso Flask:
        @app.route("/api/patients")
        @require_tenant
        def list_patients():
            ctx = request.tenant_context
            ...
    
    Uso FastAPI:
        @router.get("/patients")
        @require_tenant
        async def list_patients(request: Request):
            ctx = request.state.tenant_context
            ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request as flask_request
        
        ctx = getattr(flask_request, "tenant_context", None)
        if ctx is None:
            raise TenantResolutionError(
                "Tenant context required. Authenticate with JWT, API Key, or provide X-Tenant-ID."
            )
        return func(*args, **kwargs)
    
    return wrapper


def require_feature_flag(flag_name: str):
    """
    Decorador factory que exige uma feature flag habilitada.
    
    Uso:
        @app.route("/api/voice")
        @require_feature_flag("voice_copilot")
        def voice_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request as flask_request
            
            ctx = getattr(flask_request, "tenant_context", None)
            if ctx is None:
                raise TenantResolutionError("Tenant context required")
            
            if not ctx.has_feature(flag_name):
                from araos.platform.shared.errors import TenantFeatureNotEnabledError
                raise TenantFeatureNotEnabledError(ctx.tenant_id, flag_name)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_roles(*roles: str):
    """
    Decorador factory que exige pelo menos um dos papéis.
    
    Uso:
        @app.route("/api/admin")
        @require_roles("admin", "manager")
        def admin_endpoint():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request as flask_request
            
            ctx = getattr(flask_request, "tenant_context", None)
            if ctx is None:
                raise TenantResolutionError("Tenant context required")
            
            if not ctx.has_any_role(list(roles)):
                from araos.platform.shared.errors import AuthorizationError
                raise AuthorizationError(
                    permission=f"roles:{','.join(roles)}",
                    user_id=ctx.user_id,
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
