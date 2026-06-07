"""
AraOS Agents — Agent Context.

Todo agente recebe automaticamente:
    - TenantContext
    - IdentityContext
    - PatientDigitalTwin
    - CorrelationContext
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from araos.platform.shared.context import TenantContext
from araos.platform.identity.context import IdentityContext
from araos.clinical.twin.models import PatientDigitalTwin


@dataclass
class CorrelationContext:
    """
    Contexto de correlação para rastreamento de jornada.
    
    Permite ligar ações do agente a eventos anteriores.
    """
    correlation_id: str
    causation_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
        }


@dataclass
class AgentContext:
    """
    Contexto completo de execução de um agente.
    
    Este é o ÚNICO contexto que um agente recebe.
    Nenhum agente acessa banco de dados, event bus ou outros serviços
    diretamente — tudo passa pelo contexto.
    
    Attributes:
        tenant_context: Contexto de tenant
        identity_context: Contexto de identidade e permissões
        patient_twin: Digital Twin do paciente (opcional)
        correlation: Contexto de correlação para eventos
        input_data: Dados de entrada específicos da execução
        metadata: Metadados adicionais
    """
    
    tenant_context: TenantContext
    identity_context: IdentityContext
    patient_twin: Optional[PatientDigitalTwin] = None
    correlation: Optional[CorrelationContext] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Helpers
    @property
    def tenant_id(self) -> str:
        return self.tenant_context.tenant_id
    
    @property
    def actor_id(self) -> str:
        return self.identity_context.actor_id
    
    @property
    def patient_id(self) -> Optional[str]:
        return self.patient_twin.patient_id if self.patient_twin else None
    
    @property
    def correlation_id(self) -> Optional[str]:
        return self.correlation.correlation_id if self.correlation else None
    
    def has_permission(self, permission: str) -> bool:
        """Verifica permissão via IdentityContext."""
        return self.identity_context.has_permission(permission)
    
    def has_capabilities(self, capabilities: list) -> bool:
        """Verifica se tenant tem features necessárias."""
        return all(
            self.tenant_context.has_feature(cap)
            for cap in capabilities
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa contexto (seguro para logs)."""
        return {
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_type": self.identity_context.actor_type.value,
            "patient_id": self.patient_id,
            "correlation_id": self.correlation_id,
            "input_keys": list(self.input_data.keys()),
            "metadata_keys": list(self.metadata.keys()),
        }
