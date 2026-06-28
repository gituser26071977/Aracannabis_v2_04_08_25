"""Add data_revogacao to pacientes (P0-A FASE 2 — reconciliacao)

Adiciona coluna data_revogacao (TIMESTAMP, nullable) a tabela `pacientes`.

Contexto (bug detectado em teste de carga 2026-06-22):
  - models.py:215 define `data_revogacao = db.Column(db.DateTime)`
  - nenhuma migration gerava essa coluna
  - `db.create_all()` no startup e um no-op para tabelas ja existentes
  - qualquer query em Paciente dispara SELECT da coluna inexistente
  - causa 500 em GET /api/dashboard/stats e GET /api/pacientes em producao

Esta migration e IDEMPOTENTE (usa IF NOT EXISTS) e NAO destrutiva.
Foi adicionada com down_revision = '2026_06_21_add_modulos' (head mais
recente). NAO foi feito merge das demais heads nesta fase (4 chains
paralelas permanecem). Decisao deliberada para nao reorganizar o
Alembic dentro do escopo P0-A.

Para aplicar em producao (alem do `flask db upgrade`):
  - ja e idempotente, entao rodar 2x nao quebra
  - em situacao de emergencia, o SQL pode ser executado direto:
        ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;
    seguido de `flask db stamp REDACTED`
    para registrar formalmente no alembic_version.

Revision ID: REDACTED
Revises: 2026_06_21_add_modulos
Create Date: 2026-06-22 ...
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'REDACTED'
down_revision = '2026_06_21_add_modulos'
branch_labels = None
depends_on = None


def upgrade():
    # Idempotente: ADD COLUMN IF NOT EXISTS nao falha se ja existir
    # Tipo: TIMESTAMP (sem timezone) para casar com db.DateTime do SQLAlchemy
    # Nullable: sim (sem NOT NULL) para casar com db.Column(db.DateTime) do model
    op.execute("ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP")


def downgrade():
    # IF EXISTS para que o downgrade seja seguro em qualquer estado
    op.execute("ALTER TABLE pacientes DROP COLUMN IF EXISTS data_revogacao")
