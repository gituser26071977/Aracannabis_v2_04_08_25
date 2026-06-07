"""ARAOS Week 5: Agent Runtime & Integration Layer

Revision ID: 791ba78aa8fb
Revises: 9b93d2cb67d7
Create Date: 2026-06-07 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '791ba78aa8fb'
down_revision = '9b93d2cb67d7'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Agent Registry ──────────────────────────────────────────────
    op.create_table(
        'araos_agent_registry',
        sa.Column('agent_id', sa.String(100), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('author', sa.String(100), nullable=True),
        sa.Column('capabilities', sa.JSON, nullable=False, default=list),
        sa.Column('required_permissions', sa.JSON, nullable=False, default=list),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('configuration', sa.JSON, nullable=True, default=dict),
        sa.Column('registered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ─── Agent Memory ────────────────────────────────────────────────
    op.create_table(
        'araos_agent_memory',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False, index=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('last_execution_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_event_id', sa.String(36), nullable=True),
        sa.Column('last_event_type', sa.String(100), nullable=True),
        sa.Column('last_patient_id', sa.String(36), nullable=True, index=True),
        sa.Column('last_consultation_id', sa.String(36), nullable=True),
        sa.Column('current_state', sa.JSON, nullable=False, default=dict),
        sa.Column('execution_history', sa.JSON, nullable=False, default=list),
        sa.Column('memory_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('araos_agent_memory')
    op.drop_table('araos_agent_registry')
