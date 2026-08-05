"""
AraOS Clinical Intelligence Platform — Sprint 4.2 Clinical Context Engine.

Cria as tabelas:
    - clinical_contexts                       (write-side aggregate)
    - clinical_context_relationships          (graph edges)
    - REDACTED (idempotência do Rule Engine)

Princípios:
    - Tenant-isolated (tenant_id sempre presente + indexado).
    - Multi-tenancy estrito — zero leak entre schemas.
    - Audit chain: created_at/updated_at + audit mixin (created_by/updated_by).
    - JSON columns para campos variáveis (observations, links, source_provenance).
    - Idempotência via UniqueConstraint por (tenant, patient, rule, event).
    - Forward-chained após `REDACTED`.

Revision ID: 2026_07_18_clinical_context_s42
Revises: REDACTED
Create Date: 2026-07-18 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_18_clinical_context_s42"
down_revision = "REDACTED"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── clinical_contexts ─────────────────────────────────────────
    op.create_table(
        "clinical_contexts",
        sa.Column("context_id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("patient_id", sa.String(64), nullable=False, index=True),
        sa.Column("context_type", sa.String(48), nullable=False, index=True),
        sa.Column("status", sa.String(24), nullable=False, index=True),
        sa.Column("origin", sa.String(24), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("reason", sa.Text, nullable=False, server_default=""),
        sa.Column("observations_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("source_event_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_event_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_diagnosis_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_phenotype_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_intervention_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_outcome_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("linked_assessment_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("professionals_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("confirmed_by", sa.String(64), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by", sa.String(64), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("suggestion_id", sa.String(64), nullable=True, index=True),
        sa.Column("explanation_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aggregate_version", sa.Integer, nullable=False, server_default="1"),
        # Audit mixin
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )

    # Composite indexes for tenant-isolated queries
    op.create_index(
        "ix_ctx_tenant_patient_status",
        "clinical_contexts",
        ["tenant_id", "patient_id", "status"],
    )
    op.create_index(
        "ix_ctx_tenant_patient_type",
        "clinical_contexts",
        ["tenant_id", "patient_id", "context_type"],
    )
    op.create_index(
        "ix_ctx_tenant_created",
        "clinical_contexts",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_ctx_status_origin",
        "clinical_contexts",
        ["status", "origin"],
    )

    # ─── clinical_context_relationships ────────────────────────────
    op.create_table(
        "clinical_context_relationships",
        sa.Column("relationship_id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("source_context_id", sa.String(64), nullable=False, index=True),
        sa.Column("target_context_id", sa.String(64), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(32), nullable=False, index=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("evidence_event_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        # Audit mixin
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_crel_tenant_source",
        "clinical_context_relationships",
        ["tenant_id", "source_context_id"],
    )
    op.create_index(
        "ix_crel_tenant_target",
        "clinical_context_relationships",
        ["tenant_id", "target_context_id"],
    )
    op.create_index(
        "ix_crel_tenant_type",
        "clinical_context_relationships",
        ["tenant_id", "relationship_type"],
    )

    # ─── REDACTED ────────────────
    # Idempotência do Rule Engine.
    # PK não é obrigatória (id auto) mas UniqueConstraint garante
    # exactly-once por (tenant, patient, rule, event).
    op.create_table(
        "REDACTED",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("suggestion_id", sa.String(64), nullable=False),
        sa.Column("context_id", sa.String(64), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "patient_id", "rule_id", "event_id",
            name="uq_ctx_processed_rule_eval",
        ),
    )
    op.create_index(
        "ix_ctx_processed_tenant_patient",
        "REDACTED",
        ["tenant_id", "patient_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ctx_processed_tenant_patient", table_name="REDACTED")
    op.drop_table("REDACTED")

    op.drop_index("ix_crel_tenant_type", table_name="clinical_context_relationships")
    op.drop_index("ix_crel_tenant_target", table_name="clinical_context_relationships")
    op.drop_index("ix_crel_tenant_source", table_name="clinical_context_relationships")
    op.drop_table("clinical_context_relationships")

    op.drop_index("ix_ctx_status_origin", table_name="clinical_contexts")
    op.drop_index("ix_ctx_tenant_created", table_name="clinical_contexts")
    op.drop_index("ix_ctx_tenant_patient_type", table_name="clinical_contexts")
    op.drop_index("ix_ctx_tenant_patient_status", table_name="clinical_contexts")
    op.drop_table("clinical_contexts")
