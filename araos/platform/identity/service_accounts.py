"""
AraOS Platform — Service Account Authentication.

Autenticação para atores não-humanos:
    - Concierge (IA)
    - Voice Copilot
    - Smart Flow
    - SDR Agent
    - Integrações externas
    - Webhooks

Padrão oficial: API Key com prefixo + hash.
Suporte futuro: Client Credentials (OAuth2 client_credentials).
"""

import secrets
import hashlib
from typing import Optional, Dict, Any
from dataclasses import dataclass

from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import AuthenticationError


@dataclass
class APIKeyCredentials:
    """Credenciais de API Key geradas."""
    api_key: str          # Chave completa (só mostrada uma vez)
    prefix: str           # Primeiros 8 caracteres (para identificação)
    hash: str             # SHA-256 da chave (armazenado no DB)


class ServiceAccountAuthenticator:
    """
    Autenticador de Service Accounts.
    
    Suporta:
        - API Key (atual)
        - Client Credentials (futuro)
    
    Padrão API Key:
        - Prefixo: ara_ (identificação visual)
        - Seguido de 32 bytes aleatórios em base64
        - Total: ~45 caracteres
        - Exemplo: ara_7xK9mP2vL4nQ8wR5tY6uI3oP1aS9dF2g
    """
    
    KEY_PREFIX = "ara_"
    KEY_BYTES = 32
    
    def __init__(self, db_session):
        self.db = db_session
    
    def generate_api_key(self) -> APIKeyCredentials:
        """
        Gera nova API Key.
        
        Returns:
            APIKeyCredentials com chave, prefixo e hash.
            
        IMPORTANTE: A chave completa só é mostrada UMA VEZ.
        """
        raw_key = secrets.token_urlsafe(self.KEY_BYTES)
        api_key = f"{self.KEY_PREFIX}{raw_key}"
        prefix = api_key[:8]
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return APIKeyCredentials(
            api_key=api_key,
            prefix=prefix,
            hash=key_hash,
        )
    
    def authenticate(self, api_key: str) -> TenantContext:
        """
        Autentica service account pela API Key.
        
        Args:
            api_key: API Key completa
        
        Returns:
            TenantContext do service account
        
        Raises:
            AuthenticationError: se API Key inválida
        """
        from araos.platform.tenant.models import ServiceAccount
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        svc_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.api_key_hash == key_hash,
            ServiceAccount.active == True,
            ServiceAccount.deleted_at.is_(None),
        ).first()
        
        if not svc_account:
            raise AuthenticationError("Invalid API Key")
        
        # Atualizar last_used_at
        from datetime import datetime, timezone
        svc_account.last_used_at = datetime.now(timezone.utc)
        self.db.commit()
        
        return TenantContext(
            tenant_id=svc_account.organization_id,
            organization_id=svc_account.organization_id,
            user_id=f"svc:{svc_account.id}",
            roles=["service_account"],
            features=[],  # Resolvido posteriormente
            authenticated=True,
        )
    
    @staticmethod
    def validate_api_key_format(api_key: str) -> bool:
        """
        Valida formato da API Key.
        
        Regras:
            - Começa com 'ara_'
            - Mínimo 40 caracteres
            - Apenas caracteres alfanuméricos, underscore e hífen
        """
        prefix = "ara_"
        if not api_key.startswith(prefix):
            return False
        if len(api_key) < 40:
            return False
        # Apenas caracteres válidos para base64url
        valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
        if not all(c in valid_chars for c in api_key[len(prefix):]):
            return False
        return True
    
    # ─── Client Credentials (preparação) ─────────────────────────────
    
    def authenticate_client_credentials(
        self,
        client_id: str,
        client_secret: str,
    ) -> TenantContext:
        """
        Autentica via Client Credentials (OAuth2).
        
        Preparação para futuro. Não implementado ainda.
        
        Args:
            client_id: ID do cliente
            client_secret: Segredo do cliente
        
        Raises:
            NotImplementedError: sempre (preparação)
        """
        from araos.platform.shared.errors import NotImplementedError as PlatformNotImplemented
        raise PlatformNotImplemented("Client Credentials authentication")
