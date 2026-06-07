"""
AraOS Platform — JWT Token Provider.

Implementa emissão, validação e refresh de tokens JWT.
Tokens são padronizados para toda a plataforma.

Claims obrigatórios:
    sub         → actor_id
    tenant_id   → organization_id
    org_id      → organization_id (alias)
    clinic_ids  → lista de clínicas
    roles       → papéis do ator
    permissions → permissões efetivas
    version     → versão do token format
"""

import time
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import jwt

from araos.platform.shared.errors import TokenExpiredError, TokenInvalidError
from araos.platform.shared.types import UserID, TenantID


# ═══════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════

TOKEN_VERSION = "1.0"
ACCESS_TOKEN_EXPIRY_SECONDS = 3600        # 1 hora
REFRESH_TOKEN_EXPIRY_SECONDS = 2592000    # 30 dias
TOKEN_ALGORITHM = "HS256"


# ═══════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class TokenClaims:
    """Claims padronizados de um token AraOS."""
    sub: str                    # actor_id (user_id ou svc_id)
    tenant_id: str              # organization_id
    org_id: str                 # alias para tenant_id
    clinic_ids: List[str]       # clínicas acessíveis
    roles: List[str]            # papéis
    permissions: List[str]      # permissões efetivas
    actor_type: str             # user, service_account, agent
    jti: str                    # JWT ID (único)
    iat: int                    # issued at (epoch)
    exp: int                    # expiration (epoch)
    token_type: str             # access | refresh
    version: str                # TOKEN_VERSION
    
    # Opcionais
    email: Optional[str] = None
    full_name: Optional[str] = None
    plan: Optional[str] = None
    delegated_by: Optional[str] = None  # para delegated identity
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa claims para dict (JWT payload)."""
        result = {
            "sub": self.sub,
            "tenant_id": self.tenant_id,
            "org_id": self.org_id,
            "clinic_ids": self.clinic_ids,
            "roles": self.roles,
            "permissions": self.permissions,
            "actor_type": self.actor_type,
            "jti": self.jti,
            "iat": self.iat,
            "exp": self.exp,
            "type": self.token_type,
            "version": self.version,
        }
        if self.email:
            result["email"] = self.email
        if self.full_name:
            result["full_name"] = self.full_name
        if self.plan:
            result["plan"] = self.plan
        if self.delegated_by:
            result["delegated_by"] = self.delegated_by
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenClaims":
        """Deserializa claims de dict."""
        return cls(
            sub=data["sub"],
            tenant_id=data.get("tenant_id", data.get("org_id", "")),
            org_id=data.get("org_id", data.get("tenant_id", "")),
            clinic_ids=data.get("clinic_ids", []),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            actor_type=data.get("actor_type", "user"),
            jti=data.get("jti", ""),
            iat=data.get("iat", 0),
            exp=data.get("exp", 0),
            token_type=data.get("type", "access"),
            version=data.get("version", "1.0"),
            email=data.get("email"),
            full_name=data.get("full_name"),
            plan=data.get("plan"),
            delegated_by=data.get("delegated_by"),
        )


@dataclass
class PlatformTokenPair:
    """Par access + refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRY_SECONDS


# ═══════════════════════════════════════════════════════════════════════
# JWT TOKEN PROVIDER
# ═══════════════════════════════════════════════════════════════════════

class JWTTokenProvider:
    """
    Provider de tokens JWT para a plataforma AraOS.
    
    Responsabilidades:
        - Emitir access tokens
        - Emitir refresh tokens
        - Validar tokens
        - Refresh de tokens
        - Revogação (via blacklist de JTI)
    
    Nota: A secret_key deve ser gerenciada via KMS/vault em produção.
    """
    
    def __init__(
        self,
        secret_key: str,
        access_expiry: int = ACCESS_TOKEN_EXPIRY_SECONDS,
        refresh_expiry: int = REFRESH_TOKEN_EXPIRY_SECONDS,
    ):
        self.secret_key = secret_key
        self.access_expiry = access_expiry
        self.refresh_expiry = refresh_expiry
        self._revoked_jtis: set = set()  # Em produção: Redis/DB
    
    def issue(
        self,
        actor_id: str,
        tenant_id: str,
        roles: List[str],
        permissions: List[str],
        clinic_ids: Optional[List[str]] = None,
        actor_type: str = "user",
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        plan: Optional[str] = None,
        delegated_by: Optional[str] = None,
    ) -> PlatformTokenPair:
        """
        Emite par de tokens (access + refresh).
        
        Args:
            actor_id: ID do ator (user_id ou svc_id)
            tenant_id: ID da organização
            roles: Lista de roles
            permissions: Lista de permissões efetivas
            clinic_ids: Clínicas acessíveis
            actor_type: Tipo de ator
            email: Email do usuário
            full_name: Nome completo
            plan: Plano da organização
            delegated_by: ID do ator que delegou (opcional)
        
        Returns:
            PlatformTokenPair com access_token e refresh_token
        """
        now = int(time.time())
        
        # Access token
        access_jti = str(uuid.uuid4())
        access_claims = TokenClaims(
            sub=actor_id,
            tenant_id=tenant_id,
            org_id=tenant_id,
            clinic_ids=clinic_ids or [],
            roles=roles,
            permissions=permissions,
            actor_type=actor_type,
            jti=access_jti,
            iat=now,
            exp=now + self.access_expiry,
            token_type="access",
            version=TOKEN_VERSION,
            email=email,
            full_name=full_name,
            plan=plan,
            delegated_by=delegated_by,
        )
        access_token = jwt.encode(
            access_claims.to_dict(),
            self.secret_key,
            algorithm=TOKEN_ALGORITHM,
        )
        
        # Refresh token
        refresh_jti = str(uuid.uuid4())
        refresh_claims = TokenClaims(
            sub=actor_id,
            tenant_id=tenant_id,
            org_id=tenant_id,
            clinic_ids=[],
            roles=roles,
            permissions=[],
            actor_type=actor_type,
            jti=refresh_jti,
            iat=now,
            exp=now + self.refresh_expiry,
            token_type="refresh",
            version=TOKEN_VERSION,
        )
        refresh_token = jwt.encode(
            refresh_claims.to_dict(),
            self.secret_key,
            algorithm=TOKEN_ALGORITHM,
        )
        
        return PlatformTokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.access_expiry,
        )
    
    def validate(self, token: str, expected_type: str = "access") -> TokenClaims:
        """
        Valida e decodifica um token.
        
        Args:
            token: JWT string
            expected_type: "access" ou "refresh"
        
        Returns:
            TokenClaims decodificado
        
        Raises:
            TokenExpiredError: se token expirou
            TokenInvalidError: se token é inválido
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[TOKEN_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()
        except jwt.InvalidTokenError as e:
            raise TokenInvalidError(str(e))
        
        # Validar versão
        if payload.get("version") != TOKEN_VERSION:
            raise TokenInvalidError(f"Token version mismatch. Expected {TOKEN_VERSION}")
        
        # Validar tipo
        if payload.get("type") != expected_type:
            raise TokenInvalidError(
                f"Token type mismatch. Expected {expected_type}, got {payload.get('type')}"
            )
        
        # Verificar revogação
        jti = payload.get("jti")
        if jti and jti in self._revoked_jtis:
            raise TokenInvalidError("Token has been revoked")
        
        return TokenClaims.from_dict(payload)
    
    def refresh(self, refresh_token: str) -> PlatformTokenPair:
        """
        Gera novo par de tokens a partir de refresh token.
        
        Args:
            refresh_token: Refresh token válido
        
        Returns:
            Novo PlatformTokenPair
        
        Raises:
            TokenExpiredError: se refresh token expirou
            TokenInvalidError: se refresh token é inválido
        """
        claims = self.validate(refresh_token, expected_type="refresh")
        
        # Revogar refresh token antigo (one-time use)
        self.revoke(claims.jti)
        
        # Re-emitir com os mesmos claims (exceto exp)
        return self.issue(
            actor_id=claims.sub,
            tenant_id=claims.tenant_id,
            roles=claims.roles,
            permissions=claims.permissions,
            actor_type=claims.actor_type,
        )
    
    def revoke(self, jti: str) -> None:
        """
        Revoga token pelo JTI.
        
        Em produção: armazenar em Redis com TTL = tempo restante do token.
        """
        self._revoked_jtis.add(jti)
    
    def revoke_all_for_actor(self, actor_id: str, tokens_db: Optional[dict] = None) -> None:
        """
        Revoga todos os tokens de um ator.
        
        Em produção: usar Redis scan ou índice por actor_id.
        """
        # Placeholder — em produção implementar com Redis/DB
        pass
    
    def is_revoked(self, jti: str) -> bool:
        """Verifica se token foi revogado."""
        return jti in self._revoked_jtis
