"""
Isolamento Multi-Tenant via do_orm_execute (SQLAlchemy 2.0+).

Injeta automaticamente WHERE associacao_id = :tenant_id (ou tenant_id)
em todas as queries SELECT que envolvam tabelas com essas colunas.

Usa visitors.iterate() para encontrar TODAS as tabelas referenciadas
na query, inclusive dentro de subqueries geradas por .count(), .exists() etc.

Bypass (quando precisar consultar TODAS as associações):
    Modelo.query.execution_options(skip_tenant=True).all()
"""

from flask import g, has_request_context
from sqlalchemy import event, Table
from sqlalchemy.orm import Session
from sqlalchemy.sql import visitors

_REGISTERED = False


def configure_tenant_filters(db):
    """Registra o listener do_orm_execute para filtro multi-tenant."""
    global _REGISTERED
    if _REGISTERED:
        return
    _REGISTERED = True

    @event.listens_for(Session, "do_orm_execute")
    def _add_tenant_filter(execute_state):
        # Só filtra SELECTs
        if not execute_state.is_select:
            return

        # Não interfere em carregamentos de colunas deferred
        if execute_state.is_column_load:
            return

        # Verifica contexto Flask
        if not has_request_context():
            return
        if not hasattr(g, 'current_association') or not g.current_association:
            return

        # Permite bypass explícito ou se for superadmin
        if execute_state.execution_options.get("skip_tenant", False) or getattr(g, 'is_superadmin', False):
            return

        tenant_id = g.current_association.id
        stmt = execute_state.statement

        # Usa visitors.iterate para encontrar TODAS as Table referenciadas,
        # incluindo dentro de subqueries (.count(), .exists(), etc.)
        already_filtered = set()
        for clause in visitors.iterate(stmt):
            if isinstance(clause, Table):
                tbl_name = clause.name
                if tbl_name in already_filtered:
                    continue
                if 'associacao_id' in clause.c:
                    stmt = stmt.where(clause.c.associacao_id == tenant_id)
                    already_filtered.add(tbl_name)
                elif 'tenant_id' in clause.c:
                    stmt = stmt.where(clause.c.tenant_id == tenant_id)
                    already_filtered.add(tbl_name)

        if already_filtered:
            execute_state.statement = stmt
