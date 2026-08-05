"""
AraOS Clinical Intelligence Platform — Sprint 4.1 Foundations.

Sprint 4.1 entrega:
    1. Clinical Timeline Engine — read-side (NÃO cria tabela; consome
       ClinicalEventStore do Sprint 3.1).
    2. Explainability Core — cria a tabela `intelligence_explanations`
       (SQL projection do ExplanationRegistry).

Princípios:
    - Timeline é read-side puro, sem materialização própria. Reusa
       clinical_events table do Sprint 3.1.
    - Explanations SÃO materializadas (write-side leve: cada análise
       registra 1 Explanation). Read queries eficientes.

Revision ID: REDACTED
Revises: 2026_07_16_neuro_registry_s32
Create Date: 2026-07-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "REDACTED"
down_revision = "2026_07_16_neuro_registry_s32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── Explainability Core (write-side projection) ────────────────
    op.create_table(
        "intelligence_explanations",
        sa.Column("id", sa.String(64), primary_key=True),                # explanation_id
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("analysis_id", sa.String(64), nullable=False),
        sa.Column(
            "analysis_type",
            sa.String(32),
            nullable=False,
            comment=(
                "correlation | trend | anomaly | hypothesis | "
                "episode_suggestion | cohort_evaluation | forecast"
            ),
        ),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("method", sa.String(64), nullable=False),
        sa.Column("data_window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_window_label", sa.String(64), nullable=True),
        sa.Column("variables_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("contributing_event_ids_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("assumptions_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("limitations_json", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("analyst", sa.String(64), nullable=False, server_default="system"),
        sa.Column("correlation_id", sa.String(64), nullable=True),
        sa.Column("metadata_json", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Indexes for tenant-isolated queries
    op.create_index(
        "ix_intel_explanations_tenant_id",
        "intelligence_explanations",
        ["tenant_id"],
    )
    op.create_index(
        "REDACTED",
        "intelligence_explanations",
        ["tenant_id", "analysis_id"],
    )
    op.create_index(
        "ix_intel_explanations_tenant_type",
        "intelligence_explanations",
        ["tenant_id", "analysis_type"],
    )
    op.create_index(
        "REDACTED",
        "intelligence_explanations",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "REDACTED",
        "intelligence_explanations",
        ["correlation_id"],
    )

    # ─── Idempotency tracker para timeline views ─────────────────────
    # A Timeline Engine é read-side pura, mas registra queries "pesadas"
    # em processed_query_events para auditoria + idempotência de cache
    # computado. NÃO substitui o processed_events do Registry.
    op.create_table(
        "REDACTED",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("query_kind", sa.String(64), nullable=False),
        sa.Column("query_hash", sa.String(128), nullable=False),
        sa.Column("source_event_id", sa.String(64), nullable=False),
        sa.Column("source_event_type", sa.String(64), nullable=False),
        sa.Column("source_sequence", sa.BigInteger, nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "tenant_id", "query_kind", "query_hash", "source_event_id",
            name="uq_intel_query_processed",
        ),
    )
    op.create_index(
        "ix_intel_query_tenant_kind",
        "REDACTED",
        ["tenant_id", "query_kind"],
    )


def downgrade() -> None:
    op.drop_index("ix_intel_query_tenant_kind", table_name="REDACTED")
    op.drop_table("REDACTED")
    op.drop_index("REDACTED", table_name="intelligence_explanations")
    op.drop_index("REDACTED", table_name="intelligence_explanations")
    op.drop_index("ix_intel_explanations_tenant_type", table_name="intelligence_explanations")
    op.drop_index("REDACTED", table_name="intelligence_explanations")
    op.drop_index("ix_intel_explanations_tenant_id", table_name="intelligence_explanations")
    op.drop_table("intelligence_explanations")