"""add catalogo extraction fields and log

Revision ID: f3a8c9d2e1b4_add_catalog_fields
Revises: ec450c16ec01
Create Date: $(date -Iseconds)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a8c9d2e1b4_add_catalog_fields'
down_revision = 'ec450c16ec01'
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona campos à tabela produtos
    op.add_column('produtos', sa.Column('categoria', sa.String(length=100), nullable=True))
    op.add_column('produtos', sa.Column('unidade', sa.String(length=50), nullable=True))
    op.add_column('produtos', sa.Column('concentracao', sa.String(length=50), nullable=True))
    op.add_column('produtos', sa.Column('codigo_barras', sa.String(length=50), nullable=True))

    # Cria tabela catalogo_import_logs
    op.create_table('catalogo_import_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('detected_count', sa.Integer(), nullable=True),
        sa.Column('imported_count', sa.Integer(), nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profissionais.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Cria tabelas faltantes para auth/onboarding
    op.create_table('email_verifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profissionais.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )

    op.create_table('onboarding_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('steps_data', sa.JSON(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['profissionais.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    op.drop_column('produtos', 'categoria')
    op.drop_column('produtos', 'unidade')
    op.drop_column('produtos', 'concentracao')
    op.drop_column('produtos', 'codigo_barras')
    op.drop_table('catalogo_import_logs')
    op.drop_table('email_verifications')
    op.drop_table('onboarding_progress')
