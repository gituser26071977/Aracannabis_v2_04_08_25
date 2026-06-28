"""
Isolamento Multi-Tenant via do_orm_execute (SQLAlchemy 2.0+).

Injeta automaticamente WHERE associacao_id = :tenant_id (ou tenant_id)
em todas as queries SELECT que envolvam tabelas com essas colunas.

P0-08 (Missão 18): INSERT/UPDATE/DELETE agora também são validados.
  - Em rotas com `g.current_association` ativo (e não-superadmin), qualquer
    INSERT/UPDATE/DELETE em uma tabela com coluna `associacao_id` precisa
    setar a coluna manualmente (já é prática em `routes/pacientes.py`).
    Se o ORM detectar o registro sem tenant, ABORTA a operação.

Usa visitors.iterate() para encontrar TODAS as tabelas referenciadas
na query, inclusive dentro de subqueries geradas por .count(), .exists() etc.

Bypass (quando precisar consultar TODAS as associações):
    Modelo.query.execution_options(skip_tenant=True).all()
"""

from flask import g, has_request_context
from sqlalchemy import event, Table, exc as sa_exc
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
        # P0-08: validação também em INSERT/UPDATE/DELETE
        if execute_state.is_column_load:
            return

        if not has_request_context():
            return
        if not hasattr(g, "current_association") or not g.current_association:
            return

        # Permite bypass explícito ou se for superadmin
        if execute_state.execution_options.get("skip_tenant", False) or getattr(
            g, "is_superadmin", False
        ):
            return

        tenant_id = g.current_association.id
        stmt = execute_state.statement

        already_filtered = set()
        for clause in visitors.iterate(stmt):
            if isinstance(clause, Table):
                tbl_name = clause.name
                if tbl_name in already_filtered:
                    continue
                if "associacao_id" in clause.c:
                    stmt = stmt.where(clause.c.associacao_id == tenant_id)
                    already_filtered.add(tbl_name)
                elif "tenant_id" in clause.c:
                    stmt = stmt.where(clause.c.tenant_id == tenant_id)
                    already_filtered.add(tbl_name)

        if already_filtered:
            execute_state.statement = stmt

    @event.listens_for(Session, "before_flush")
    def _validate_tenant_on_write(session, flush_context, instances):
        """
        P0-08 (Missão 18): bloquear INSERT/UPDATE de instâncias sem
        associacao_id quando há contexto de tenant.

        Se a rota esqueceu de setar associacao_id (ou setou None / errado),
        abortamos antes do flush com IntegrityError explícito.
        """
        if not has_request_context():
            return
        if getattr(g, "is_superadmin", False):
            return

        tenant_id = getattr(g, "current_association", None)
        tenant_id = tenant_id.id if tenant_id else None

        if tenant_id is None:
            # Sem tenant no contexto: rotas sem `@jwt_required` ou públicas.
            # Não bloqueamos (rotas públicas podem ser admin-only por decorator).
            return

        for obj in session.new:
            # Apenas models com coluna associacao_id
            assoc_id = getattr(obj, "associacao_id", None)
            if assoc_id is None:
                tbl = getattr(obj, "__table__", None)
                if tbl is not None and "associacao_id" in tbl.c:
                    raise sa_exc.IntegrityError(
                        statement=(
                            f"INSERT em {tbl.name} sem associacao_id. "
                            f"P0-08: bloqueado. Tenant={tenant_id}."
                        ),
                        params=None,
                        orig=Exception("missing associacao_id"),
                    )
            elif assoc_id != tenant_id:
                tbl = getattr(obj, "__table__", None)
                tbl_name = tbl.name if tbl is not None else "?"
                raise sa_exc.IntegrityError(
                    statement=(
                        f"INSERT em {tbl_name} com associacao_id={assoc_id} "
                        f"diferente do tenant={tenant_id}. P0-08: bloqueado."
                    ),
                    params=None,
                    orig=Exception("tenant mismatch"),
                )

        for obj in session.dirty:
            # UPDATE: verificar se associacao_id mudou para valor diferente do tenant
            assoc_id = getattr(obj, "associacao_id", None)
            if assoc_id is not None and assoc_id != tenant_id:
                tbl = getattr(obj, "__table__", None)
                tbl_name = tbl.name if tbl is not None else "?"
                raise sa_exc.IntegrityError(
                    statement=(
                        f"UPDATE em {tbl_name} tentando mover registro para "
                        f"associacao_id={assoc_id} (tenant={tenant_id}). "
                        f"P0-08: bloqueado."
                    ),
                    params=None,
                    orig=Exception("cross-tenant update"),
                )
