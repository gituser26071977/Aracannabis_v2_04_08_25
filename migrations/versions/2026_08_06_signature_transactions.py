"""certificate_alias + signature_transactions (fluxo CESS/Bird ID)

Revision ID: 2026_08_06_signature_transactions
Revises: 2026_08_06_digital_signature
Create Date: 2026-08-06

- digital_signature_configs: client_id/client_secret ficam nullable
  (credenciais corporativas podem vir de env) + coluna certificate_alias
- nova tabela signature_transactions (rastreia o TCN da assinatura CESS)
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_06_signature_transactions"
down_revision = "2026_08_06_digital_signature"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("digital_signature_configs", "client_id", existing_type=sa.String(length=200), nullable=True)
    op.alter_column("digital_signature_configs", "client_secret", existing_type=sa.String(length=500), nullable=True)
    op.add_column(
        "digital_signature_configs",
        sa.Column("certificate_alias", sa.String(length=300), nullable=True),
    )

    op.create_table(
        "signature_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("config_id", sa.Integer(), sa.ForeignKey("digital_signature_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tcn", sa.String(length=64), nullable=False, unique=True),
        sa.Column("documento_nome", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="aguardando", nullable=False),
        sa.Column("resultado_url", sa.String(length=500), nullable=True),
        sa.Column("documento_assinado", sa.LargeBinary(), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("signature_transactions")
    op.drop_column("digital_signature_configs", "certificate_alias")
    op.alter_column("digital_signature_configs", "client_secret", existing_type=sa.String(length=500), nullable=False)
    op.alter_column("digital_signature_configs", "client_id", existing_type=sa.String(length=200), nullable=False)
