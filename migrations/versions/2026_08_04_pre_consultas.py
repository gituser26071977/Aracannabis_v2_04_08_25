"""pre_consultas: tabela de pre-consultas do intake vinculadas ao paciente + relaxa data_nascimento

Revision ID: 2026_08_04_pre_consultas
Revises: 2026_08_04_perfil_acesso
Create Date: 2026-08-04

- Cria `pre_consultas` (pré-consulta do Ara Intake vinculada ao paciente SIAP,
  alimenta o Daily Board do médico com queixa/status).
- `pacientes.data_nascimento` passa a ser nullable (autoregistro pelo intake
  nem sempre coleta data de nascimento).
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_04_pre_consultas"
down_revision = "2026_08_04_perfil_acesso"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pre_consultas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("queixa_principal", sa.Text(), nullable=True),
        sa.Column("intensidade", sa.String(length=20), nullable=True),
        sa.Column("canal", sa.String(length=20), server_default="web", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="concluida", nullable=False),
        sa.Column("intake_interview_id", sa.String(length=64), nullable=True, unique=True),
        sa.Column("araos_patient_id", sa.String(length=64), nullable=True),
        sa.Column("gene_expressions", sa.JSON(), nullable=True),
        sa.Column("data_pre_consulta", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.alter_column("pacientes", "data_nascimento", existing_type=sa.Date(), nullable=True)
    op.alter_column(
        "pacientes", "profissional_responsavel_id",
        existing_type=sa.Integer(), nullable=True,
    )


def downgrade():
    op.alter_column(
        "pacientes", "profissional_responsavel_id",
        existing_type=sa.Integer(), nullable=False,
    )
    op.alter_column("pacientes", "data_nascimento", existing_type=sa.Date(), nullable=False)
    op.drop_table("pre_consultas")
