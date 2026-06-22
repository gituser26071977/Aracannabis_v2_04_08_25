"""add modulos, modulos_assinaturas, modulos_consentimentos tables

Revision ID: 2026_06_21_add_modulos
Revises: 2026_06_17_clinica_management
Create Date: 2026-06-21 16:50:00

Cria as tabelas do sistema de Módulos de Especialidade:
- `modulos` — catálogo de módulos disponíveis
- `modulos_assinaturas` — vínculo profissional-modulo (trial / active / expired / cancelled)
- `modulos_consentimentos` — termo de consentimento LGPD aceito pelo profissional

Insere seed com 5 módulos canônicos:
- base (sempre incluso, preco 0)
- cannabis-medicinal
- nutrologia
- psiquiatria
- cardiologia
- pesquisa-clinica
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026_06_21_add_modulos'
down_revision = '2026_06_17_clinica_management'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # ── 1. Tabela `modulos` ───────────────────────────────────────
    modulos_table = op.create_table(
        'modulos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(length=64), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('descricao_curta', sa.String(length=200), nullable=True),
        sa.Column('icone', sa.String(length=64), nullable=True, server_default='extension'),
        sa.Column('cor', sa.String(length=16), nullable=True, server_default='#0d7377'),
        sa.Column('preco_mensal', sa.Float(), nullable=True, server_default='0'),
        sa.Column('plano_minimo_slug', sa.String(length=64), nullable=True, server_default='basico'),
        sa.Column('ordem', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('requer_consentimento_lgpd', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('politica_versao', sa.String(length=16), nullable=True, server_default='v1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_modulos_slug', 'modulos', ['slug'], unique=True)

    # ── 2. Tabela `modulos_assinaturas` ───────────────────────────
    op.create_table(
        'modulos_assinaturas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profissional_id', sa.Integer(), nullable=False),
        sa.Column('modulo_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='trial'),
        sa.Column('trial_iniciado_em', sa.DateTime(), nullable=True),
        sa.Column('trial_expira_em', sa.DateTime(), nullable=True),
        sa.Column('ativo_desde', sa.DateTime(), nullable=True),
        sa.Column('expira_em', sa.DateTime(), nullable=True),
        sa.Column('cancelado_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profissional_id'], ['profissionais.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('profissional_id', 'modulo_id', name='uq_modulo_assinatura_user_mod'),
    )
    op.create_index('REDACTED', 'modulos_assinaturas', ['profissional_id'])
    op.create_index('ix_modulos_assinaturas_modulo_id', 'modulos_assinaturas', ['modulo_id'])

    # ── 3. Tabela `modulos_consentimentos` ────────────────────────
    op.create_table(
        'modulos_consentimentos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profissional_id', sa.Integer(), nullable=False),
        sa.Column('modulo_id', sa.Integer(), nullable=False),
        sa.Column('aceito', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('politica_versao', sa.String(length=16), nullable=False),
        sa.Column('ip_origem', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=256), nullable=True),
        sa.Column('aceito_em', sa.DateTime(), nullable=True),
        sa.Column('revogado_em', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['modulo_id'], ['modulos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profissional_id'], ['profissionais.id'], ondelete='CASCADE'),
    )
    op.create_index('REDACTED', 'modulos_consentimentos', ['profissional_id'])
    op.create_index('REDACTED', 'modulos_consentimentos', ['modulo_id'])

    # ── 4. Seed dos módulos canônicos ─────────────────────────────
    # Idempotente: só insere se nenhum dos slugs existir ainda.
    op.execute("""
        INSERT INTO modulos (slug, nome, descricao, descricao_curta, icone, cor,
                             preco_mensal, plano_minimo_slug, ordem, ativo,
                             requer_consentimento_lgpd, politica_versao,
                             created_at, updated_at)
        SELECT * FROM (VALUES
            ('base',
             'Módulo Base',
             'Funcionalidades essenciais de prontuário, agenda, prescrição e LGPD. Incluso em todos os planos pagos.',
             'Prontuário, agenda e prescrição.',
             'dashboard', '#0d7377', 0.0, 'basico', 0, true, false, 'v1',
             NOW(), NOW()),

            ('cannabis-medicinal',
             'Cannabis Medicinal',
             'Módulo completo para clínicas de cannabis medicinal: anamnese direcionada, perfil canabinoide, plano terapêutico com CBD/THC, monitoramento de efeitos e relatórios ANVISA.',
             'Anamnese canabinoide, prescrição CBD/THC, relatórios ANVISA.',
             'eco', '#0d7377', 99.0, 'premium', 10, true, true, 'v1',
             NOW(), NOW()),

            ('nutrologia',
             'Nutrologia',
             'Avaliação antropométrica, plano alimentar, controle de macros e micronutrientes, gráficos de evolução.',
             'Antropometria, plano alimentar e bioimpedância.',
             'restaurant', '#f5a623', 89.0, 'basico', 20, true, true, 'v1',
             NOW(), NOW()),

            ('psiquiatria',
             'Psiquiatria',
             'Escalas validadas (PHQ-9, GAD-7, Beck), plano psicofarmacológico, diário de humor e relatórios CID-10/CID-11.',
             'PHQ-9, GAD-7, Beck, diário de humor.',
             'psychology', '#7B1FA2', 89.0, 'basico', 30, true, true, 'v1',
             NOW(), NOW()),

            ('cardiologia',
             'Cardiologia',
             'ECG digital, calculadora de risco cardiovascular (Framingham, SCORE), controle pressórico e dislipidemia.',
             'ECG digital, risco cardiovascular.',
             'favorite', '#c62828', 89.0, 'premium', 40, true, true, 'v1',
             NOW(), NOW()),

            ('pesquisa-clinica',
             'Pesquisa Clínica',
             'CRF eletrônico, gestão de participantes, consentimento livre e esclarecido, exportação para SPSS/R.',
             'CRF eletrônico, ICF, exportação SPSS/R.',
             'science', '#2e7d32', 149.0, 'enterprise', 50, true, true, 'v1',
             NOW(), NOW())
        ) AS novos(slug, nome, descricao, descricao_curta, icone, cor,
                   preco_mensal, plano_minimo_slug, ordem, ativo,
                   requer_consentimento_lgpd, politica_versao,
                   created_at, updated_at)
        WHERE NOT EXISTS (SELECT 1 FROM modulos WHERE slug IN
            ('base', 'cannabis-medicinal', 'nutrologia', 'psiquiatria',
             'cardiologia', 'pesquisa-clinica'))
    """)


def downgrade():
    op.drop_index('REDACTED', table_name='modulos_consentimentos')
    op.drop_index('REDACTED', table_name='modulos_consentimentos')
    op.drop_table('modulos_consentimentos')

    op.drop_index('ix_modulos_assinaturas_modulo_id', table_name='modulos_assinaturas')
    op.drop_index('REDACTED', table_name='modulos_assinaturas')
    op.drop_table('modulos_assinaturas')

    op.drop_index('ix_modulos_slug', table_name='modulos')
    op.drop_table('modulos')