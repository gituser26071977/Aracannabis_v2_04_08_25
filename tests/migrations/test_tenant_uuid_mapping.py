"""
Sprint S2 — Commit C1: tests for tenant_uuid mapping migration.

Tests the migration ``2026_08_02_s2_tenant_uuid_mapping.py`` in isolation
using SQLite in-memory. No Flask app required (C1 is DB-only).

Tests (per spec §FASE 6 COMMIT C1):
  1. REDACTED — upgrade() backfills all
     existing associacoes with valid UUIDs.
  2. test_insert_preserves_tenant_uuid — after upgrade, INSERT with
     explicit tenant_uuid works.
  3. REDACTED — UNIQUE constraint rejects
     duplicate tenant_uuid.
  4. test_downgrade_roundtrip — downgrade() removes column and restores
     original schema (idempotência do rollback).
"""

import importlib.util
import os
import uuid

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError


# ── Path constants ─────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_MIGRATION_FILE = os.path.join(
    _PROJECT_ROOT,
    "migrations",
    "versions",
    "2026_08_02_s2_tenant_uuid_mapping.py",
)
_MIGRATION_MODULE_NAME = "REDACTED"


def _import_migration():
    """Import the migration module by absolute path."""
    spec = importlib.util.spec_from_file_location(
        _MIGRATION_MODULE_NAME, _MIGRATION_FILE
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _apply_op(engine, fn):
    """Run a migration op function within an Alembic Operations context."""
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            fn()


# ── Fixtures ───────────────────────────────────────────────────────────
@pytest.fixture()
def db_engine():
    """In-memory SQLite with minimal associacoes table (legacy schema)."""
    engine = create_engine("sqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                CREATE TABLE associacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR NOT NULL,
                    slug VARCHAR,
                    cnpj VARCHAR UNIQUE NOT NULL,
                    endereco VARCHAR,
                    telefone VARCHAR,
                    email VARCHAR,
                    ativo BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
    yield engine
    engine.dispose()


# ── Tests ──────────────────────────────────────────────────────────────
def REDACTED(db_engine):
    """Test 1 (spec): upgrade() backfills all existing associacoes with valid UUIDs."""
    mod = _import_migration()

    # Seed 3 associacoes
    with db_engine.begin() as conn:
        for i in range(1, 4):
            conn.execute(
                sa.text(
                    "INSERT INTO associacoes (nome, cnpj) VALUES (:n, :c)"
                ),
                {"n": f"assoc_{i}", "c": f"00.000.000/0001-{i:02d}"},
            )

    # Apply upgrade
    _apply_op(db_engine, mod.upgrade)

    # Verify all 3 have valid UUIDs
    with db_engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT id, tenant_uuid FROM associacoes ORDER BY id"
            )
        ).fetchall()

    assert len(rows) == 3
    uuids = []
    for row in rows:
        assoc_id, tenant_uuid = row
        # Must be valid UUID
        parsed = uuid.UUID(tenant_uuid)
        # Must be UUID v5 (deterministic per spec)
        assert parsed.version == 5, f"expected UUID v5, got v{parsed.version}"
        # tenant_uuid must equal uuid5(NS, f"associacao:{id}")
        expected = str(
            uuid.uuid5(
                uuid.UUID("REDACTED"),
                f"associacao:{assoc_id}",
            )
        )
        assert tenant_uuid == expected, (
            f"backfill not deterministic: id={assoc_id} "
            f"got={tenant_uuid} expected={expected}"
        )
        uuids.append(tenant_uuid)

    # All UUIDs must be unique
    assert len(set(uuids)) == 3


def test_insert_preserves_tenant_uuid(db_engine):
    """Test 2 (spec): after upgrade, new INSERT with explicit tenant_uuid works."""
    mod = _import_migration()

    # Apply upgrade first
    _apply_op(db_engine, mod.upgrade)

    # Insert new associacao with explicit tenant_uuid (simulates future app code)
    new_uuid = str(uuid.uuid4())
    with db_engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO associacoes (nome, cnpj, tenant_uuid) "
                "VALUES (:n, :c, :t)"
            ),
            {"n": "new_assoc", "c": "11.111.111/0001-99", "t": new_uuid},
        )

    # Verify
    with db_engine.connect() as conn:
        row = conn.execute(
            sa.text("SELECT tenant_uuid FROM associacoes WHERE cnpj = :c"),
            {"c": "11.111.111/0001-99"},
        ).fetchone()
    assert row is not None
    assert row[0] == new_uuid


def REDACTED(db_engine):
    """Test 3 (spec): UNIQUE constraint on tenant_uuid rejects duplicates."""
    mod = _import_migration()

    # Apply upgrade
    _apply_op(db_engine, mod.upgrade)

    dupe_uuid = str(uuid.uuid4())

    # First insert succeeds
    with db_engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO associacoes (nome, cnpj, tenant_uuid) "
                "VALUES (:n, :c, :t)"
            ),
            {"n": "first", "c": "22.222.222/0001-99", "t": dupe_uuid},
        )

    # Second insert with same tenant_uuid must fail
    with pytest.raises(IntegrityError):
        with db_engine.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO associacoes (nome, cnpj, tenant_uuid) "
                    "VALUES (:n, :c, :t)"
                ),
                {
                    "n": "second",
                    "c": "33.333.333/0001-99",
                    "t": dupe_uuid,
                },
            )


def test_downgrade_roundtrip(db_engine):
    """Spec: downgrade() roundtrip — column is removed, schema restored."""
    mod = _import_migration()

    # Apply upgrade
    _apply_op(db_engine, mod.upgrade)

    # Verify column exists
    with db_engine.connect() as conn:
        cols = [
            row[1]
            for row in conn.execute(
                sa.text("PRAGMA table_info(associacoes)")
            ).fetchall()
        ]
    assert "tenant_uuid" in cols

    # Apply downgrade
    _apply_op(db_engine, mod.downgrade)

    # Verify column is gone
    with db_engine.connect() as conn:
        cols = [
            row[1]
            for row in conn.execute(
                sa.text("PRAGMA table_info(associacoes)")
            ).fetchall()
        ]
    assert "tenant_uuid" not in cols

    # Verify index is gone (was ix_associacoes_tenant_uuid)
    with db_engine.connect() as conn:
        indexes = [
            row[1]
            for row in conn.execute(
                sa.text("PRAGMA index_list(associacoes)")
            ).fetchall()
        ]
    assert "ix_associacoes_tenant_uuid" not in indexes
