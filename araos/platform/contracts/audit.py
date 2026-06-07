"""
AraOS Platform — Audit Provider Contract.

Interface abstrata para serviços de auditoria.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from araos.platform.shared.types import TenantID, UserID


@dataclass
class AuditEntryData:
    """Dados para criação de entrada de auditoria."""
    tenant_id: TenantID
    user_id: Optional[UserID]
    user_role: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    changes_summary: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    compliance_context: Optional[Dict[str, Any]] = None


@dataclass
class AuditQueryResult:
    """Resultado de consulta de auditoria."""
    entries: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    has_more: bool


class AuditProvider(ABC):
    """
    Contrato para auditoria centralizada.
    
    Implementações:
        - PostgresAuditProvider (concreto): PostgreSQL append-only
        - ClickHouseAuditProvider (futuro): para análise em escala
    """
    
    @abstractmethod
    async def log(self, entry: AuditEntryData) -> str:
        """
        Registra entrada de auditoria com hash chain.
        
        Returns:
            ID da entrada criada
        """
        ...
    
    @abstractmethod
    async def query(self, tenant_id: TenantID,
                    filters: Optional[Dict[str, Any]] = None,
                    page: int = 1,
                    per_page: int = 50) -> AuditQueryResult:
        """
        Consulta registros de auditoria com filtros.
        
        Filtros comuns:
            - user_id: atividade de usuário
            - action: CREATE, READ, UPDATE, DELETE
            - resource_type: patient, exam, prescription
            - date_from, date_to: período
            - ip_address: acessos de IP
        """
        ...
    
    @abstractmethod
    async def export(self, tenant_id: TenantID,
                     user_id: UserID,
                     format: str = "json") -> str:
        """
        Exporta auditoria para direito do titular (LGPD).
        
        Returns:
            URL do arquivo exportado
        """
        ...
    
    @abstractmethod
    async def verify_integrity(self, tenant_id: TenantID) -> bool:
        """
        Verifica integridade da hash chain.
        
        Returns:
            True se cadeia está intacta
        """
        ...
    
    @abstractmethod
    async def detect_anomalies(self, tenant_id: TenantID) -> List[Dict[str, Any]]:
        """
        Detecta padrões anômalos.
        
        Exemplos:
            - Acessos fora do horário comercial
            - Múltiplos logins falhos
            - Acesso a pacientes não vinculados ao médico
            - Downloads em massa de dados
        """
        ...
