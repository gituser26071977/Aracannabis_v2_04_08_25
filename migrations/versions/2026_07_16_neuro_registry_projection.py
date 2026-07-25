"""
AraOS Neurodevelopmental Registry — Projection Tables (Sprint 3.2 / ADR-0002).

Cria as 7 tabelas físicas do Registry (read model rebuildable):

    1. neuro_registry_clinical_identities — Aggregate Root
    2. neuro_registry_diagnoses — Entity
    3. neuro_registry_phenotypes — Entity
    4. neuro_registry_assessments — Entity
    5. neuro_registry_interventions — Aggregate Root
    6. neuro_registry_outcomes — Entity
    7. neuro_registry_processed_events — idempotency tracker

Estas tabelas são PROJECTION — totalmente descartáveis, reconstruíveis
a partir do Event Store. Foreign keys CASCADE permitem wipe + replay.

Revision ID: 2026_07_16_neuro_registry_s32
Revises: 2026_07_15_cee_s31
Create Date: 2026-07-16 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_16_neuro_registry_s32"
down_revision = "2026_07_15_cee_s31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ═══════════════════════════════════════════════════════════════════
    # 1. CLINICAL IDENTITY
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_clinical_identities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("initial_notes", sa.Text, nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archive_reason", sa.String(64), nullable=True),
        sa.Column("diagnosis_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("phenotype_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("assessment_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("intervention_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("outcome_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "patient_id",
            name="REDACTED",
        ),
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_clinical_identities",
        ["tenant_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_clinical_identities",
        ["patient_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_clinical_identities",
        ["tenant_id", "status"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 2. DIAGNOSIS
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_diagnoses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "identity_id",
            sa.String(36),
            sa.ForeignKey(
                "neuro_registry_clinical_identities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("condition_code", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("classification", sa.JSON, nullable=False),
        sa.Column("primary_code", sa.String(64), nullable=True),
        sa.Column("primary_type", sa.String(32), nullable=True),
        sa.Column("severity", sa.String(32), nullable=True),
        sa.Column("onset_date", sa.String(10), nullable=True),
        sa.Column("hypothesised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmation_evidence", sa.JSON, nullable=False),
        sa.Column("remission_type", sa.String(32), nullable=True),
        sa.Column("previous_condition_code", sa.String(64), nullable=True),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_neuro_registry_diag_tenant_id",
        "neuro_registry_diagnoses",
        ["tenant_id"],
    )
    op.create_index(
        "ix_neuro_registry_diag_patient_id",
        "neuro_registry_diagnoses",
        ["patient_id"],
    )
    op.create_index(
        "ix_neuro_registry_diag_identity_id",
        "neuro_registry_diagnoses",
        ["identity_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_diagnoses",
        ["condition_code"],
    )
    op.create_index(
        "ix_neuro_registry_diag_state",
        "neuro_registry_diagnoses",
        ["state"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_diagnoses",
        ["identity_id", "state"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_diagnoses",
        ["tenant_id", "state"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 3. PHENOTYPE
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_phenotypes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "identity_id",
            sa.String(36),
            sa.ForeignKey(
                "neuro_registry_clinical_identities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("phenotype_code", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("onset_date", sa.String(10), nullable=True),
        sa.Column("linked_diagnosis_ids", sa.JSON, nullable=False),
        sa.Column("context", sa.Text, nullable=True),
        sa.Column("observed_by", sa.String(36), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", sa.String(36), nullable=True),
        sa.Column("resolution_reason", sa.Text, nullable=True),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_neuro_registry_pheno_tenant_id",
        "neuro_registry_phenotypes",
        ["tenant_id"],
    )
    op.create_index(
        "ix_neuro_registry_pheno_patient_id",
        "neuro_registry_phenotypes",
        ["patient_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_phenotypes",
        ["identity_id"],
    )
    op.create_index(
        "ix_neuro_registry_pheno_code",
        "neuro_registry_phenotypes",
        ["phenotype_code"],
    )
    op.create_index(
        "ix_neuro_registry_pheno_active",
        "neuro_registry_phenotypes",
        ["is_active"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_phenotypes",
        ["identity_id", "is_active"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 4. ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "identity_id",
            sa.String(36),
            sa.ForeignKey(
                "neuro_registry_clinical_identities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("scale_code", sa.String(50), nullable=False),
        sa.Column("scale_version", sa.String(20), nullable=False),
        sa.Column("applied_by", sa.String(36), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_responses", sa.JSON, nullable=False),
        sa.Column("computed_scores", sa.JSON, nullable=False),
        sa.Column("interpretation", sa.JSON, nullable=False),
        sa.Column("linked_diagnosis_ids", sa.JSON, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="final"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("previous_version_id", sa.String(36), nullable=True),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_neuro_registry_assess_tenant_id",
        "neuro_registry_assessments",
        ["tenant_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_assessments",
        ["patient_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_assessments",
        ["identity_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_assessments",
        ["scale_code"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_assessments",
        ["identity_id", "scale_code"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 5. INTERVENTION
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_interventions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "identity_id",
            sa.String(36),
            sa.ForeignKey(
                "neuro_registry_clinical_identities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("intervention_type", sa.String(32), nullable=False),
        sa.Column("subtype", sa.String(100), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("dose", sa.JSON, nullable=True),
        sa.Column("previous_dose", sa.JSON, nullable=True),
        sa.Column("indication_condition_code", sa.String(64), nullable=True),
        sa.Column("linked_diagnosis_ids", sa.JSON, nullable=False),
        sa.Column("prescriber_id", sa.String(36), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("started_by", sa.String(36), nullable=False),
        sa.Column("start_date", sa.String(10), nullable=False),
        sa.Column("end_date", sa.String(10), nullable=True),
        sa.Column("stop_reason", sa.String(64), nullable=True),
        sa.Column("stop_outcome_summary", sa.Text, nullable=True),
        sa.Column("pause_reason", sa.Text, nullable=True),
        sa.Column("expected_resume_date", sa.String(10), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_paused", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_neuro_registry_int_tenant_id",
        "neuro_registry_interventions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_neuro_registry_int_patient_id",
        "neuro_registry_interventions",
        ["patient_id"],
    )
    op.create_index(
        "ix_neuro_registry_int_identity_id",
        "neuro_registry_interventions",
        ["identity_id"],
    )
    op.create_index(
        "ix_neuro_registry_int_type",
        "neuro_registry_interventions",
        ["intervention_type"],
    )
    op.create_index(
        "ix_neuro_registry_int_state",
        "neuro_registry_interventions",
        ["state"],
    )
    op.create_index(
        "ix_neuro_registry_int_active",
        "neuro_registry_interventions",
        ["is_active"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_interventions",
        ["identity_id", "state"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 6. OUTCOME
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_outcomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column(
            "identity_id",
            sa.String(36),
            sa.ForeignKey(
                "neuro_registry_clinical_identities.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        sa.Column("outcome_type", sa.String(32), nullable=False),
        sa.Column("observed_by", sa.String(36), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", sa.JSON, nullable=False),
        sa.Column("intervention_id", sa.String(36), nullable=True),
        sa.Column("magnitude", sa.String(32), nullable=True),
        sa.Column("severity", sa.String(32), nullable=True),
        sa.Column("causality", sa.String(32), nullable=True),
        sa.Column("action_taken", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("duration_months", sa.Integer, nullable=True),
        sa.Column("responding_domains", sa.JSON, nullable=False),
        sa.Column("non_responding_domains", sa.JSON, nullable=False),
        sa.Column("duration_observed_months", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source_event_ids", sa.JSON, nullable=False),
        sa.Column("last_sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_outcomes",
        ["tenant_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_outcomes",
        ["patient_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_outcomes",
        ["identity_id"],
    )
    op.create_index(
        "ix_neuro_registry_outcome_type",
        "neuro_registry_outcomes",
        ["outcome_type"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_outcomes",
        ["identity_id", "outcome_type"],
    )

    # ═══════════════════════════════════════════════════════════════════
    # 7. PROCESSED EVENTS (idempotency tracker)
    # ═══════════════════════════════════════════════════════════════════
    op.create_table(
        "neuro_registry_processed_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("aggregate_type", sa.String(32), nullable=True),
        sa.Column("aggregate_id", sa.String(36), nullable=True),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("event_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_processed_events",
        ["tenant_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_processed_events",
        ["patient_id"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_processed_events",
        ["event_type"],
    )
    op.create_index(
        "ix_neuro_registry_processed_seq",
        "neuro_registry_processed_events",
        ["sequence"],
    )
    op.create_index(
        "REDACTED",
        "neuro_registry_processed_events",
        ["tenant_id", "sequence"],
    )


def downgrade() -> None:
    # Ordem reversa — tabelas dependentes primeiro
    op.drop_table("neuro_registry_processed_events")
    op.drop_table("neuro_registry_outcomes")
    op.drop_table("neuro_registry_interventions")
    op.drop_table("neuro_registry_assessments")
    op.drop_table("neuro_registry_phenotypes")
    op.drop_table("neuro_registry_diagnoses")
    op.drop_table("neuro_registry_clinical_identities")