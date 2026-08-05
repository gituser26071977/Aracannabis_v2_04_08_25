"""perfil_acesso: coluna de perfil de acesso por esfera (assistencial/administrativo/solo)

Revision ID: 2026_08_04_perfil_acesso
Revises: 2026_08_04_faturamento
Create Date: 2026-08-04

Adiciona `profissionais.perfil_acesso` (NULL = derivado por role/plano).
Resolução em services/perfil_acesso.py: admin/superadmin → solo; auxiliar →
administrativo; assinante de plano individual → solo; senão assistencial.
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_04_perfil_acesso"
down_revision = "2026_08_04_faturamento"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profissionais",
        sa.Column("perfil_acesso", sa.String(length=20), nullable=True),
    )


def downgrade():
    op.drop_column("profissionais", "perfil_acesso")
