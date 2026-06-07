"""
AraOS Platform — Immutable Audit Ledger.

Fonte oficial de rastreabilidade da plataforma.

Características:
    - Append-only (nunca atualizado, nunca deletado)
    - Hash chain SHA-256 (imutabilidade criptográfica)
    - Integração automática com Event Bus
    - Exportação LGPD
"""

from .ledger import AuditEntry, AuditLedger
from .service import AuditService

__all__ = [
    "AuditEntry",
    "AuditLedger",
    "AuditService",
]
