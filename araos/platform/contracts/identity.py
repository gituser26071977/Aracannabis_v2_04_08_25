"""
AraOS Platform — Identity Provider Contract.

Interface abstrata para todos os serviços de identidade e autenticação.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from araos.platform.shared.types import TenantID, UserID


@dataclass
class AuthResult:
    """Resultado de uma operação de autenticação."""
    success: bool
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int = 3600
    mfa_required: bool = False
    message: str = ""


@dataclass
class TokenPayload:
    """Payload decodificado de um token JWT."""
    sub: str  # user_id
    org: str  # tenant_id
    role: str
    roles: List[str]
    permissions: List[str]
    modules: List[str]
    iat: int
    exp: int
    jti: str
    type: str = "access"  # access | refresh


@dataclass
class TokenPair:
    """Par de tokens (access + refresh)."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class IdentityProvider(ABC):
    """
    Contrato para autenticação e autorização.
    
    Implementações:
        - IdentityService (concreto): JWT + bcrypt
        - OAuthIdentityProvider (concreto): Google, Microsoft, Gov.br
        - BiometricIdentityProvider (futuro): DeepFace + liveness
    """
    
    @abstractmethod
    async def authenticate(self, email: str, password: str,
                           tenant_id: TenantID) -> AuthResult:
        """
        Autentica usuário por email/senha.
        """
        ...
    
    @abstractmethod
    async def authenticate_oauth(self, provider: str, code: str,
                                  tenant_id: TenantID) -> AuthResult:
        """
        Autentica via OAuth (Google, Microsoft, Gov.br).
        """
        ...
    
    @abstractmethod
    async def register(self, email: str, password: str, full_name: str,
                       tenant_id: TenantID,
                       role: str = "viewer") -> AuthResult:
        """
        Registra novo usuário.
        """
        ...
    
    @abstractmethod
    async def authorize(self, token: str,
                        required_permissions: List[str]) -> bool:
        """
        Verifica se token possui permissões necessárias.
        """
        ...
    
    @abstractmethod
    async def logout(self, token: str) -> None:
        """
        Revoga sessão (logout).
        """
        ...
    
    @abstractmethod
    async def change_password(self, user_id: UserID,
                               old_password: str,
                               new_password: str) -> bool:
        """
        Altera senha do usuário.
        """
        ...
    
    @abstractmethod
    async def get_user(self, user_id: UserID) -> Optional[Dict[str, Any]]:
        """
        Retorna dados do usuário.
        """
        ...


class TokenProvider(ABC):
    """
    Contrato para emissão e validação de tokens.
    
    Implementações:
        - JWTTokenProvider (concreto): PyJWT
        - PasetoTokenProvider (futuro): alternativa mais segura
    """
    
    @abstractmethod
    def issue(self, user_id: UserID, tenant_id: TenantID,
              role: str, permissions: List[str],
              modules: List[str]) -> TokenPair:
        """Emite access + refresh tokens."""
        ...
    
    @abstractmethod
    def validate(self, token: str) -> TokenPayload:
        """
        Valida access token.
        
        Raises:
            TokenExpiredError: se expirado
            TokenInvalidError: se inválido
        """
        ...
    
    @abstractmethod
    def refresh(self, refresh_token: str) -> TokenPair:
        """
        Gera novo par de tokens a partir de refresh token.
        
        Raises:
            SessionRevokedError: se sessão foi revogada
        """
        ...
    
    @abstractmethod
    def revoke(self, token_jti: str) -> None:
        """Revoga token pelo JTI."""
        ...
