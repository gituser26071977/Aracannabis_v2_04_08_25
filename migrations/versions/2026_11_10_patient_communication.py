"""Consentimento de comunicação e opt-out do Portal do Paciente.

Adiciona a `pacientes`:
  * aceita_comunicacao_whatsapp (NULL = não informado)
  * opt_out_em, opt_out_motivo
  * convite_portal_enviado_em

E cria `patient_convites` para auditar os convites enviados (LGPD).

Idempotente: usa ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS,
seguindo o padrão das migrations P0-A. Não faz merge das heads paralelas:
down_revision aponta para a head aplicada em produção
(`2026_08_29_vsf_integration`).

Revision ID: 2026_11_10_patient_communication
Revises: 2026_08_29_vsf_integration
Create Date: 2026-11-10
"""

from alembic import op

revision = "2026_11_10_patient_communication"
down_revision = "2026_08_29_vsf_integration"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS "
        "aceita_comunicacao_whatsapp BOOLEAN"
    )
    op.execute(
        "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS opt_out_em TIMESTAMP"
    )
    op.execute(
        "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS opt_out_motivo VARCHAR(255)"
    )
    op.execute(
        "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS "
        "convite_portal_enviado_em TIMESTAMP"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS patient_convites (
            id SERIAL PRIMARY KEY,
            associacao_id INTEGER REFERENCES associacoes(id) ON DELETE CASCADE,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
            canal VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
            template VARCHAR(40),
            status VARCHAR(20) NOT NULL DEFAULT 'pendente',
            provider_id VARCHAR(120),
            erro TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_patient_convites_paciente "
        "ON patient_convites (paciente_id, created_at DESC)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_patient_convites_paciente")
    op.execute("DROP TABLE IF EXISTS patient_convites")
    op.execute("ALTER TABLE pacientes DROP COLUMN IF EXISTS convite_portal_enviado_em")
    op.execute("ALTER TABLE pacientes DROP COLUMN IF EXISTS opt_out_motivo")
    op.execute("ALTER TABLE pacientes DROP COLUMN IF EXISTS opt_out_em")
    op.execute(
        "ALTER TABLE pacientes DROP COLUMN IF EXISTS aceita_comunicacao_whatsapp"
    )
