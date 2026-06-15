"""add consultorios table for intelligent_import feature

Revision ID: d3e4f5a6b7c8
Revises: a7b8c9d0e1f2
Create Date: 2026-06-15 03:00:00

Cria tabela `consultorios` (tenant-scoped via associacao_id) para suportar
o intent `consultorios` do IntelligentImportService.

Constraints:
  - FK associacoes.id ON DELETE CASCADE (limpeza automática)
  - UNIQUE (associacao_id, nome) para evitar duplicidade por clínica
  - INDEX em associacao_id para queries multi-tenant

Parte da feature feat/intelligent-import (fase I4).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3e4f5a6b7c8'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'consultorios',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('associacao_id', sa.Integer(), nullable=False, index=True),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.Column('andar', sa.String(length=40), nullable=True),
        sa.Column('ala', sa.String(length=40), nullable=True),
        sa.Column('capacidade', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('recursos', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['associacao_id'],
            ['associacoes.id'],
            name='fk_consultorios_associacao',
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint('associacao_id', 'nome', name='uq_consultorio_assoc_nome'),
    )


def downgrade():
    op.drop_table('consultorios')
