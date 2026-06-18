"""add slug and feature flags to planos

Revision ID: 2026_06_17_clinica_management
Revises: 2026_06_16_p0_13
Create Date: 2026-06-17 03:00:00

Adiciona colunas em `planos` para suportar gating de features por tier:
- `slug` (String 64, unique) — canônico: 'basico' | 'premium' | 'enterprise'
- `permite_gestao_clinica` (Boolean, default False)
- `permite_agentes_sdr` (Boolean, default False)
- `permite_chatbot_ia` (Boolean, default False)

Backfill:
- sem_ia → slug=basico, permite_gestao_clinica=False
- com_ia → slug=premium, permite_gestao_clinica=True

Insere plano `enterprise` se não existir (preço R$499,90, slug=enterprise,
permite_gestao_clinica=True, permite_agentes_sdr=True, permite_chatbot_ia=True).

Parte da feature Gestão da Clínica (PLANO_NOVOS_MODULOS).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_06_17_clinica_management'
down_revision = '2026_06_16_p0_13'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Adiciona colunas novas (nullable inicialmente para backfill seguro)
    op.add_column('planos', sa.Column('slug', sa.String(length=64), nullable=True))
    op.add_column('planos', sa.Column('permite_gestao_clinica', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('planos', sa.Column('permite_agentes_sdr', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('planos', sa.Column('permite_chatbot_ia', sa.Boolean(), nullable=False, server_default='false'))

    # 2. Backfill slug + permite_gestao_clinica com base em `nome` existente
    op.execute("""
        UPDATE planos
        SET slug = CASE
                WHEN nome = 'sem_ia' THEN 'basico'
                WHEN nome = 'com_ia' THEN 'premium'
                WHEN nome = 'basico' THEN 'basico'
                WHEN nome = 'premium' THEN 'premium'
                WHEN nome = 'enterprise' THEN 'enterprise'
                ELSE LOWER(REPLACE(nome, ' ', '_'))
            END,
            permite_gestao_clinica = CASE
                WHEN nome = 'com_ia' THEN true
                WHEN nome = 'premium' THEN true
                WHEN nome = 'enterprise' THEN true
                ELSE false
            END,
            permite_agentes_sdr = CASE
                WHEN nome = 'com_ia' THEN true
                WHEN nome = 'premium' THEN true
                WHEN nome = 'enterprise' THEN true
                ELSE false
            END,
            permite_chatbot_ia = CASE
                WHEN nome = 'com_ia' THEN true
                WHEN nome = 'premium' THEN true
                WHEN nome = 'enterprise' THEN true
                ELSE false
            END
    """)

    # 3. Cria índice/constraint unique em slug (depois do backfill)
    op.create_unique_constraint('uq_planos_slug', 'planos', ['slug'])

    # 4. Insere plano enterprise se não existir
    op.execute("""
        INSERT INTO planos (nome, slug, descricao, preco_mensal,
                            limite_pacientes, limite_agentes_ia, limite_armazenamento_mb,
                            cor, is_popular, ativo,
                            permite_gestao_clinica, permite_agentes_sdr, permite_chatbot_ia,
                            created_at, updated_at)
        SELECT 'enterprise', 'enterprise', 'Plano Enterprise — Clínicas multi-unidade, recursos avançados', 499.90,
               99999, 50, 10240,
               '#7B1FA2', true, true,
               true, true, true,
               NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM planos WHERE slug = 'enterprise')
    """)


def downgrade():
    # Reverte na ordem inversa
    op.drop_constraint('uq_planos_slug', 'planos', type_='unique')
    op.drop_column('planos', 'permite_chatbot_ia')
    op.drop_column('planos', 'permite_agentes_sdr')
    op.drop_column('planos', 'permite_gestao_clinica')
    op.drop_column('planos', 'slug')