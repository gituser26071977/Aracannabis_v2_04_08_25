"""
Sprint 4.5 — Knowledge Persistence Layer.

Cria as tabelas para Clinical Knowledge Engine:

    - clinical_genes                     (projeção de Gene AR)
    - clinical_genomes                   (ClinicalGenome projection)
    - knowledge_correlations             (CorrelationResult)
    - knowledge_hypotheses               (ClinicalHypothesis)
    - knowledge_cohorts                  (Cohort)
    - knowledge_research_sessions        (ResearchSession)
    - knowledge_graphs                   (KnowledgeGraph JSON blob per ADR-0008)

Princípios (Architecture Freeze v1.0):
    - Tenant SEMPRE presente + COMPOSITE PK (tenant_id + entity_id).
    - Cross-tenant queries IMPOSSÍVEIS pela estrutura da PK.
    - FKs apenas para tenant_id → araos_organizations (NO ACTION, não CASCADE).
    - JSON columns para campos variáveis; TEXT para bit-exact round-trip.
    - Soft-delete: deleted_at TIMESTAMPTZ NULL (LGPD/audit compliance).
    - Audit mixin (created_at, updated_at, deleted_at, created_by, updated_by, deleted_by).
    - Forward-chained após `2026_07_22_merge_araos_heads` (G2).

Regras críticas:
    - Composite PKs (tenant_id, ...) — cross-tenant queries IMPOSSÍVEIS.
    - result_json TEXT (não JSONB) para research_sessions — preserva
      bit-exact canonical JSON.
    - graph_json JSONB para knowledge_graphs — ADR-0008 Opção A.

Revision ID: REDACTED
Revises: 2026_07_22_merge_araos_heads
Create Date: 2026-07-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "REDACTED"
down_revision = "2026_07_22_merge_araos_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ────────────────────────────────────────────────────────────────
    # clinical_genes — Projection of ClinicalGene AR
    # Composite PK: (tenant_id, patient_id, gene_id)
    # Gene sem sentido fora do contexto paciente.
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "clinical_genes",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("gene_id", sa.String(96), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("trajectory_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("history_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Audit mixin
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "patient_id", "gene_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_clinical_genes_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_cgenes_tenant_state_hash",
        "clinical_genes",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_cgenes_tenant_patient",
        "clinical_genes",
        ["tenant_id", "patient_id"],
    )

    # ────────────────────────────────────────────────────────────────
    # clinical_genomes — ClinicalGenome projection
    # Composite PK: (tenant_id, genome_id)
    # Genes, correlations, hypotheses são TUPLAS lossless (JSON arrays).
    # NÃO counts apenas — full tuples necessárias para replay.
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "clinical_genomes",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("genome_id", sa.String(96), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_label", sa.String(32), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("graph_snapshot_id", sa.String(96), nullable=True),
        # Lossless tuples — NÃO counts
        sa.Column("genes_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("correlations_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("hypotheses_json", sa.JSON, nullable=False, server_default="[]"),
        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "genome_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_clinical_genomes_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_cgenomes_tenant_state_hash",
        "clinical_genomes",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_cgenomes_tenant_patient",
        "clinical_genomes",
        ["tenant_id", "patient_id"],
    )
    op.create_index(
        "ix_cgenomes_tenant_built_at",
        "clinical_genomes",
        ["tenant_id", "built_at"],
    )

    # ────────────────────────────────────────────────────────────────
    # knowledge_correlations — CorrelationResult
    # Composite PK: (tenant_id, correlation_id)
    # Coefficient em DOUBLE PRECISION para preservar IEEE 754.
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_correlations",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("correlation_id", sa.String(96), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("gene_x_id", sa.String(96), nullable=False),
        sa.Column("gene_y_id", sa.String(96), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("coefficient", sa.Float, nullable=False),
        sa.Column("p_value", sa.Float, nullable=True),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "correlation_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_kcorrelations_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_kcorr_tenant_state_hash",
        "knowledge_correlations",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_kcorr_tenant_patient",
        "knowledge_correlations",
        ["tenant_id", "patient_id"],
    )

    # ────────────────────────────────────────────────────────────────
    # knowledge_hypotheses — ClinicalHypothesis
    # Composite PK: (tenant_id, hypothesis_id)
    # ⚠️ code cross-tenant leak gap (manifest/code): Sprint 4.5+ ADR.
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_hypotheses",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("hypothesis_id", sa.String(96), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("rule_id", sa.String(96), nullable=False),
        sa.Column("claim", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("correlations_used_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "hypothesis_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_khypotheses_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_khyp_tenant_state_hash",
        "knowledge_hypotheses",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_khyp_tenant_patient",
        "knowledge_hypotheses",
        ["tenant_id", "patient_id"],
    )

    # ────────────────────────────────────────────────────────────────
    # knowledge_cohorts — Cohort
    # Composite PK: (tenant_id, cohort_id)
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_cohorts",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("cohort_id", sa.String(96), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("criteria_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("matched_patient_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "cohort_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_kcohorts_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_kcohort_tenant_state_hash",
        "knowledge_cohorts",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_kcohort_tenant_built_at",
        "knowledge_cohorts",
        ["tenant_id", "built_at"],
    )

    # ────────────────────────────────────────────────────────────────
    # knowledge_research_sessions — ResearchSession
    # Composite PK: (tenant_id, session_id)
    # result_json é TEXT (não JSONB) — preserva canonical JSON byte-exact.
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_research_sessions",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(96), nullable=False),
        sa.Column("query_id", sa.String(96), nullable=False),
        sa.Column("cohort_id", sa.String(96), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        # TEXT — bit-exact canonical JSON
        sa.Column("result_json", sa.Text, nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("reproducible", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("explanation_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "session_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_krsessions_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_krsess_tenant_state_hash",
        "knowledge_research_sessions",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_krsess_tenant_cohort",
        "knowledge_research_sessions",
        ["tenant_id", "cohort_id"],
    )

    # ────────────────────────────────────────────────────────────────
    # knowledge_graphs — KnowledgeGraph (ADR-0008 Opção A: JSON blob)
    # Composite PK: (tenant_id, graph_id)
    # graph_json JSONB — preserva payload do to_canonical_dict().
    # ────────────────────────────────────────────────────────────────
    op.create_table(
        "knowledge_graphs",
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("graph_id", sa.String(96), nullable=False),
        sa.Column("patient_id", sa.String(64), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False),
        # JSONB — graph_json do to_canonical_dict()
        sa.Column("graph_json", sa.JSON, nullable=False),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column("deleted_by", sa.String(36), nullable=True),
        sa.PrimaryKeyConstraint("tenant_id", "graph_id"),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["araos_organizations.id"],
            name="fk_kgraphs_tenant",
            ondelete="NO ACTION",
        ),
    )
    op.create_index(
        "ix_kgraphs_tenant_state_hash",
        "knowledge_graphs",
        ["tenant_id", "state_hash"],
    )
    op.create_index(
        "ix_kgraphs_tenant_patient",
        "knowledge_graphs",
        ["tenant_id", "patient_id"],
    )
    op.create_index(
        "ix_kgraphs_tenant_built_at",
        "knowledge_graphs",
        ["tenant_id", "built_at"],
    )


def downgrade() -> None:
    # Drop em ordem inversa de dependência
    op.drop_index("ix_kgraphs_tenant_built_at", table_name="knowledge_graphs")
    op.drop_index("ix_kgraphs_tenant_patient", table_name="knowledge_graphs")
    op.drop_index("ix_kgraphs_tenant_state_hash", table_name="knowledge_graphs")
    op.drop_table("knowledge_graphs")

    op.drop_index("ix_krsess_tenant_cohort", table_name="knowledge_research_sessions")
    op.drop_index("ix_krsess_tenant_state_hash", table_name="knowledge_research_sessions")
    op.drop_table("knowledge_research_sessions")

    op.drop_index("ix_kcohort_tenant_built_at", table_name="knowledge_cohorts")
    op.drop_index("ix_kcohort_tenant_state_hash", table_name="knowledge_cohorts")
    op.drop_table("knowledge_cohorts")

    op.drop_index("ix_khyp_tenant_patient", table_name="knowledge_hypotheses")
    op.drop_index("ix_khyp_tenant_state_hash", table_name="knowledge_hypotheses")
    op.drop_table("knowledge_hypotheses")

    op.drop_index("ix_kcorr_tenant_patient", table_name="knowledge_correlations")
    op.drop_index("ix_kcorr_tenant_state_hash", table_name="knowledge_correlations")
    op.drop_table("knowledge_correlations")

    op.drop_index("ix_cgenomes_tenant_built_at", table_name="clinical_genomes")
    op.drop_index("ix_cgenomes_tenant_patient", table_name="clinical_genomes")
    op.drop_index("ix_cgenomes_tenant_state_hash", table_name="clinical_genomes")
    op.drop_table("clinical_genomes")

    op.drop_index("ix_cgenes_tenant_patient", table_name="clinical_genes")
    op.drop_index("ix_cgenes_tenant_state_hash", table_name="clinical_genes")
    op.drop_table("clinical_genes")
