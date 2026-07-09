"""rc.16 — Relax crm/uf_crm NOT NULL para staff (conselho_tipo=NONE)

Contexto
--------
A migration rc.15 (commit 14dd2a4) já adicionou `conselho_tipo` em
`solicitacoes_cadastro`, mas o modelo e o schema mantinham
`crm` e `uf_crm` como `NOT NULL`. Para o fluxo de staff/secretária
(conselho_tipo='NONE'), o endpoint
`POST /api/cadastro_profissionais/solicitar-cadastro` insere
`crm=None, uf_crm=None`, o que estoura `NotNullViolation` e o
`except IntegrityError` mascarava o erro com um 409 "Dados duplicados."
enganoso.

Esta migration:
1. Relaxa `NOT NULL` em `crm` e `uf_crm` em `profissionais` e
   `solicitacoes_cadastro` (idempotente — re-executável com segurança).
2. Substitui a `UniqueConstraint("crm","uf_crm")` por **partial unique
   index** (`WHERE crm IS NOT NULL AND uf_crm IS NOT NULL`), permitindo
   múltiplos staffs com NULL/NULL sem perder unicidade para profissionais
   de saúde.

É a primeira vez que o projeto usa partial unique index. Documentado
aqui para referência futura.

Revision ID: REDACTED
Revises: REDACTED
Create Date: 2026-07-09 14:40:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'REDACTED'
down_revision = 'REDACTED'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Normalizar string vazia para NULL antes do DROP NOT NULL.
    #    (defesa em profundidade — registros antigos podem ter crm=''.)
    op.execute("UPDATE profissionais SET crm = NULL WHERE crm = ''")
    op.execute("UPDATE profissionais SET uf_crm = NULL WHERE uf_crm = ''")
    op.execute("UPDATE solicitacoes_cadastro SET crm = NULL WHERE crm = ''")
    op.execute("UPDATE solicitacoes_cadastro SET uf_crm = NULL WHERE uf_crm = ''")

    # 2) Relaxar NOT NULL — idempotente via DO block para Postgres.
    op.execute("ALTER TABLE profissionais ALTER COLUMN crm DROP NOT NULL")
    op.execute("ALTER TABLE profissionais ALTER COLUMN uf_crm DROP NOT NULL")
    op.execute("ALTER TABLE solicitacoes_cadastro ALTER COLUMN crm DROP NOT NULL")
    op.execute("ALTER TABLE solicitacoes_cadastro ALTER COLUMN uf_crm DROP NOT NULL")

    # 3) Substituir UniqueConstraint antigo por partial unique index.
    #    IF EXISTS torna a migration re-rodável.
    op.execute("ALTER TABLE profissionais DROP CONSTRAINT IF EXISTS uq_crm_uf")
    op.execute("ALTER TABLE solicitacoes_cadastro DROP CONSTRAINT IF EXISTS uq_solicitacao_crm_uf")

    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_uf_partial "
        "ON profissionais (crm, uf_crm) "
        "WHERE crm IS NOT NULL AND uf_crm IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_solicitacao_crm_uf_partial "
        "ON solicitacoes_cadastro (crm, uf_crm) "
        "WHERE crm IS NOT NULL AND uf_crm IS NOT NULL"
    )


def downgrade():
    # Reversão best-effort: dropar índices parciais e recriar constraints
    # antigas (assumindo que não há duplicatas NULL/NULL que violem).
    op.execute("DROP INDEX IF EXISTS uq_crm_uf_partial")
    op.execute("DROP INDEX IF EXISTS uq_solicitacao_crm_uf_partial")

    op.execute(
        "ALTER TABLE profissionais ADD CONSTRAINT uq_crm_uf UNIQUE (crm, uf_crm)"
    )
    op.execute(
        "ALTER TABLE solicitacoes_cadastro ADD CONSTRAINT uq_solicitacao_crm_uf UNIQUE (crm, uf_crm)"
    )
    # NOT NULL não é revertido — staff já cadastrados teriam NULLs ilegais.