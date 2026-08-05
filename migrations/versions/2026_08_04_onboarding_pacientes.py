"""onboarding_pacientes: fila de pendências do cadastro de pacientes

Revision ID: 2026_08_04_onboarding_pacientes
Revises: 2026_08_04_pre_consultas
Create Date: 2026-08-04

Cria `onboarding_pacientes` (padrão SGA): itens pendentes do cadastro
administrativo de pacientes (duplicado / dados incompletos) para confirmação
ou descarte pelo administrativo.
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_04_onboarding_pacientes"
down_revision = "2026_08_04_pre_consultas"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "onboarding_pacientes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=True),
        sa.Column("telefone", sa.String(length=32), nullable=True),
        sa.Column("cpf", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("queixa", sa.Text(), nullable=True),
        sa.Column("origem", sa.String(length=20), server_default="admin", nullable=False),
        sa.Column("dados_sugeridos", sa.JSON(), nullable=True),
        sa.Column("motivo", sa.String(length=30), server_default="dados_incompletos", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pendente", nullable=False),
        sa.Column("duplicado_de", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("onboarding_pacientes")
