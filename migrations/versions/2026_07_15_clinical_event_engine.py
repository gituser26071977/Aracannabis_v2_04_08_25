"""
AraOS Clinical Event Engine — Migration (ADR-0001 / Sprint 3.1).

Cria a tabela `clinical_events` cross-specialty.

Esta é a tabela canônica de eventos clínicos do AraOS. Substitui a
premissa antiga de "cada módulo escreve direto na Timeline".

Single source of truth para:
    - Timeline clínica
    - Dashboards
    - IA clínica
    - Relatórios
    - Observatório Sergipano
    - Pesquisa científica

Adicionar novo event_type = 1 linha em `clinical_events` + 1 entrada
em `araos.clinical.event_store.catalog`. Zero migração Alembic adicional.

Revision ID: 2026_07_15_cee_s31
Revises: 2026_07_15_neuro_s1
Create Date: 2026-07-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_15_cee_s31"
down_revision = "2026_07_15_neuro_s1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinical_events",
        # PK
        sa.Column("id", sa.String(36), primary_key=True),
        # Tenant isolation (FK conceitual — string para flexibilidade)
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("araos_organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Patient (string para suportar UUIDs AraOS + IDs legacy)
        sa.Column("patient_id", sa.String(36), nullable=False),
        # Identidade do evento
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("event_version", sa.String(16), nullable=False, server_default="1.0"),
        sa.Column("event_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_module", sa.String(32), nullable=False),
        # Dados
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("event_metadata", sa.JSON, nullable=False),
        # Aggregate
        sa.Column("aggregate_type", sa.String(32), nullable=True),
        sa.Column("aggregate_id", sa.String(36), nullable=True),
        # Atores
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("created_by_user", sa.String(36), nullable=True),
        # Audit (AuditFieldsMixin + soft delete LGPD)
        sa.Column("created_by_mix", sa.String(36), nullable=True),
        sa.Column("updated_by_mix", sa.String(36), nullable=True),
        sa.Column("deleted_by_mix", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Hash chain SHA-256
        sa.Column("previous_hash", sa.String(64), nullable=True),
        sa.Column("event_hash", sa.String(64), nullable=False),
        # Sequence per-tenant (insertion order, monotonic).
        # Define a ordem canônica da hash chain — independente de
        # event_datetime. Permite integridade da chain mesmo com
        # múltiplos eventos no mesmo timestamp (SQLite precision).
        sa.Column("sequence", sa.BigInteger, nullable=False),
    )

    # ─── Índices ────────────────────────────────────────────────────
    # Query típica: "todos eventos do paciente X ordenados por data"
    op.create_index(
        "REDACTED",
        "clinical_events",
        ["tenant_id", "patient_id", "event_datetime"],
    )
    # Filtros por tipo (dashboards, IA)
    op.create_index(
        "ix_clinical_events_event_type",
        "clinical_events",
        ["event_type"],
    )
    # Reconstrução de projeções a partir de aggregate
    op.create_index(
        "ix_clinical_events_aggregate",
        "clinical_events",
        ["aggregate_type", "aggregate_id"],
    )
    # ETL do observatório
    op.create_index(
        "ix_clinical_events_source_module",
        "clinical_events",
        ["source_module", "event_datetime"],
    )
    # Hot path do hash chain (last_hash por tenant — sequence DESC)
    op.create_index(
        "ix_clinical_events_tenant_sequence",
        "clinical_events",
        ["tenant_id", "sequence"],
    )
    # Soft delete queries
    op.create_index(
        "ix_clinical_events_deleted_at",
        "clinical_events",
        ["deleted_at"],
    )
    # Unicidade da sequence por tenant (integridade da chain)
    op.create_unique_constraint(
        "uq_clinical_events_tenant_sequence",
        "clinical_events",
        ["tenant_id", "sequence"],
    )

    # ─── Tabela de sequence tracking ───────────────────────────────
    # 1 linha por tenant. `last_sequence` = maior sequence atribuído.
    # Próximo sequence = last_sequence + 1.
    op.create_table(
        "clinical_event_sequences",
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("araos_organizations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("last_sequence", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("clinical_event_sequences")
    op.drop_constraint(
        "uq_clinical_events_tenant_sequence", "clinical_events", type_="unique"
    )
    op.drop_index("ix_clinical_events_deleted_at", table_name="clinical_events")
    op.drop_index("ix_clinical_events_tenant_sequence", table_name="clinical_events")
    op.drop_index("ix_clinical_events_source_module", table_name="clinical_events")
    op.drop_index("ix_clinical_events_aggregate", table_name="clinical_events")
    op.drop_index("ix_clinical_events_event_type", table_name="clinical_events")
    op.drop_index(
        "REDACTED", table_name="clinical_events"
    )
    op.drop_table("clinical_events")
