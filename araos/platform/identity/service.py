"""
AraOS Platform — Identity Service.

Implementação concreta do IdentityProvider.
Sistema único de identidade para toda a plataforma.

Integra:
    - Permission Engine (roles → permissions)
    - JWT Token Provider (emissão/validação)
    - Service Account Auth (API Keys)
    - Identity Context (propagação)
    - Delegated Identity (preparação)

Nenhum módulo deve possuir autenticação própria.
Toda identidade passa por aqui.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from araos.platform.contracts.identity import IdentityProvider as IdentityProviderContract
from araos.platform.contracts.identity import AuthResult, TokenPair, TokenPayload
from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    TokenInvalidError,
    TenantNotFoundError,
)
from araos.platform.shared.types import TenantID, UserID

from .permissions import RoleRegistry, PermissionRegistry
from .tokens import JWTTokenProvider, TokenClaims, PlatformTokenPair
from .context import IdentityContext, ActorType
from .service_accounts import ServiceAccountAuthenticator
from .delegated import DelegationManager, DelegatedIdentity


@dataclass
class LoginCredentials:
    """Credenciais de login."""
    email: str
    password: str
    tenant_id: Optional[str] = None


class IdentityService(IdentityProviderContract):
    """
    Serviço de identidade da plataforma AraOS.
    
    Responsabilidades:
        - Autenticar usuários (email/senha)
        - Autenticar service accounts (API Key)
        - Emitir tokens JWT
        - Validar tokens
        - Autorizar por permissão
        - Resolver IdentityContext
    
    Uso:
        identity = IdentityService(db_session, secret_key="...")
        
        # Login
        result = await identity.authenticate("doc@clinica.com", "senha", "org_123")
        
        # Validar token
        claims = identity.token_provider.validate(token)
        
        # Verificar permissão
        if identity.authorize(token, ["patient.read"]):
            ...
    """
    
    def __init__(
        self,
        db_session,
        secret_key: str,
        password_hasher=None,  # bcrypt/argon2 instance
    ):
        self.db = db_session
        self.token_provider = JWTTokenProvider(secret_key)
        self.svc_auth = ServiceAccountAuthenticator(db_session)
        self.password_hasher = password_hasher
        self.delegation_manager = DelegationManager(db_session)
    
    # ─── Autenticação ────────────────────────────────────────────────
    
    async def authenticate(
        self,
        email: str,
        password: str,
        tenant_id: TenantID,
    ) -> AuthResult:
        """
        Autentica usuário por email/senha.
        
        Args:
            email: Email do usuário
            password: Senha em plaintext
            tenant_id: ID da organização
        
        Returns:
            AuthResult com tokens ou erro
        """
        from araos.platform.tenant.models import User
        
        user = self.db.query(User).filter(
            User.organization_id == tenant_id,
            User.email == email,
            User.active == True,
            User.deleted_at.is_(None),
        ).first()
        
        if not user:
            return AuthResult(
                success=False,
                message="Invalid credentials",
            )
        
        # Verificar lock
        if user.is_locked():
            return AuthResult(
                success=False,
                message="Account locked. Try again later.",
            )
        
        # Verificar senha
        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                from datetime import datetime, timedelta, timezone
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            self.db.commit()
            
            return AuthResult(
                success=False,
                message="Invalid credentials",
            )
        
        # Sucesso — resetar tentativas
        user.failed_login_attempts = 0
        from datetime import datetime, timezone
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count += 1
        self.db.commit()
        
        # Resolver permissões
        permissions = list(RoleRegistry.resolve_permissions(user.roles or []))
        
        # Emitir tokens
        tokens = self.token_provider.issue(
            actor_id=user.id,
            tenant_id=tenant_id,
            roles=user.roles or [],
            permissions=permissions,
            clinic_ids=user.clinic_ids or [],
            actor_type="user",
            email=user.email,
            full_name=user.full_name,
        )
        
        return AuthResult(
            success=True,
            user_id=user.id,
            tenant_id=tenant_id,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
            message="Authentication successful",
        )
    
    async def authenticate_oauth(
        self,
        provider: str,
        code: str,
        tenant_id: TenantID,
    ) -> AuthResult:
        """
        Autentica via OAuth (preparação).
        
        Não implementado — preparação para Google, Microsoft, Gov.br.
        """
        from araos.platform.shared.errors import NotImplementedError as PlatformNotImplemented
        raise PlatformNotImplemented("OAuth authentication")
    
    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        tenant_id: TenantID,
        role: str = "viewer",
    ) -> AuthResult:
        """
        Registra novo usuário.
        
        Args:
            email: Email
            password: Senha em plaintext
            full_name: Nome completo
            tenant_id: Organização
            role: Role inicial
        
        Returns:
            AuthResult com tokens
        """
        from araos.platform.tenant.models import User
        
        # Verificar se email já existe
        existing = self.db.query(User).filter(
            User.organization_id == tenant_id,
            User.email == email,
        ).first()
        
        if existing:
            return AuthResult(
                success=False,
                message="Email already registered",
            )
        
        # Hash da senha
        password_hash = self._hash_password(password)
        
        user = User(
            organization_id=tenant_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            roles=[role],
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Autenticar automaticamente
        return await self.authenticate(email, password, tenant_id)
    
    # ─── Autorização ─────────────────────────────────────────────────
    
    async def authorize(
        self,
        token: str,
        required_permissions: List[str],
    ) -> bool:
        """
        Verifica se token possui permissões necessárias.
        
        Args:
            token: Access token JWT
            required_permissions: Lista de permissões necessárias
        
        Returns:
            True se autorizado
        """
        try:
            claims = self.token_provider.validate(token)
        except (TokenExpiredError, TokenInvalidError):
            return False
        
        # Verificar cada permissão necessária
        for required in required_permissions:
            if not self._check_permission(claims.permissions, required):
                return False
        
        return True
    
    def _check_permission(self, permissions: List[str], required: str) -> bool:
        """Verifica se uma lista de permissões concede a permissão necessária."""
        if required in permissions:
            return True
        # Wildcard
        for perm in permissions:
            if perm == "*" or perm == "platform.admin":
                return True
            if perm.endswith(".*"):
                prefix = perm[:-2]
                if required.startswith(f"{prefix}."):
                    return True
        return False
    
    # ─── Logout ──────────────────────────────────────────────────────
    
    async def logout(self, token: str) -> None:
        """
        Revoga sessão (logout).
        
        Revoga o token pelo JTI.
        """
        try:
            claims = self.token_provider.validate(token)
            self.token_provider.revoke(claims.jti)
        except (TokenExpiredError, TokenInvalidError):
            pass  # Token já inválido, nada a fazer
    
    # ─── Senha ───────────────────────────────────────────────────────
    
    async def change_password(
        self,
        user_id: UserID,
        old_password: str,
        new_password: str,
    ) -> bool:
        """Altera senha do usuário."""
        from araos.platform.tenant.models import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not self._verify_password(old_password, user.password_hash):
            return False
        
        user.password_hash = self._hash_password(new_password)
        self.db.commit()
        
        # Revogar todos os tokens do usuário
        self.token_provider.revoke_all_for_actor(user_id)
        
        return True
    
    # ─── Usuário ─────────────────────────────────────────────────────
    
    async def get_user(self, user_id: UserID) -> Optional[Dict[str, Any]]:
        """Retorna dados do usuário."""
        from araos.platform.tenant.models import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        return user.to_dict()
    
    # ─── Identity Context ────────────────────────────────────────────
    
    def resolve_identity_context(self, token: str) -> IdentityContext:
        """
        Resolve IdentityContext a partir de token.
        
        Principal ponto de entrada para middleware.
        """
        claims = self.token_provider.validate(token)
        
        return IdentityContext(
            actor_id=claims.sub,
            actor_type=ActorType(claims.actor_type),
            tenant_id=claims.tenant_id,
            organization_id=claims.org_id,
            clinic_ids=claims.clinic_ids,
            roles=claims.roles,
            permissions=claims.permissions,
            email=claims.email,
            full_name=claims.full_name,
            plan=claims.plan,
            authenticated=True,
            delegated_by=claims.delegated_by,
        )
    
    def REDACTED(
        self, api_key: str
    ) -> IdentityContext:
        """
        Resolve IdentityContext a partir de API Key de service account.
        """
        tenant_ctx = self.svc_auth.authenticate(api_key)
        
        from araos.platform.tenant.models import ServiceAccount
        svc_id = tenant_ctx.user_id.replace("svc:", "")
        svc = self.db.query(ServiceAccount).filter(ServiceAccount.id == svc_id).first()
        
        if not svc:
            raise AuthenticationError("Service account not found")
        
        return IdentityContext(
            actor_id=svc.id,
            actor_type=ActorType.SERVICE_ACCOUNT,
            tenant_id=svc.organization_id,
            organization_id=svc.organization_id,
            clinic_ids=svc.clinic_ids or [],
            roles=["service_account"],
            permissions=svc.permissions or [],
            authenticated=True,
        )
    
    # ─── Password Helpers ────────────────────────────────────────────
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica senha contra hash."""
        if self.password_hasher:
            return self.password_hasher.check(password_hash, password)
        # Fallback: plain comparison (nunca em produção!)
        return password_hash == password
    
    def _hash_password(self, password: str) -> str:
        """Gera hash de senha."""
        if self.password_hasher:
            return self.password_hasher.hash(password)
        # Fallback: plain (nunca em produção!)
        return password
    
    # ─── Token Helpers ───────────────────────────────────────────────
    
    def refresh_token(self, refresh_token: str) -> PlatformTokenPair:
        """Renova tokens."""
        return self.token_provider.refresh(refresh_token)
    
    def validate_token(self, token: str) -> TokenClaims:
        """Valida token e retorna claims."""
        return self.token_provider.validate(token)
