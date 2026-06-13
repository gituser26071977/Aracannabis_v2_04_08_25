"""add secretary role support

Revision ID: e1f2a3b4c5d6
Revises: c8f2a1b9d4e7
Create Date: 2026-06-11 00:00:00.000000

Adiciona suporte à nova role 'secretary' (e 'manager') no AraOS.

Mudanças:
  - Torna crm e uf_crm nullable em profissionais (staff sem conselho de classe)
  - Adiciona índice em profissionais.role para queries RBAC
  - Adiciona colunas em convites_profissionais_instituicoes:
      * invite_type ('staff' | 'professional') — distingue tipo de convite
      * revoked_at, revoked_by_id — auditoria de revogação
      * accepted_by_user_id — link ao Profissional criado no aceite
"""
from alembic import op
import sqlalchemy as sa


revision = 'e1f2a3b4c5d6'
down_revision = 'c8f2a1b9d4e7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. CRM/UF_CRM nullable — staff (secretary/manager) não tem conselho de classe
    op.alter_column(
        'profissionais',
        'crm',
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        'profissionais',
        'uf_crm',
        existing_type=sa.String(),
        nullable=True,
    )

    # 2. Índice em role — acelera filtros RBAC
    op.create_index(
        'ix_profissionais_role',
        'profissionais',
        ['role'],
        unique=False,
    )

    # 3. ConviteProfissionalInstituicao — campos novos
    op.add_column(
        'convites_profissionais_instituicoes',
        sa.Column('invite_type', sa.String(length=20), nullable=False, server_default='professional'),
    )
    op.add_column(
        'convites_profissionais_instituicoes',
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
    )
    op.add_column(
        'convites_profissionais_instituicoes',
        sa.Column('revoked_by_id', sa.Integer(), sa.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=True),
    )
    op.add_column(
        'convites_profissionais_instituicoes',
        sa.Column('accepted_by_user_id', sa.Integer(), sa.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index(
        'ix_convites_profissionais_invite_type',
        'convites_profissionais_instituicoes',
        ['invite_type'],
        unique=False,
    )


def downgrade():
    # Reverter na ordem inversa
    op.drop_index('ix_convites_profissionais_invite_type', table_name='convites_profissionais_instituicoes')
    op.drop_column('convites_profissionais_instituicoes', 'accepted_by_user_id')
    op.drop_column('convites_profissionais_instituicoes', 'revoked_by_id')
    op.drop_column('convites_profissionais_instituicoes', 'revoked_at')
    op.drop_column('convites_profissionais_instituicoes', 'invite_type')

    op.drop_index('ix_profissionais_role', table_name='profissionais')
    op.alter_column(
        'profissionais',
        'uf_crm',
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        'profissionais',
        'crm',
        existing_type=sa.String(),
        nullable=False,
    )
