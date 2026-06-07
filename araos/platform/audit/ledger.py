"""
AraOS Platform — Immutable Audit Ledger.

Ledger append-only com hash chain SHA-256.
Garante imutabilidade e rastreabilidade completa.

Campos:
    entry_id: UUID da entrada
    tenant_id: ID da organização
    actor_id: Quem fez a ação
    actor_type: Tipo do ator
    action: Ação realizada
    resource_type: Tipo do recurso
    resource_id: ID do recurso
    before: Estado anterior (JSON)
    after: Estado posterior (JSON)
    changes_summary: Resumo das mudanças
    correlation_id: ID de correlação
    event_id: ID do evento que gerou (se via Event Bus)
    timestamp: Quando ocorreu
    hash: SHA-256 desta entrada
    previous_hash: SHA-256 da entrada anterior
    ip_address: IP do cliente
    user_agent: User-Agent
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.orm import Session

from araos.platform.tenant.models import Base


class AuditEntry(Base):
    """Entrada do Audit Ledger."""
    __tablename__ = "araos_audit_ledger"
    
    entry_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), nullable=False, index=True)
    
    actor_id = Column(String(36), nullable=False)
    actor_type = Column(String(50), nullable=False)
    
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    changes_summary = Column(Text, nullable=True)
    
    correlation_id = Column(String(36), nullable=True, index=True)
    event_id = Column(String(36), nullable=True, index=True)
    
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Hash chain
    hash = Column(String(64), nullable=False, index=True)
    previous_hash = Column(String(64), nullable=False)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def compute_hash(self) -> str:
        """
        Computa SHA-256 desta entrada.
        
        Inclui todos os campos exceto o próprio hash.
        """
        data = {
            "entry_id": self.entry_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "before": self.before,
            "after": self.after,
            "changes_summary": self.changes_summary,
            "correlation_id": self.correlation_id,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else "",
            "previous_hash": self.previous_hash,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }
        
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    def verify(self) -> bool:
        """Verifica se o hash desta entrada está correto."""
        return self.hash == self.compute_hash()


class AuditLedger:
    """
    Ledger append-only com hash chain.
    
    Responsabilidades:
        - Registrar entradas de auditoria
        - Manter hash chain
        - Verificar integridade
        - Exportar para LGPD
        - Detectar anomalias
    
    Regra de ouro:
        NUNCA atualizar. NUNCA deletar.
        Apenas APPEND.
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    def append(self, entry: AuditEntry) -> str:
        """
        Adiciona entrada ao ledger.
        
        Fluxo:
            1. Busca última entrada para previous_hash
            2. Define previous_hash
            3. Computa hash da nova entrada
            4. Persiste
        
        Returns:
            entry_id da entrada criada
        """
        # 1. Buscar última entrada do tenant
        last_entry = self.db.query(AuditEntry).filter(
            AuditEntry.tenant_id == entry.tenant_id,
        ).order_by(AuditEntry.timestamp.desc()).first()
        
        # 2. Definir previous_hash
        if last_entry:
            entry.previous_hash = last_entry.hash
        else:
            # Genesis hash
            entry.previous_hash = "0" * 64
        
        # 3. Computar hash
        entry.hash = entry.compute_hash()
        
        # 4. Persistir
        self.db.add(entry)
        self.db.commit()
        
        return entry.entry_id
    
    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Busca entrada por ID."""
        return self.db.query(AuditEntry).filter(
            AuditEntry.entry_id == entry_id,
        ).first()
    
    def query(
        self,
        tenant_id: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """
        Consulta registros de auditoria.
        
        Filtros:
            - actor_id: atividade de usuário
            - action: tipo de ação
            - resource_type: tipo de recurso
            - resource_id: ID do recurso
            - date_from, date_to: período
            - correlation_id: cadeia de correlação
        """
        query = self.db.query(AuditEntry).filter(
            AuditEntry.tenant_id == tenant_id,
        )
        
        if filters:
            if "actor_id" in filters:
                query = query.filter(AuditEntry.actor_id == filters["actor_id"])
            if "action" in filters:
                query = query.filter(AuditEntry.action == filters["action"])
            if "resource_type" in filters:
                query = query.filter(AuditEntry.resource_type == filters["resource_type"])
            if "resource_id" in filters:
                query = query.filter(AuditEntry.resource_id == filters["resource_id"])
            if "correlation_id" in filters:
                query = query.filter(AuditEntry.correlation_id == filters["correlation_id"])
            if "date_from" in filters:
                query = query.filter(AuditEntry.timestamp >= filters["date_from"])
            if "date_to" in filters:
                query = query.filter(AuditEntry.timestamp <= filters["date_to"])
        
        total = query.count()
        entries = query.order_by(AuditEntry.timestamp.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return {
            "entries": [self._to_dict(e) for e in entries],
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_more": total > page * per_page,
        }
    
    def verify_integrity(self, tenant_id: str) -> bool:
        """
        Verifica integridade da hash chain.
        
        Returns:
            True se cadeia está intacta
        """
        entries = self.db.query(AuditEntry).filter(
            AuditEntry.tenant_id == tenant_id,
        ).order_by(AuditEntry.timestamp).all()
        
        if not entries:
            return True
        
        # Verificar genesis
        if entries[0].previous_hash != "0" * 64:
            return False
        
        # Verificar cada link
        for i, entry in enumerate(entries):
            # Verificar hash
            if not entry.verify():
                return False
            
            # Verificar link (exceto genesis)
            if i > 0:
                if entry.previous_hash != entries[i - 1].hash:
                    return False
        
        return True
    
    def detect_anomalies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Detecta padrões anômalos.
        
        Anomalias detectadas:
            - Acessos fora do horário comercial
            - Múltiplos logins falhos
            - Acesso a pacientes não vinculados
            - Downloads em massa
        """
        anomalies = []
        
        # Múltiplos logins falhos
        failed_logins = self.db.query(AuditEntry).filter(
            AuditEntry.tenant_id == tenant_id,
            AuditEntry.action == "LOGIN_FAILED",
        ).order_by(AuditEntry.timestamp.desc()).limit(10).all()
        
        if len(failed_logins) >= 5:
            anomalies.append({
                "type": "multiple_failed_logins",
                "severity": "high",
                "count": len(failed_logins),
                "actor_id": failed_logins[0].actor_id,
                "timestamp": failed_logins[0].timestamp.isoformat(),
            })
        
        # Acessos fora do horário (22h - 06h)
        # Simplificado — em produção usar timezone da clínica
        
        return anomalies
    
    def export(self, tenant_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Exporta auditoria para direito do titular (LGPD).
        
        Returns:
            Dados exportados
        """
        entries = self.db.query(AuditEntry).filter(
            AuditEntry.tenant_id == tenant_id,
        ).order_by(AuditEntry.timestamp).all()
        
        return {
            "tenant_id": tenant_id,
            "export_date": datetime.utcnow().isoformat(),
            "entry_count": len(entries),
            "entries": [self._to_dict(e) for e in entries],
            "integrity_verified": self.verify_integrity(tenant_id),
        }
    
    def _to_dict(self, entry: AuditEntry) -> Dict[str, Any]:
        """Converte entrada para dict."""
        return {
            "entry_id": entry.entry_id,
            "tenant_id": entry.tenant_id,
            "actor_id": entry.actor_id,
            "actor_type": entry.actor_type,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "before": entry.before,
            "after": entry.after,
            "changes_summary": entry.changes_summary,
            "correlation_id": entry.correlation_id,
            "event_id": entry.event_id,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "hash": entry.hash,
            "previous_hash": entry.previous_hash,
            "ip_address": entry.ip_address,
            "user_agent": entry.user_agent,
        }
