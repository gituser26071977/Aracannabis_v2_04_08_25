"""pre_atendimento: slug publico por profissional + tenant em pre_consultas

Revision ID: 2026_08_13_pre_atendimento
Revises: 2026_08_06_signature_transactions
Create Date: 2026-08-13

- `profissionais.pre_atendimento_slug` (único, nullable): URL pública de
  pré-atendimento do tenant (ex.: 'dr.anderson', 'dr.ueslhe').
- `pre_consultas.associacao_id`: isola pré-consultas por tenant.
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_13_pre_atendimento"
down_revision = "2026_08_06_signature_transactions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profissionais",
        sa.Column("pre_atendimento_slug", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "REDACTED",
        "profissionais",
        ["pre_atendimento_slug"],
    )
    op.add_column(
        "pre_consultas",
        sa.Column(
            "associacao_id",
            sa.Integer(),
            sa.ForeignKey("associacoes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("pre_consultas", "associacao_id")
    op.drop_constraint(
        "REDACTED", "profissionais", type_="unique"
    )
    op.drop_column("profissionais", "pre_atendimento_slug")
