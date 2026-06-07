"""
AraOS Platform — Tenant Context.

Contexto de tenant propagado através de toda requisição.
Este é o ÚNICO objeto de contexto autorizado.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .types import TenantID, UserID


@dataclass
class TenantContext:
    """
    Contexto completo de tenant, usuário e sessão.
    
    Propagado automaticamente pelo middleware de tenant.
    Nunca deve ser criado manualmente no handler — sempre via resolver.
    
    Attributes:
        tenant_id: Identificador único do tenant (obrigatório)
        organization_id: ID da organização (pode ser igual ao tenant_id)
        clinic_id: ID da clínica (null se multi-clinic não habilitado)
        user_id: ID do usuário autenticado (null para requisições anônimas)
        roles: Lista de papéis do usuário
        features: Lista de features habilitadas para o tenant
        plan: Plano de assinatura (free, pro, enterprise)
        authenticated: Se o usuário está autenticado
        session_id: ID da sessão atual
        request_id: ID da requisição (para tracing)
        ip_address: IP do cliente
        user_agent: User-Agent do cliente
    """
    
    tenant_id: TenantID
    organization_id: Optional[TenantID] = None
    clinic_id: Optional[str] = None
    user_id: Optional[UserID] = None
    roles: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    plan: str = "free"
    authenticated: bool = False
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.organization_id is None:
            self.organization_id = self.tenant_id
    
    def has_role(self, role: str) -> bool:
        """Verifica se o usuário tem um papel específico."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Verifica se o usuário tem qualquer um dos papéis."""
        return any(r in self.roles for r in roles)
    
    def has_feature(self, feature: str) -> bool:
        """Verifica se uma feature está habilitada para o tenant."""
        return feature in self.features
    
    def is_plan(self, plan: str) -> bool:
        """Verifica se o tenant está em um plano específico."""
        return self.plan == plan
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict (JSON-safe)."""
        return {
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "clinic_id": self.clinic_id,
            "user_id": self.user_id,
            "roles": self.roles,
            "features": self.features,
            "plan": self.plan,
            "authenticated": self.authenticated,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantContext":
        """Deserializa de dict."""
        return cls(
            tenant_id=data["tenant_id"],
            organization_id=data.get("organization_id"),
            clinic_id=data.get("clinic_id"),
            user_id=data.get("user_id"),
            roles=data.get("roles", []),
            features=data.get("features", []),
            plan=data.get("plan", "free"),
            authenticated=data.get("authenticated", False),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
        )
    
    def __str__(self) -> str:
        return f"TenantContext(tenant={self.tenant_id}, user={self.user_id}, plan={self.plan})"
