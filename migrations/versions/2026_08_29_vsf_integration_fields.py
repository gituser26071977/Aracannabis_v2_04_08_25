"""add VSF integration fields to pacientes and consultas

Revision ID: 2026_08_29_vsf_integration
Revises: 2026_08_25_f1_evolucao_estruturada
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_29_vsf_integration"
down_revision = "2026_08_25_f1_evolucao_estruturada"
branch_labels = None
depends_on = None


def upgrade():
    # Paciente fields
    op.add_column("pacientes", sa.Column("vsf_patient_id", sa.String(), nullable=True))
    op.add_column("pacientes", sa.Column("face_enrolled", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    # Consulta fields
    op.add_column("consultas", sa.Column("vsf_appointment_id", sa.String(), nullable=True))
    op.add_column("consultas", sa.Column("vsf_synced", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("consultas", sa.Column("convenio_id", sa.Integer(), sa.ForeignKey("convenios.id", ondelete="SET NULL"), nullable=True))
    op.add_column("consultas", sa.Column("convenio_nome", sa.String(), nullable=True))


def downgrade():
    op.drop_column("consultas", "convenio_nome")
    op.drop_column("consultas", "convenio_id")
    op.drop_column("consultas", "vsf_synced")
    op.drop_column("consultas", "vsf_appointment_id")
    op.drop_column("pacientes", "face_enrolled")
    op.drop_column("pacientes", "vsf_patient_id")