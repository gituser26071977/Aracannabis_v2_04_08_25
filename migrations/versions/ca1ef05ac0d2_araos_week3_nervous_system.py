"""ARAOS Week 3: The Nervous System

Revision ID: ca1ef05ac0d2
Revises: 83c3e98787e1
Create Date: 2026-06-07 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca1ef05ac0d2'
down_revision = '83c3e98787e1'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Event Store ─────────────────────────────────────────────────
    op.create_table(
        'araos_event_store',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_version', sa.String(10), nullable=False, server_default='1.0'),
        sa.Column('event_category', sa.String(20), nullable=False, server_default='operational'),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('correlation_id', sa.String(36), nullable=True, index=True),
        sa.Column('causation_id', sa.String(36), nullable=True, index=True),
        sa.Column('actor_id', sa.String(36), nullable=True),
        sa.Column('actor_type', sa.String(50), nullable=True),
        sa.Column('aggregate_type', sa.String(50), nullable=True, index=True),
        sa.Column('aggregate_id', sa.String(36), nullable=True, index=True),
        sa.Column('timestamp', sa.BigInteger, nullable=False),
        sa.Column('payload', sa.JSON, nullable=False, default=dict),
        sa.Column('event_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('priority', sa.String(20), nullable=False, server_default='normal'),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_event_store_tenant_type', 'araos_event_store', ['tenant_id', 'event_type'])
    op.create_index('ix_event_store_aggregate', 'araos_event_store', ['aggregate_type', 'aggregate_id'])
    op.create_index('ix_event_store_timestamp', 'araos_event_store', ['timestamp'])

    # ─── Dead Letter Queue ───────────────────────────────────────────
    op.create_table(
        'araos_event_dlq',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('event_id', sa.String(36), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('error_message', sa.Text, nullable=False),
        sa.Column('error_stack', sa.Text, nullable=True),
        sa.Column('consumer_group', sa.String(100), nullable=False),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
        sa.Column('event_metadata', sa.JSON, nullable=True, default=dict),
    )

    # ─── Event Correlations ──────────────────────────────────────────
    op.create_table(
        'araos_event_correlations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('correlation_id', sa.String(36), nullable=False, index=True),
        sa.Column('causation_id', sa.String(36), nullable=True, index=True),
        sa.Column('event_id', sa.String(36), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('event_metadata', sa.JSON, nullable=True, default=dict),
    )

    # ─── Audit Ledger ────────────────────────────────────────────────
    op.create_table(
        'araos_audit_ledger',
        sa.Column('entry_id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('actor_id', sa.String(36), nullable=False),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_id', sa.String(36), nullable=True, index=True),
        sa.Column('before', sa.JSON, nullable=True),
        sa.Column('after', sa.JSON, nullable=True),
        sa.Column('changes_summary', sa.Text, nullable=True),
        sa.Column('correlation_id', sa.String(36), nullable=True, index=True),
        sa.Column('event_id', sa.String(36), nullable=True, index=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, index=True),
        sa.Column('hash', sa.String(64), nullable=False, index=True),
        sa.Column('previous_hash', sa.String(64), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
    )


def downgrade():
    op.drop_table('araos_audit_ledger')
    op.drop_table('araos_event_correlations')
    op.drop_table('araos_event_dlq')
    op.drop_table('araos_event_store')
