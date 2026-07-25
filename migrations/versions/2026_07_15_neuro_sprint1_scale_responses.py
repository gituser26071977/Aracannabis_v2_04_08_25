"""
AraOS Neurodevelopmental Module — Sprint 1 Migration.

Cria a tabela `neuro_scale_responses` para persistência polimórfica
de respostas de escalas neuropsicológicas.

Sprint 1 entrega apenas esta tabela (núcleo do plugin subsystem).
Tabelas adicionais virão nos sprints seguintes:
    - Sprint 3: neuro_patient_profiles, neuro_conditions_catalog
    - Sprint 4: neuro_medications, neuro_medication_doses, neuro_cannabis_regimens
    - Sprint 5: neuro_graph_configs, neuro_reports, neuro_research_exports

Revision ID: 2026_07_15_neuro_s1
Revises: a1b2c3d4e5f6
Create Date: 2026-07-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_15_neuro_s1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "neuro_scale_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        # Tenant isolation — FK conceitual (string) para suportar
        # UUIDs do AraOS Platform sem acoplar a schema organizations
        sa.Column("tenant_id", sa.String(36), nullable=False),
        # Paciente — string para suportar tanto UUIDs AraOS quanto IDs legacy
        sa.Column("patient_id", sa.String(36), nullable=False),
        # Identificação da escala
        sa.Column("scale_code", sa.String(50), nullable=False),
        sa.Column("scale_version", sa.String(20), nullable=False),
        # Respostas brutas (validadas contra ScaleSpec.json_schema no runner)
        sa.Column("raw_responses", sa.JSON, nullable=False),
        # Scores calculados (cache — sempre deriváveis de raw_responses)
        sa.Column("computed_scores", sa.JSON, nullable=False),
        # Interpretação (band, label_pt, color, recommendation, references)
        sa.Column("interpretation", sa.JSON, nullable=False),
        # Metadados extras (idade, observador, contexto, flags de segurança)
        sa.Column("extra_metadata", sa.JSON, nullable=False),
        # Controle de aplicação
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_by", sa.String(36), nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="ui"),
        sa.Column("status", sa.String(20), nullable=False, server_default="final"),
        # Audit fields (AuditFieldsMixin)
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ─── Índices ────────────────────────────────────────────────────
    # tenant_id + soft-delete (queries padrão)
    op.create_index(
        "ix_neuro_scale_resp_tenant_id", "neuro_scale_responses", ["tenant_id"]
    )
    op.create_index(
        "ix_neuro_scale_resp_patient_id", "neuro_scale_responses", ["patient_id"]
    )
    op.create_index(
        "ix_neuro_scale_resp_scale_code", "neuro_scale_responses", ["scale_code"]
    )
    op.create_index(
        "ix_neuro_scale_resp_applied_at", "neuro_scale_responses", ["applied_at"]
    )
    op.create_index(
        "ix_neuro_scale_resp_status", "neuro_scale_responses", ["status"]
    )
    op.create_index(
        "ix_neuro_scale_resp_created_by", "neuro_scale_responses", ["created_by"]
    )

    # Índices compostos (queries frequentes em dashboards e timelines)
    op.create_index(
        "ix_neuro_scale_resp_patient_scale",
        "neuro_scale_responses",
        ["patient_id", "scale_code"],
    )
    op.create_index(
        "ix_neuro_scale_resp_tenant_applied",
        "neuro_scale_responses",
        ["tenant_id", "applied_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_neuro_scale_resp_tenant_applied", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_patient_scale", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_created_by", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_status", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_applied_at", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_scale_code", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_patient_id", table_name="neuro_scale_responses")
    op.drop_index("ix_neuro_scale_resp_tenant_id", table_name="neuro_scale_responses")
    op.drop_table("neuro_scale_responses")