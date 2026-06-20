"""add slug and feature flags to planos

Revision ID: 2026_06_17_clinica_management
Revises: d3e4f5a6b7c8
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
down_revision = 'd3e4f5a6b7c8'
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

    # 4. Seed dos 3 planos canônicos (basico, premium, enterprise) se faltarem
    op.execute("""
        INSERT INTO planos (nome, slug, descricao, preco_mensal,
                            limite_pacientes, limite_agentes_ia, limite_armazenamento_mb,
                            cor, is_popular, ativo,
                            permite_gestao_clinica, permite_agentes_sdr, permite_chatbot_ia,
                            created_at, updated_at)
        SELECT * FROM (VALUES
            ('Plano Sem IA',     'basico',
             'Para profissionais que querem apenas prontuário digital e gestão clínica.',
             99.0::float,  100,   0,  5120,
             '#2196F3', false, true, false, false, false, NOW(), NOW()),
            ('Plano Com IA',     'premium',
             'Inclui agentes de IA (EuSouLia, chatbot médico), dashboard SDR e automações.',
             249.0::float, 500,   10, 10240,
             '#FF9800', true,  true, true,  true,  true,  NOW(), NOW()),
            ('Plano Enterprise', 'enterprise',
             'Clínicas multi-unidade: VSF, reconhecimento facial, métricas avançadas.',
             499.9::float, 99999, 50, 10240,
             '#7B1FA2', false, true, true,  true,  true,  NOW(), NOW())
        ) AS novos(nome, slug, descricao, preco_mensal,
                   limite_pacientes, limite_agentes_ia, limite_armazenamento_mb,
                   cor, is_popular, ativo,
                   permite_gestao_clinica, permite_agentes_sdr, permite_chatbot_ia,
                   created_at, updated_at)
        WHERE NOT EXISTS (SELECT 1 FROM planos WHERE slug IN ('basico', 'premium', 'enterprise'))
    """)


def downgrade():
    # Reverte na ordem inversa
    op.drop_constraint('uq_planos_slug', 'planos', type_='unique')
    op.drop_column('planos', 'permite_chatbot_ia')
    op.drop_column('planos', 'permite_agentes_sdr')
    op.drop_column('planos', 'permite_gestao_clinica')
    op.drop_column('planos', 'slug')