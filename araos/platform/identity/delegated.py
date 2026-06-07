"""
AraOS Platform — Delegated Identity.

PREPARAÇÃO para identidade delegada.
Não implementado ainda — apenas modelado.

Cenários futuros:
    - Concierge atuando em nome do Dr. Anderson
    - Voice Copilot atuando em nome do usuário humano
    - SDR agent agendando consulta para paciente
    - IA gerando evolução para aprovação do médico

Arquitetura:
    Actor: Agente de IA
    On Behalf Of: Usuário humano ou profissional
    Scope: Limites do que o agente pode fazer
    Audit: Toda ação delegada é rastreável
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from araos.platform.shared.types import UserID, TenantID


class DelegationScope(str, Enum):
    """Escopo de delegação."""
    READ_ONLY = "read_only"           # Apenas leitura
    CLINICAL_RECORD = "clinical_record"  # Evoluções, prescrições
    COMMUNICATION = "communication"   # Enviar mensagens
    SCHEDULING = "scheduling"         # Agendar consultas
    FULL = "full"                     # Acesso total (perigoso)


class DelegationStatus(str, Enum):
    """Status da delegação."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class DelegationContext:
    """
    Contexto de uma delegação ativa.
    
    Representa: "Agent X está agindo em nome de User Y"
    """
    delegation_id: str
    
    # Ator que está agindo (o agente)
    actor_id: str
    actor_type: str  # agent, service_account
    
    # Ator em cujo nome está agindo (o humano)
    on_behalf_of_id: str
    on_behalf_of_type: str  # user, professional, patient
    
    # Escopo e limites
    scope: DelegationScope
    permissions: List[str]  # Subconjunto das permissões do on_behalf_of
    
    # Contexto
    tenant_id: TenantID
    clinic_ids: List[str]
    
    # Temporal
    granted_at: datetime
    expires_at: Optional[datetime]
    
    # Status
    status: DelegationStatus
    
    # Metadados
    reason: Optional[str] = None  # Motivo da delegação
    session_id: Optional[str] = None
    
    def is_active(self) -> bool:
        """Verifica se delegação está ativa."""
        if self.status != DelegationStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "on_behalf_of_id": self.on_behalf_of_id,
            "on_behalf_of_type": self.on_behalf_of_type,
            "scope": self.scope.value,
            "permissions": self.permissions,
            "tenant_id": self.tenant_id,
            "clinic_ids": self.clinic_ids,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "reason": self.reason,
            "session_id": self.session_id,
        }


@dataclass
class DelegatedIdentity:
    """
    Identidade delegada para uso em tokens e contextos.
    
    Quando um agente atua em nome de um humano, o token contém:
        - sub: ID do agente
        - delegated_by: ID do humano
        - permissions: interseção (agente ∩ humano ∩ escopo)
    
    Isso permite audit completo: "Agent X fez Y em nome de Z"
    """
    
    # Identidade primária (o agente)
    actor_id: str
    actor_type: str
    
    # Identidade delegada (o humano)
    delegated_by_id: str
    delegated_by_type: str
    
    # Permissões efetivas (interseção calculada)
    effective_permissions: List[str]
    
    # Contexto da delegação
    delegation_context: Optional[DelegationContext] = None
    
    def to_identity_context(self) -> "IdentityContext":
        """Converte para IdentityContext com delegação."""
        from .context import IdentityContext, ActorType
        
        return IdentityContext(
            actor_id=self.actor_id,
            actor_type=ActorType(self.actor_type),
            tenant_id=self.delegation_context.tenant_id if self.delegation_context else "",
            organization_id=self.delegation_context.tenant_id if self.delegation_context else "",
            clinic_ids=self.delegation_context.clinic_ids if self.delegation_context else [],
            roles=["agent", "delegated"],
            permissions=self.effective_permissions,
            authenticated=True,
            delegated_by=self.delegated_by_id,
        )
    
    def to_token_claims(self) -> Dict[str, Any]:
        """Gera claims para token JWT delegado."""
        return {
            "sub": self.actor_id,
            "actor_type": self.actor_type,
            "delegated_by": self.delegated_by_id,
            "delegated_by_type": self.delegated_by_type,
            "permissions": self.effective_permissions,
            "delegation_id": self.delegation_context.delegation_id if self.delegation_context else None,
        }


class DelegationManager:
    """
    Gerenciador de delegações (preparação).
    
    Responsabilidades futuras:
        - Grant: conceder delegação
        - Revoke: revogar delegação
        - Validate: validar delegação ativa
        - Audit: registrar todas as delegações
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    def grant(
        self,
        actor_id: str,
        on_behalf_of_id: str,
        scope: DelegationScope,
        tenant_id: str,
        expires_at: Optional[datetime] = None,
        reason: Optional[str] = None,
    ) -> DelegationContext:
        """
        Concede delegação (preparação).
        
        Em produção: persistir no DB, notificar o on_behalf_of.
        """
        from araos.platform.shared.errors import NotImplementedError as PlatformNotImplemented
        raise PlatformNotImplemented("Delegation grant")
    
    def revoke(self, delegation_id: str) -> None:
        """Revoga delegação (preparação)."""
        from araos.platform.shared.errors import NotImplementedError as PlatformNotImplemented
        raise PlatformNotImplemented("Delegation revoke")
    
    def validate(self, delegation_id: str) -> Optional[DelegationContext]:
        """Valida delegação ativa (preparação)."""
        from araos.platform.shared.errors import NotImplementedError as PlatformNotImplemented
        raise PlatformNotImplemented("Delegation validation")
