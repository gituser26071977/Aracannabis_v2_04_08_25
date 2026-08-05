"""
Sprint S2 — Commit C1: tenant_uuid mapping column.

Adiciona coluna ``tenant_uuid`` (String(36) UUID) à tabela ``associacoes``.

Esta coluna estabelece o mapping entre:
  - ``associacoes.id`` (Integer, legacy SaaS) — fonte primária atual
  - ``araos_organizations.id`` (String(36) UUID, AraOS) — fonte canônica futura

A coluna é:
  - nullable (rollback friendly)
  - backfilled automaticamente com UUID v5 determinístico por
    ``associacao.id`` (idempotente — re-executar upgrade() não colide)
  - unique (constraint criada após backfill para evitar conflito transitório)
  - indexada (lookups pelo bridge ``g.tenant_id_canonical`` → ``associacao_id``)

Decisão arquitetural (ver SPRINT_S2_DESIGN §FASE 8 RISCO AR-2, opção C
recomendada): mapping table approach. Não renomeamos ``associacao_id``
para ``tenant_id`` (custo altíssimo); adicionamos coluna paralela que
permite a AraOS emitir tokens com ``tenant_id`` UUID canônico, e o bridge
resolve para ``associacao_id`` Integer via esta coluna.

Revision ID: 2026_08_02_s2_tenant_uuid
Revises: e41413efd37a
Create Date: 2026-08-02 00:00:00.000000
"""

import uuid

import sqlalchemy as sa
from alembic import op


# ── Identifiers ────────────────────────────────────────────────────────
revision = "2026_08_02_s2_tenant_uuid"
down_revision = "e41413efd37a"
branch_labels = None
depends_on = None


# ── Constants ──────────────────────────────────────────────────────────
# UUID v5 namespace para backfill determinístico.
# Permite re-executar upgrade() sem colidir (idempotência).
# REDACTED é um valor arbitrário estável
# (não colide com namespaces padrão da stdlib).
_TENANT_UUID_NS = uuid.UUID("REDACTED")


def upgrade() -> None:
    """Adiciona coluna, backfilla, cria constraint UNIQUE e índice."""

    # 1. Adicionar coluna (nullable para backfill seguro)
    op.add_column(
        "associacoes",
        sa.Column("tenant_uuid", sa.String(36), nullable=True),
    )

    # 2. Backfill: UUID v5 determinístico por associacao.id
    #    SELECT + UPDATE em transação (rollback on error).
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT id FROM associacoes WHERE tenant_uuid IS NULL")
    ).fetchall()
    for row in rows:
        assoc_id = row[0]
        # uuid5(namespace, name) é determinístico — mesmo input, mesmo output.
        tenant_uuid = str(uuid.uuid5(_TENANT_UUID_NS, f"associacao:{assoc_id}"))
        bind.execute(
            sa.text("UPDATE associacoes SET tenant_uuid = :tid WHERE id = :id"),
            {"tid": tenant_uuid, "id": assoc_id},
        )

    # 3. UNIQUE INDEX (substitui CREATE UNIQUE CONSTRAINT — cross-DB compat:
    #    PostgreSQL e SQLite. Semantically equivalent para INSERT: ambos
    #    rejeitam duplicatas. SQLite não suporta ALTER TABLE ADD CONSTRAINT).
    op.create_index(
        "uq_associacoes_tenant_uuid",
        "associacoes",
        ["tenant_uuid"],
        unique=True,
    )


def downgrade() -> None:
    """Remove índice e coluna. Restore original schema."""
    op.drop_index("uq_associacoes_tenant_uuid", table_name="associacoes")
    op.drop_column("associacoes", "tenant_uuid")
