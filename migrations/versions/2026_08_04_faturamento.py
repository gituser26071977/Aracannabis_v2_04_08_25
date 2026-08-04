"""faturamento clinico: convenios, servicos, tabela, repasses, lancamentos

Revision ID: 2026_08_04_faturamento
Revises: 2026_08_02_s2_tenant_uuid
Create Date: 2026-08-04

Módulo de faturamento do atendimento clínico:
- convenios (operadora/consultorio) — valor fixo por serviço
- servicos — tabela particular (valor_particular), base da modalidade PARTICULAR
- tabela_preco_convenios — override do valor por convênio
- percentuais_repasse — % do profissional por serviço (servico_id NULL = global)
- lancamentos_faturamento — conta a receber (convenio_id NULL = PARTICULAR)
- recebimentos — pagamentos parciais/múltiplos do lançamento
"""
from alembic import op
import sqlalchemy as sa


revision = "2026_08_04_faturamento"
down_revision = "2026_08_02_s2_tenant_uuid"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "convenios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False, unique=True),
        sa.Column("registro_ans", sa.String(length=50), nullable=True),
        sa.Column("tipo", sa.String(length=20), server_default="operadora", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "servicos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("tipo", sa.String(length=20), server_default="consulta", nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("valor_particular", sa.Float(), server_default="0", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "tabela_preco_convenios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("convenio_id", sa.Integer(), sa.ForeignKey("convenios.id"), nullable=False),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id"), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("convenio_id", "servico_id", name="uq_tabela_convenio_servico"),
    )

    op.create_table(
        "percentuais_repasse",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id"), nullable=False),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id"), nullable=True),
        sa.Column("percentual", sa.Float(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "profissional_id", "servico_id", name="uq_repasse_profissional_servico"
        ),
    )

    op.create_table(
        "lancamentos_faturamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("associacao_id", sa.Integer(), sa.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("paciente_id", sa.Integer(), sa.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("atendimento_id", sa.Integer(), sa.ForeignKey("consultas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("profissional_id", sa.Integer(), sa.ForeignKey("profissionais.id"), nullable=False),
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id"), nullable=False),
        sa.Column("convenio_id", sa.Integer(), sa.ForeignKey("convenios.id"), nullable=True),
        sa.Column("valor_total", sa.Float(), nullable=False),
        sa.Column("desconto", sa.Float(), server_default="0", nullable=False),
        sa.Column("valor_receber", sa.Float(), nullable=False),
        sa.Column("percentual_repasse", sa.Float(), nullable=False),
        sa.Column("valor_repasse", sa.Float(), nullable=False),
        sa.Column("forma_pagamento", sa.String(length=30), server_default="dinheiro"),
        sa.Column("status", sa.String(length=20), server_default="pendente", nullable=False),
        sa.Column("data_lancamento", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("data_recebimento", sa.DateTime(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "recebimentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lancamento_id", sa.Integer(), sa.ForeignKey("lancamentos_faturamento.id"), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("forma_pagamento", sa.String(length=30), server_default="dinheiro"),
        sa.Column("data", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("criado_por", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("recebimentos")
    op.drop_table("lancamentos_faturamento")
    op.drop_table("percentuais_repasse")
    op.drop_table("tabela_preco_convenios")
    op.drop_table("servicos")
    op.drop_table("convenios")
