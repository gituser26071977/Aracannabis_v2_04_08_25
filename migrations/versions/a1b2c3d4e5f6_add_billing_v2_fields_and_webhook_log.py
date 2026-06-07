"""add billing v2 fields and webhook log

Revision ID: a1b2c3d4e5f6
Revises: ec450c16ec01
Create Date: 2026-06-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'ec450c16ec01'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos à tabela assinaturas
    op.add_column('assinaturas', sa.Column('provedor', sa.String(length=50), nullable=True))
    op.add_column('assinaturas', sa.Column('provider_subscription_id', sa.String(length=255), nullable=True))
    op.add_column('assinaturas', sa.Column('periodicidade', sa.String(length=20), nullable=True, server_default='mensal'))
    op.create_index('ix_assinaturas_provider_subscription_id', 'assinaturas', ['provider_subscription_id'], unique=False)

    # Adicionar campos à tabela faturas
    op.add_column('faturas', sa.Column('provedor', sa.String(length=50), nullable=True))
    op.add_column('faturas', sa.Column('provider_invoice_id', sa.String(length=255), nullable=True))
    op.create_index('ix_faturas_provider_invoice_id', 'faturas', ['provider_invoice_id'], unique=False)

    # Criar tabela webhook_logs
    op.create_table(
        'webhook_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('provider_event_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('processed', sa.Boolean(), default=False),
        sa.Column('fatura_id', sa.Integer(), sa.ForeignKey('faturas.id'), nullable=True),
        sa.Column('assinatura_id', sa.Integer(), sa.ForeignKey('assinaturas.id'), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.UniqueConstraint('provider', 'provider_event_id', name='uq_webhook_provider_event')
    )


def downgrade():
    op.drop_table('webhook_logs')
    op.drop_index('ix_faturas_provider_invoice_id', table_name='faturas')
    op.drop_column('faturas', 'provider_invoice_id')
    op.drop_column('faturas', 'provedor')
    op.drop_index('ix_assinaturas_provider_subscription_id', table_name='assinaturas')
    op.drop_column('assinaturas', 'periodicidade')
    op.drop_column('assinaturas', 'provider_subscription_id')
    op.drop_column('assinaturas', 'provedor')
