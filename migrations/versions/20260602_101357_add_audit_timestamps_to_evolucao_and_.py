"""Add audit timestamps to evolucoes and prescricoes

Revision ID: 20260602_101357
Revises: ec450c16ec01
Create Date: 2026-06-02 10:13:57

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260602_101357'
down_revision = 'ec450c16ec01'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at and updated_at to evolucoes
    with op.batch_alter_table('evolucoes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Add created_at and updated_at to prescricoes
    with op.batch_alter_table('prescricoes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove created_at and updated_at from prescricoes
    with op.batch_alter_table('prescricoes', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')

    # Remove created_at and updated_at from evolucoes
    with op.batch_alter_table('evolucoes', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
