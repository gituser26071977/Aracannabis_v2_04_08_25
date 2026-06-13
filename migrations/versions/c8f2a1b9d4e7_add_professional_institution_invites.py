"""add professional institution invites

Revision ID: c8f2a1b9d4e7
Revises: bb2cbd44835d
Create Date: 2026-06-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'c8f2a1b9d4e7'
down_revision = 'bb2cbd44835d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('solicitacoes_cadastro', sa.Column('convite_token', sa.String(length=128), nullable=True))

    op.create_table(
        'convites_profissionais_instituicoes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('associacao_id', sa.Integer(), sa.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('convidado_por_id', sa.Integer(), sa.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=True),
        sa.Column('nome', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('telefone', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, server_default='member'),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('token', name='uq_convite_profissional_token')
    )
    op.create_index('ix_convites_profissionais_email', 'convites_profissionais_instituicoes', ['email'], unique=False)
    op.create_index('ix_convites_profissionais_token', 'convites_profissionais_instituicoes', ['token'], unique=False)


def downgrade():
    op.drop_index('ix_convites_profissionais_token', table_name='convites_profissionais_instituicoes')
    op.drop_index('ix_convites_profissionais_email', table_name='convites_profissionais_instituicoes')
    op.drop_table('convites_profissionais_instituicoes')
    op.drop_column('solicitacoes_cadastro', 'convite_token')
