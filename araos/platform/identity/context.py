"""
AraOS Platform — Identity Context.

Contexto de identidade propagado através de toda a plataforma.
Usado por Audit, Event Bus, Core, Voice, Smart Flow.

Diferença entre TenantContext e IdentityContext:
    - TenantContext: contexto de tenant (organização, clínica, features)
    - IdentityContext: contexto de identidade (ator, permissões, delegação)
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from araos.platform.shared.types import TenantID, UserID


class ActorType(str, Enum):
    """Tipos de atores na plataforma."""
    USER = "user"                      # Usuário humano
    PROFESSIONAL = "professional"      # Profissional de saúde
    SERVICE_ACCOUNT = "service_account"  # Conta de serviço
    AGENT = "agent"                    # Agente de IA
    SYSTEM = "system"                  # Sistema/processo interno
    ANONYMOUS = "anonymous"            # Usuário não autenticado


@dataclass
class IdentityContext:
    """
    Contexto de identidade completo.
    
    Propagado em:
        - Requisições HTTP (via middleware)
        - Eventos do Event Bus
        - Logs de auditoria
        - Chamadas entre serviços
    
    Attributes:
        actor_id: ID único do ator
        actor_type: Tipo de ator (user, agent, service_account, etc.)
        tenant_id: ID da organização
        organization_id: Alias para tenant_id
        clinic_ids: Clínicas que o ator pode acessar
        roles: Papéis do ator
        permissions: Permissões efetivas (roles + overrides)
        session_id: ID da sessão
        request_id: ID da requisição (tracing)
        ip_address: IP do cliente
        user_agent: User-Agent
        authenticated: Se o ator está autenticado
        delegated_by: ID do ator que delegou (opcional)
    """
    
    actor_id: str
    actor_type: ActorType
    tenant_id: TenantID
    organization_id: TenantID
    clinic_ids: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    authenticated: bool = False
    delegated_by: Optional[str] = None
    
    # Dados adicionais do ator
    email: Optional[str] = None
    full_name: Optional[str] = None
    plan: Optional[str] = None
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se o ator tem uma permissão específica."""
        if permission in self.permissions:
            return True
        # Wildcard total (sistema)
        if "*" in self.permissions or "platform.admin" in self.permissions:
            return True
        # Wildcard parcial
        for perm in self.permissions:
            if perm.endswith(".*"):
                prefix = perm[:-2]
                if permission.startswith(f"{prefix}."):
                    return True
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Verifica se tem pelo menos uma das permissões."""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Verifica se tem todas as permissões."""
        return all(self.has_permission(p) for p in permissions)
    
    def has_role(self, role: str) -> bool:
        """Verifica se tem um papel específico."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Verifica se tem pelo menos um dos papéis."""
        return any(r in self.roles for r in roles)
    
    def is_human(self) -> bool:
        """Verifica se o ator é humano."""
        return self.actor_type in (ActorType.USER, ActorType.PROFESSIONAL)
    
    def is_service(self) -> bool:
        """Verifica se o ator é um serviço/integração."""
        return self.actor_type in (ActorType.SERVICE_ACCOUNT, ActorType.AGENT)
    
    def is_system(self) -> bool:
        """Verifica se o ator é o sistema."""
        return self.actor_type == ActorType.SYSTEM
    
    def is_delegated(self) -> bool:
        """Verifica se a identidade foi delegada."""
        return self.delegated_by is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict (JSON-safe)."""
        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type.value,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "clinic_ids": self.clinic_ids,
            "roles": self.roles,
            "permissions": self.permissions,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "authenticated": self.authenticated,
            "delegated_by": self.delegated_by,
            "email": self.email,
            "full_name": self.full_name,
            "plan": self.plan,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityContext":
        """Deserializa de dict."""
        return cls(
            actor_id=data["actor_id"],
            actor_type=ActorType(data.get("actor_type", "anonymous")),
            tenant_id=data["tenant_id"],
            organization_id=data.get("organization_id", data["tenant_id"]),
            clinic_ids=data.get("clinic_ids", []),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            session_id=data.get("session_id"),
            request_id=data.get("request_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            authenticated=data.get("authenticated", False),
            delegated_by=data.get("delegated_by"),
            email=data.get("email"),
            full_name=data.get("full_name"),
            plan=data.get("plan"),
        )
    
    def to_tenant_context(self):
        """
        Converte para TenantContext.
        
        Usado quando um módulo precisa apenas de contexto de tenant.
        """
        from araos.platform.shared.context import TenantContext
        return TenantContext(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            clinic_id=self.clinic_ids[0] if self.clinic_ids else None,
            user_id=self.actor_id if self.is_human() else None,
            roles=self.roles,
            features=[],  # Deve ser resolvido pelo feature flag service
            plan=self.plan or "free",
            authenticated=self.authenticated,
            session_id=self.session_id,
            request_id=self.request_id,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
        )
    
    @classmethod
    def system(cls, tenant_id: str) -> "IdentityContext":
        """Cria contexto de sistema para operações internas."""
        return cls(
            actor_id="system",
            actor_type=ActorType.SYSTEM,
            tenant_id=tenant_id,
            organization_id=tenant_id,
            roles=["system"],
            permissions=["*"],  # Sistema tem acesso total
            authenticated=True,
        )
    
    def __str__(self) -> str:
        delegated = f" (delegated by {self.delegated_by})" if self.delegated_by else ""
        return f"IdentityContext({self.actor_type.value}:{self.actor_id}{delegated})"
