"""
AraOS Platform — Tenant Context Resolver.

Resolve TenantContext a partir de múltiplas fontes de autenticação:
    1. JWT (token Bearer)
    2. Header X-Tenant-ID
    3. API Key
    4. Service Account

Retorna TenantContext padronizado consumido por todos os módulos.
"""

from typing import Optional, Dict, Any, List
import base64
import hashlib
import hmac
import re

from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import (
    AuthenticationError,
    TenantResolutionError,
    TenantNotFoundError,
)


class ResolverInput:
    """Input unificado para resolução de tenant."""
    
    def __init__(
        self,
        authorization_header: Optional[str] = None,
        api_key_header: Optional[str] = None,
        tenant_id_header: Optional[str] = None,
        service_account_header: Optional[str] = None,
        jwt_cookie: Optional[str] = None,
        query_params: Optional[Dict[str, str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_path: Optional[str] = None,
    ):
        self.authorization_header = authorization_header
        self.api_key_header = api_key_header
        self.tenant_id_header = tenant_id_header
        self.service_account_header = service_account_header
        self.jwt_cookie = jwt_cookie
        self.query_params = query_params or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.request_path = request_path


class TenantContextResolver:
    """
    Resolvedor de TenantContext.
    
    Ordem de resolução:
        1. JWT (mais comum para usuários humanos)
        2. API Key (integrações e service accounts)
        3. Service Account Key (agentes internos)
        4. Header X-Tenant-ID (para endpoints públicos/anon)
        5. Query param (fallback)
    """
    
    def __init__(
        self,
        identity_client=None,  # IdentityClient para validar JWT
        db_session=None,       # SQLAlchemy session para consultar DB
    ):
        self.identity_client = identity_client
        self.db_session = db_session
    
    def resolve_sync(self, input_data: ResolverInput) -> TenantContext:
        """
        Versão síncrona do resolve (para Flask before_request).
        
        Nota: Não suporta JWT que requer async no identity_client.
              Para JWT, use o middleware FastAPI ou chame resolve() async.
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Dentro de um loop rodando, precisamos de outra abordagem
                # Flask 2.0+ suporta async before_request, mas para compatibilidade
                # vamos usar run_coroutine_threadsafe ou simplesmente resolver
                # sem o identity_client async
                return self._resolve_sync_impl(input_data)
            return loop.run_until_complete(self.resolve(input_data))
        except RuntimeError:
            # Sem loop rodando
            return asyncio.run(self.resolve(input_data))
    
    def _resolve_sync_impl(self, input_data: ResolverInput) -> TenantContext:
        """Implementação síncrona para casos onde async não está disponível."""
        # 1. Tentar API Key (síncrono)
        if input_data.api_key_header:
            context = self._resolve_from_api_key_sync(input_data)
            if context:
                return context
        
        # 2. Tentar Service Account (síncrono)
        if input_data.service_account_header:
            context = self._resolve_from_service_account_sync(input_data)
            if context:
                return context
        
        # 3. Tentar Tenant ID (síncrono)
        if input_data.tenant_id_header:
            context = self._resolve_from_tenant_id_sync(input_data)
            if context:
                return context
        
        # 4. JWT requer async — não disponível em modo síncrono
        if input_data.authorization_header:
            raise TenantResolutionError(
                "JWT resolution requires async context. Use async middleware or provide API Key."
            )
        
        raise TenantResolutionError(
            "Unable to resolve tenant context synchronously. "
            "Provide API Key, Service Account Key, or X-Tenant-ID header."
        )
    
    def _resolve_from_api_key_sync(self, input_data: ResolverInput) -> Optional[TenantContext]:
        """Síncrono: resolve a partir de API Key."""
        api_key = input_data.api_key_header
        if not api_key or not self.db_session:
            return None
        
        from .models import ServiceAccount, now_utc
        import hashlib
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        svc_account = self.db_session.query(ServiceAccount).filter(
            ServiceAccount.api_key_hash == key_hash,
            ServiceAccount.active == True,
        ).first()
        
        if not svc_account:
            raise AuthenticationError("Invalid API Key")
        
        svc_account.last_used_at = now_utc()
        self.db_session.commit()
        
        return TenantContext(
            tenant_id=svc_account.organization_id,
            organization_id=svc_account.organization_id,
            user_id=f"svc:{svc_account.id}",
            roles=["service_account"],
            features=[],
            authenticated=True,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    def _resolve_from_service_account_sync(self, input_data: ResolverInput) -> Optional[TenantContext]:
        """Síncrono: resolve a partir de Service Account."""
        svc_key = input_data.service_account_header
        if not svc_key or not self.db_session:
            return None
        
        from .models import ServiceAccount, now_utc
        import hashlib
        
        key_hash = hashlib.sha256(svc_key.encode()).hexdigest()
        svc_account = self.db_session.query(ServiceAccount).filter(
            ServiceAccount.api_key_hash == key_hash,
            ServiceAccount.active == True,
        ).first()
        
        if not svc_account:
            raise AuthenticationError("Invalid Service Account Key")
        
        svc_account.last_used_at = now_utc()
        self.db_session.commit()
        
        return TenantContext(
            tenant_id=svc_account.organization_id,
            organization_id=svc_account.organization_id,
            user_id=f"svc:{svc_account.id}",
            roles=["service_account"],
            features=[],
            authenticated=True,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    def _resolve_from_tenant_id_sync(self, input_data: ResolverInput) -> Optional[TenantContext]:
        """Síncrono: resolve a partir de X-Tenant-ID."""
        tenant_id = input_data.tenant_id_header
        if not tenant_id or not self.db_session:
            return None
        
        from .models import Organization
        
        org = self.db_session.query(Organization).filter(
            Organization.id == tenant_id,
            Organization.status == "active",
            Organization.deleted_at.is_(None),
        ).first()
        
        if not org:
            raise TenantNotFoundError(tenant_id)
        
        return TenantContext(
            tenant_id=org.id,
            organization_id=org.id,
            user_id=None,
            roles=["anonymous"],
            features=org.settings.get("features", []) if org.settings else [],
            plan=org.plan,
            authenticated=False,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    async def resolve(self, input_data: ResolverInput) -> TenantContext:
        """
        Resolve TenantContext a partir do input.
        
        Args:
            input_data: Dados extraídos da requisição HTTP
        
        Returns:
            TenantContext completo
        
        Raises:
            TenantResolutionError: se não conseguir resolver
            AuthenticationError: se autenticação falhar
        """
        # 1. Tentar JWT
        if input_data.authorization_header:
            context = await self._resolve_from_jwt(input_data)
            if context:
                return context
        
        # 2. Tentar API Key
        if input_data.api_key_header:
            context = await self._resolve_from_api_key(input_data)
            if context:
                return context
        
        # 3. Tentar Service Account
        if input_data.service_account_header:
            context = await self._resolve_from_service_account(input_data)
            if context:
                return context
        
        # 4. Tentar Header X-Tenant-ID (anônimo ou pré-autenticado)
        if input_data.tenant_id_header:
            context = await self._resolve_from_tenant_id(input_data)
            if context:
                return context
        
        # 5. Tentar query param
        tenant_id = input_data.query_params.get("tenant_id")
        if tenant_id:
            context = await self._resolve_from_tenant_id(
                ResolverInput(tenant_id_header=tenant_id)
            )
            if context:
                return context
        
        raise TenantResolutionError(
            "Unable to resolve tenant context. "
            "Provide JWT, API Key, Service Account Key, or X-Tenant-ID header."
        )
    
    async def _resolve_from_jwt(self, input_data: ResolverInput) -> Optional[TenantContext]:
        """Resolve a partir de JWT Bearer token."""
        auth = input_data.authorization_header
        if not auth or not auth.startswith("Bearer "):
            return None
        
        token = auth[7:]  # Remove "Bearer "
        
        if not self.identity_client:
            raise TenantResolutionError(
                "JWT provided but no identity_client configured"
            )
        
        try:
            # identity_client.validate_token retorna TenantContext
            context = await self.identity_client.validate_token(token)
            
            # Enriquecer com dados da request
            context.ip_address = input_data.ip_address
            context.user_agent = input_data.user_agent
            context.authenticated = True
            
            return context
        except Exception as e:
            raise AuthenticationError(f"Invalid JWT: {str(e)}")
    
    async def _resolve_from_api_key(self, input_data: ResolverInput) -> Optional[TenantContext]:
        """Resolve a partir de API Key (X-Api-Key)."""
        api_key = input_data.api_key_header
        if not api_key:
            return None
        
        if not self.db_session:
            raise TenantResolutionError(
                "API Key provided but no db_session configured"
            )
        
        # Buscar service account pela API key (hash)
        from .models import ServiceAccount
        
        # O prefixo da API key é os primeiros 8 caracteres
        prefix = api_key[:8] if len(api_key) >= 8 else api_key
        
        # Hash da API key para comparação segura
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        svc_account = self.db_session.query(ServiceAccount).filter(
            ServiceAccount.api_key_hash == key_hash,
            ServiceAccount.active == True,
        ).first()
        
        if not svc_account:
            raise AuthenticationError("Invalid API Key")
        
        # Atualizar last_used_at
        from .models import now_utc
        svc_account.last_used_at = now_utc()
        self.db_session.commit()
        
        return TenantContext(
            tenant_id=svc_account.organization_id,
            organization_id=svc_account.organization_id,
            user_id=f"svc:{svc_account.id}",
            roles=["service_account"],
            features=[],  # Preenchido pelo feature flag service
            authenticated=True,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    async def _resolve_from_service_account(
        self, input_data: ResolverInput
    ) -> Optional[TenantContext]:
        """Resolve a partir de Service Account Key (X-Service-Account)."""
        svc_key = input_data.service_account_header
        if not svc_key:
            return None
        
        if not self.db_session:
            raise TenantResolutionError(
                "Service Account Key provided but no db_session configured"
            )
        
        from .models import ServiceAccount
        
        key_hash = hashlib.sha256(svc_key.encode()).hexdigest()
        
        svc_account = self.db_session.query(ServiceAccount).filter(
            ServiceAccount.api_key_hash == key_hash,
            ServiceAccount.active == True,
        ).first()
        
        if not svc_account:
            raise AuthenticationError("Invalid Service Account Key")
        
        from .models import now_utc
        svc_account.last_used_at = now_utc()
        self.db_session.commit()
        
        return TenantContext(
            tenant_id=svc_account.organization_id,
            organization_id=svc_account.organization_id,
            user_id=f"svc:{svc_account.id}",
            roles=["service_account"],
            features=[],
            authenticated=True,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    async def _resolve_from_tenant_id(
        self, input_data: ResolverInput
    ) -> Optional[TenantContext]:
        """Resolve a partir de X-Tenant-ID (contexto anônimo)."""
        tenant_id = input_data.tenant_id_header
        if not tenant_id:
            return None
        
        if not self.db_session:
            raise TenantResolutionError(
                "Tenant ID provided but no db_session configured"
            )
        
        from .models import Organization
        
        org = self.db_session.query(Organization).filter(
            Organization.id == tenant_id,
            Organization.status == "active",
            Organization.deleted_at.is_(None),
        ).first()
        
        if not org:
            raise TenantNotFoundError(tenant_id)
        
        return TenantContext(
            tenant_id=org.id,
            organization_id=org.id,
            user_id=None,
            roles=["anonymous"],
            features=org.settings.get("features", []) if org.settings else [],
            plan=org.plan,
            authenticated=False,
            ip_address=input_data.ip_address,
            user_agent=input_data.user_agent,
        )
    
    # ─── Helpers para frameworks ─────────────────────────────────────
    
    @classmethod
    def from_flask_request(cls, request) -> ResolverInput:
        """Extrai ResolverInput de um request Flask."""
        return ResolverInput(
            authorization_header=request.headers.get("Authorization"),
            api_key_header=request.headers.get("X-Api-Key"),
            tenant_id_header=request.headers.get("X-Tenant-ID"),
            service_account_header=request.headers.get("X-Service-Account"),
            jwt_cookie=request.cookies.get("jwt"),
            query_params=dict(request.args),
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            request_path=request.path,
        )
    
    @classmethod
    def from_fastapi_request(cls, request) -> ResolverInput:
        """Extrai ResolverInput de um request FastAPI."""
        return ResolverInput(
            authorization_header=request.headers.get("Authorization"),
            api_key_header=request.headers.get("X-Api-Key"),
            tenant_id_header=request.headers.get("X-Tenant-ID"),
            service_account_header=request.headers.get("X-Service-Account"),
            jwt_cookie=request.cookies.get("jwt"),
            query_params=dict(request.query_params),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            request_path=request.url.path,
        )
