"""add conselho_tipo to profissionais and solicitacoes_cadastro

Revision ID: a7b8c9d0e1f2
Revises: 791ba78aa8fb, 7b45916cd7fc
Create Date: 2026-06-15 02:00:00

Adiciona coluna `conselho_tipo` nas tabelas `profissionais` e `solicitacoes_cadastro`
para suportar múltiplos conselhos de classe (CRM, CRP, COREN, CRN, CREFITO, NONE).

Valores default = 'CRM' (compatibilidade com dados existentes que assumiam CRM).
Para staff (secretária/gestor) o valor é 'NONE' e `crm` permanece NULL.

Parte da feature feat/intelligent-import (fase I0).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = ('791ba78aa8fb', '7b45916cd7fc')
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona coluna conselho_tipo em profissionais
    op.add_column(
        'profissionais',
        sa.Column('conselho_tipo', sa.String(length=20), nullable=True, server_default='CRM')
    )

    # Adiciona coluna conselho_tipo em solicitacoes_cadastro
    op.add_column(
        'solicitacoes_cadastro',
        sa.Column('conselho_tipo', sa.String(length=20), nullable=True, server_default='CRM')
    )


def downgrade():
    op.drop_column('solicitacoes_cadastro', 'conselho_tipo')
    op.drop_column('profissionais', 'conselho_tipo')
