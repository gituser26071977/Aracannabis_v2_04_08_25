"""digital_signature_configs: certificação digital por profissional (Bird ID)

Revision ID: 2026_08_06_digital_signature
Revises: 2026_08_04_onboarding_documentos
Create Date: 2026-08-06

Tabela de configuração de assinatura digital (provedor + credenciais) usada
para prescrições, laudos e relatórios.
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_06_digital_signature"
down_revision = "2026_08_04_onboarding_documentos"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "digital_signature_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("provedor", sa.String(length=30), server_default="birdid", nullable=False),
        sa.Column("client_id", sa.String(length=200), nullable=False),
        sa.Column("client_secret", sa.String(length=500), nullable=False),
        sa.Column("base_url", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="pendente", nullable=False),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("digital_signature_configs")
