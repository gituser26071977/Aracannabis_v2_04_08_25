"""
Sprint S2 — fixtures compartilhadas para os testes do TenantMappingService.

Cria a tabela ``associacoes`` via SQL direto (sem passar pelo ORM
``db.create_all()``, que falharia por causa de FKs cross-module em
``models.py`` que apontam para ``associacoes``).

Schema criado:
  - associacoes (id, nome, cnpj UNIQUE, tenant_uuid)
  - Índice UNIQUE em tenant_uuid (espelha migration C1)

Por que SQL direto (sem ORM):
  - A service usa ``text()`` puro; o teste espelha isso.
  - Não depende da cadeia de imports de ``models.py``.
  - Não acopla o teste a modelos que não são alvo da C2.
"""

import os
import sys

import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture()
def engine():
    """SQLite in-memory com schema associacoes (espelha C1 + model legacy)."""
    eng = create_engine("sqlite:///:memory:", future=True)
    with eng.begin() as conn:
        # Tabela: id INTEGER PK AUTOINCREMENT, colunas legacy + tenant_uuid
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
                    updated_at TIMESTAMP,
                    tenant_uuid VARCHAR(36)
                )
                """
            )
        )
        # Espelha migration C1: UNIQUE INDEX em tenant_uuid
        conn.execute(
            sa.text(
                "CREATE UNIQUE INDEX uq_associacoes_tenant_uuid "
                "ON associacoes (tenant_uuid)"
            )
        )
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    """Sessão SQLAlchemy ligada ao engine in-memory."""
    SessionLocal = sessionmaker(bind=engine, future=True)
    sess = SessionLocal()
    yield sess
    sess.close()


@pytest.fixture()
def make_associacao(session):
    """Factory: insere uma associacao com tenant_uuid opcional.

    Uso:
        assoc_id = make_associacao(nome="A1", cnpj="...", tenant_uuid="...")
    """
    def _make(
        nome: str,
        cnpj: str,
        tenant_uuid: str | None = None,
        assoc_id: int | None = None,
    ) -> int:
        if assoc_id is not None:
            session.execute(
                sa.text(
                    "INSERT INTO associacoes "
                    "(id, nome, cnpj, tenant_uuid) "
                    "VALUES (:id, :n, :c, :t)"
                ),
                {"id": assoc_id, "n": nome, "c": cnpj, "t": tenant_uuid},
            )
        else:
            session.execute(
                sa.text(
                    "INSERT INTO associacoes "
                    "(nome, cnpj, tenant_uuid) "
                    "VALUES (:n, :c, :t)"
                ),
                {"n": nome, "c": cnpj, "t": tenant_uuid},
            )
        session.commit()

        if assoc_id is None:
            row = session.execute(
                sa.text("SELECT id FROM associacoes WHERE cnpj = :c"),
                {"c": cnpj},
            ).fetchone()
            return int(row[0])
        return assoc_id

    return _make
