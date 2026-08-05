"""
Sprint 4.5 — Foundation Freeze (post-Gate 1.5).

Adiciona índices compostos de cobertura para queries de listagem
identificadas na revisão de performance (RC1_GATE1_PERFORMANCE_REVIEW.md
§5.2). Apenas aditivo — nenhuma alteração estrutural.

Migration forward-only compatível (Alembic 1.13+).
Idempotente via `IF NOT EXISTS` quando disponível.

Revision ID: REDACTED
Revises: REDACTED
Create Date: 2026-07-22 12:30:00.000000

Razão: reduzir filesort em list_* mantendo os índices tenant-bound.
Não-impacto em produção: índices podem ser criados `CONCURRENTLY` em
zero-downtime deployments (não estamos usando aqui para manter
compatibilidade SQLite nos testes).
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "REDACTED"
down_revision = "REDACTED"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # clinical_genomes — list_genomes ORDER BY (patient_id, window_start, window_end, genome_id)
    op.create_index(
        "ix_cgenomes_tenant_patient_window",
        "clinical_genomes",
        ["tenant_id", "patient_id", "window_start", "window_end"],
    )

    # knowledge_correlations — list_correlations ORDER BY (patient_id, correlation_id)
    op.create_index(
        "ix_kcorr_tenant_patient_corr",
        "knowledge_correlations",
        ["tenant_id", "patient_id", "correlation_id"],
    )

    # knowledge_hypotheses — list_hypotheses ORDER BY (patient_id, hypothesis_id)
    op.create_index(
        "ix_khyp_tenant_patient_hyp",
        "knowledge_hypotheses",
        ["tenant_id", "patient_id", "hypothesis_id"],
    )

    # knowledge_graphs — list_graphs ORDER BY (patient_id, graph_id)
    op.create_index(
        "ix_kgraphs_tenant_patient_graph",
        "knowledge_graphs",
        ["tenant_id", "patient_id", "graph_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_kgraphs_tenant_patient_graph", table_name="knowledge_graphs"
    )
    op.drop_index(
        "ix_khyp_tenant_patient_hyp", table_name="knowledge_hypotheses"
    )
    op.drop_index(
        "ix_kcorr_tenant_patient_corr", table_name="knowledge_correlations"
    )
    op.drop_index(
        "ix_cgenomes_tenant_patient_window", table_name="clinical_genomes"
    )
