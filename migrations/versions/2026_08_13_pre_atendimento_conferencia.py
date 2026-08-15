"""pre_consultas: conferencia + pagamento no pre-atendimento

Revision ID: REDACTED
Revises: 2026_08_13_pre_atendimento
Create Date: 2026-08-13

Adiciona campos de conferência e pagamento para o fluxo de pré-atendimento:
- dados_solicitacao (JSON) — respostas do questionário
- status_pagamento, valor_consulta, preferencia_id, link_pagamento
- conferido_por, conferido_em, pagamento_confirmado_em, rejeitado_motivo
"""
from alembic import op
import sqlalchemy as sa


revision = "REDACTED"
down_revision = "2026_08_13_pre_atendimento"
branch_labels = None
depends_on = None


def upgrade():
    # Pré-atendimento pode não ter paciente até a conferência liberar.
    op.alter_column(
        "pre_consultas",
        "paciente_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column("pre_consultas", sa.Column("dados_solicitacao", sa.JSON(), nullable=True))
    op.add_column("pre_consultas", sa.Column("status_pagamento", sa.String(length=20), server_default="pendente", nullable=False))
    op.add_column("pre_consultas", sa.Column("valor_consulta", sa.Float(), nullable=True))
    op.add_column("pre_consultas", sa.Column("preferencia_id", sa.String(length=64), nullable=True))
    op.add_column("pre_consultas", sa.Column("link_pagamento", sa.String(length=500), nullable=True))
    op.add_column("pre_consultas", sa.Column("conferido_por", sa.String(length=120), nullable=True))
    op.add_column("pre_consultas", sa.Column("conferido_em", sa.DateTime(), nullable=True))
    op.add_column("pre_consultas", sa.Column("pagamento_confirmado_em", sa.DateTime(), nullable=True))
    op.add_column("pre_consultas", sa.Column("rejeitado_motivo", sa.Text(), nullable=True))


def downgrade():
    for col in ("rejeitado_motivo", "pagamento_confirmado_em", "conferido_em",
                "conferido_por", "link_pagamento", "preferencia_id", "valor_consulta",
                "status_pagamento", "dados_solicitacao"):
        op.drop_column("pre_consultas", col)
