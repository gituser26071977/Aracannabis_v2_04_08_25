"""onboarding_documentos: documentos enviados no onboarding (upload → OCR)

Revision ID: 2026_08_04_onboarding_documentos
Revises: 2026_08_04_onboarding_pacientes
Create Date: 2026-08-04

Tabela dos documentos (imagem/PDF) enviados no cadastro de pacientes.
`paciente_id` NULL até o paciente ser cadastrado/confirmado (então é vinculado).
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_04_onboarding_documentos"
down_revision = "2026_08_04_onboarding_pacientes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "onboarding_documentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nome_original", sa.String(length=255), nullable=False),
        sa.Column("caminho_arquivo", sa.String(length=500), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=True),
        sa.Column("texto_extraido", sa.Text(), nullable=True),
        sa.Column("confianca", sa.Float(), nullable=True),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("onboarding_documentos")
