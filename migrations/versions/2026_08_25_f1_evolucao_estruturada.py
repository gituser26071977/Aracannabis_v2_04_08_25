"""evolucao estruturada F1: sinais vitais, exame fisico por sistema, diagnosticos (CID)

Revision ID: 2026_08_25_f1_evolucao_estruturada
Revises: 2026_08_15_evolucao_soap
Create Date: 2026-08-25

F1 — módulo base estruturado (convive com o SOAP legado):
- evolucao_sinais_vitais   — medições próprias (PA, FC, FR, T°C, SpO2, glicemia,
                              peso, altura, IMC calculado no backend)
- evolucao_exame_fisico    — exame físico por sistema orgânico
- diagnosticos             — diagnóstico com CID-10, tipo (hipótese/definitivo)
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_25_f1_evolucao_estruturada"
down_revision = "2026_08_15_evolucao_soap"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evolucao_sinais_vitais",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("associacao_id", sa.Integer(), sa.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("evolucao_id", sa.Integer(), sa.ForeignKey("evolucoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id", ondelete="SET NULL"), nullable=True),
        sa.Column("data_medicao", sa.DateTime(), nullable=False),
        sa.Column("pa_sistolica", sa.Integer(), nullable=True),
        sa.Column("pa_diastolica", sa.Integer(), nullable=True),
        sa.Column("fc", sa.Integer(), nullable=True),
        sa.Column("fr", sa.Integer(), nullable=True),
        sa.Column("temperatura", sa.Float(), nullable=True),
        sa.Column("spo2", sa.Integer(), nullable=True),
        sa.Column("glicemia", sa.Float(), nullable=True),
        sa.Column("peso", sa.Float(), nullable=True),
        sa.Column("altura", sa.Float(), nullable=True),
        sa.Column("imc", sa.Float(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_evolucao_sinais_vitais_paciente", "evolucao_sinais_vitais", ["paciente_id", "data_medicao"])

    op.create_table(
        "evolucao_exame_fisico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("associacao_id", sa.Integer(), sa.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("evolucao_id", sa.Integer(), sa.ForeignKey("evolucoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sistema", sa.String(length=64), nullable=False),
        sa.Column("achados", sa.Text(), nullable=True),
        sa.Column("data_exame", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_evolucao_exame_fisico_paciente", "evolucao_exame_fisico", ["paciente_id", "data_exame"])

    op.create_table(
        "diagnosticos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("associacao_id", sa.Integer(), sa.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cid", sa.String(length=16), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default="hipotese"),
        sa.Column("data_diagnostico", sa.DateTime(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_diagnosticos_paciente", "diagnosticos", ["paciente_id", "data_diagnostico"])


def downgrade():
    op.drop_index("ix_diagnosticos_paciente", table_name="diagnosticos")
    op.drop_table("diagnosticos")
    op.drop_index("ix_evolucao_exame_fisico_paciente", table_name="evolucao_exame_fisico")
    op.drop_table("evolucao_exame_fisico")
    op.drop_index("ix_evolucao_sinais_vitais_paciente", table_name="evolucao_sinais_vitais")
    op.drop_table("evolucao_sinais_vitais")
