"""rc.15 — Adiciona coluna conselho_tipo em solicitacoes_cadastro (correção)

Migration corretiva para garantir que a coluna `conselho_tipo` exista em
`solicitacoes_cadastro`. A migration original multi-head `a7b8c9d0e1f2`
(intencionalmente adicionava a coluna em `profissionais` E em
`solicitacoes_cadastro`), mas em produção apenas a parte de
`profissionais` foi aplicada — o lado de `solicitacoes_cadastro` ficou
faltando, gerando 500 em `POST /api/cadastro_profissionais/solicitar-cadastro`.

Esta migration é idempotente (usa schema naming seguro) e é declarada
multi-head com `down_revision` tupla conectando-se à revisão atualmente
rodada em produção (`REDACTED`) e à
`a7b8c9d0e1f2` (head multi original), para preservar a linearidade do
histórico.

Revision ID: REDACTED
Revises: REDACTED, a7b8c9d0e1f2
Create Date: 2026-07-08 12:00:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'REDACTED'
down_revision = ('REDACTED', 'a7b8c9d0e1f2')
branch_labels = None
depends_on = None


def upgrade():
    # Garante coluna conselho_tipo em solicitacoes_cadastro (idempotente)
    # O IF NOT EXISTS é nativo do PostgreSQL 9.6+ e permite re-execução
    # segura caso a migration seja marcada como aplicada manualmente.
    op.execute(
        'ALTER TABLE solicitacoes_cadastro '
        'ADD COLUMN IF NOT EXISTS conselho_tipo varchar(20) DEFAULT \'CRM\''
    )


def downgrade():
    # Não removemos a coluna mesmo no downgrade — a aplicação referencia-a
    # em models e query. Caso de rollback, intervenção manual seria necessária.
    # Esta migration é estritamente aditiva.
    pass
