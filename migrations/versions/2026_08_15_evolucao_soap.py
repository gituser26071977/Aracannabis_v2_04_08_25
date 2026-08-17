"""evolucoes: campos SOAP estruturados (anamnese, exame fisico, sinais vitais)

Revision ID: 2026_08_15_evolucao_soap
Revises: REDACTED
Create Date: 2026-08-15

Destrincha a evolução livre em campos estruturados (padrão SOAP):
- anamnese (S), exame_fisico (O), sinais_vitais (O), exames_resultados (O),
  avaliacao (A), plano (P).
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_15_evolucao_soap"
down_revision = "REDACTED"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("evolucoes", sa.Column("anamnese", sa.Text(), nullable=True))
    op.add_column("evolucoes", sa.Column("exame_fisico", sa.Text(), nullable=True))
    op.add_column("evolucoes", sa.Column("sinais_vitais", sa.JSON(), nullable=True))
    op.add_column("evolucoes", sa.Column("exames_resultados", sa.Text(), nullable=True))
    op.add_column("evolucoes", sa.Column("avaliacao", sa.Text(), nullable=True))
    op.add_column("evolucoes", sa.Column("plano", sa.Text(), nullable=True))


def downgrade():
    for col in ("plano", "avaliacao", "exames_resultados", "sinais_vitais",
                "exame_fisico", "anamnese"):
        op.drop_column("evolucoes", col)
