"""
Sprint S2 — Commit C2: tests for TenantMappingService.

Cobre todas as responsabilidades da spec:
  - get_tenant_uuid(associacao_id) — existente, inexistente
  - get_associacao_id(tenant_uuid) — existente, inexistente, UUID inválido
  - exists(tenant_uuid) — True, False (missing), False (invalid)
  - get_or_raise(tenant_uuid) — sucesso, TenantNotFound, InvalidTenantUUID
  - Cache hit (segunda call não toca DB)
  - Cache miss (primeira call toca DB)
  - Round-trip associacao_id → tenant_uuid → associacao_id
  - 100% de cobertura
"""

import uuid as _uuid

import pytest
import sqlalchemy as sa

from services.tenant_mapping import (
    InvalidTenantUUID,
    TenantMappingService,
    TenantNotFound,
)


# ── get_tenant_uuid ─────────────────────────────────────────────────────
class TestGetTenantUuid:
    def test_existing_returns_uuid(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        # assoc_id 1 (autoincrement)
        result = service.get_tenant_uuid(1)

        assert result == "REDACTED"

    def test_missing_returns_none(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        result = service.get_tenant_uuid(9999)

        assert result is None

    def REDACTED(self, session, make_associacao):
        """Edge: row existe mas tenant_uuid IS NULL (legado sem backfill)."""
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid=None,
        )
        service = TenantMappingService(session)

        result = service.get_tenant_uuid(1)

        assert result is None


# ── get_associacao_id ───────────────────────────────────────────────────
class TestGetAssociacaoId:
    def test_existing_returns_id(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        result = service.get_associacao_id(
            "REDACTED"
        )

        assert result == 1

    def test_missing_returns_none(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        result = service.get_associacao_id(
            "REDACTED"
        )

        assert result is None

    @pytest.mark.parametrize(
        "bad_uuid",
        [
            "not-a-uuid",
            "12345",
            "",
            "00000000-0000-0000-0000",  # truncado
            "REDACTED",  # chars inválidos
            "REDACTED",  # último char inválido
        ],
    )
    def test_invalid_uuid_raises(self, session, bad_uuid):
        service = TenantMappingService(session)

        with pytest.raises(InvalidTenantUUID):
            service.get_associacao_id(bad_uuid)

    def test_non_string_raises(self, session):
        """Defesa: input não-string também levanta InvalidTenantUUID."""
        service = TenantMappingService(session)

        with pytest.raises(InvalidTenantUUID):
            service.get_associacao_id(None)  # type: ignore[arg-type]


# ── exists ──────────────────────────────────────────────────────────────
class TestExists:
    def test_valid_existing_returns_true(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        assert service.exists("REDACTED") is True

    def test_valid_missing_returns_false(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        assert service.exists("REDACTED") is False

    def test_invalid_uuid_returns_false(self, session):
        """exists NÃO levanta — entradas malformadas retornam False."""
        service = TenantMappingService(session)

        assert service.exists("not-a-uuid") is False
        assert service.exists("") is False
        assert service.exists("REDACTED") is False


# ── get_or_raise ────────────────────────────────────────────────────────
class TestGetOrRaise:
    def test_existing_returns_id(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        result = service.get_or_raise(
            "REDACTED"
        )

        assert result == 1

    def REDACTED(self, session, make_associacao):
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01",
            tenant_uuid="REDACTED",
        )
        service = TenantMappingService(session)

        with pytest.raises(TenantNotFound):
            service.get_or_raise("REDACTED")

    def test_invalid_uuid_raises_invalid(self, session):
        service = TenantMappingService(session)

        with pytest.raises(InvalidTenantUUID):
            service.get_or_raise("not-a-uuid")


# ── Cache behavior ─────────────────────────────────────────────────────
class TestCache:
    def REDACTED(
        self, session, make_associacao
    ):
        """Cache hit: 2ª call não toca o DB, mesmo se valor mudou."""
        uuid_a = "REDACTED"
        uuid_b = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=uuid_a,
        )
        service = TenantMappingService(session)

        # Primeira call: popula cache
        first = service.get_associacao_id(uuid_a)
        assert first == 1

        # Mutação no DB (simula outro processo)
        session.execute(
            sa.text(
                "UPDATE associacoes SET tenant_uuid = :t WHERE id = :id"
            ),
            {"t": uuid_b, "id": 1},
        )
        session.commit()

        # Segunda call: cache hit — retorna valor antigo
        cached = service.get_associacao_id(uuid_a)
        assert cached == 1

        # Nova instância (cache vazio): reflete DB
        fresh = TenantMappingService(session)
        assert fresh.get_associacao_id(uuid_a) is None
        assert fresh.get_associacao_id(uuid_b) == 1

    def REDACTED(
        self, session, make_associacao
    ):
        """Lookup por um sentido popula o sentido oposto no cache."""
        uuid_v = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=uuid_v,
        )
        service = TenantMappingService(session)

        # Lookup por UUID
        assoc_id = service.get_associacao_id(uuid_v)
        assert assoc_id == 1

        # Sentido oposto já populado (sem query)
        # Mutamos o DB para detectar cache hit
        session.execute(
            sa.text("UPDATE associacoes SET tenant_uuid = NULL WHERE id = :id"),
            {"id": 1},
        )
        session.commit()

        # get_tenant_uuid retorna valor antigo (cache hit)
        assert service.get_tenant_uuid(1) == uuid_v

    def test_cache_miss_first_call(self, session, make_associacao):
        """Cache miss: primeira call faz query (verificável por mutation)."""
        uuid_v = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=uuid_v,
        )
        service = TenantMappingService(session)

        # Antes de qualquer call, cache está vazio
        assert service._cache_uuid_to_id == {}
        assert service._cache_id_to_uuid == {}

        # Primeira call: miss → query → popula
        result = service.get_associacao_id(uuid_v)
        assert result == 1
        assert service._cache_uuid_to_id == {uuid_v: 1}
        assert service._cache_id_to_uuid == {1: uuid_v}


# ── Round-trip ──────────────────────────────────────────────────────────
class TestRoundTrip:
    def test_id_to_uuid_to_id(self, session, make_associacao):
        """associacao_id → tenant_uuid → associacao_id retorna o id original."""
        original_uuid = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=original_uuid,
        )
        service = TenantMappingService(session)

        # Forward
        uuid_back = service.get_tenant_uuid(1)
        assert uuid_back == original_uuid

        # Reverse
        id_back = service.get_associacao_id(uuid_back)
        assert id_back == 1

    def test_uuid_to_id_to_uuid(self, session, make_associacao):
        """tenant_uuid → associacao_id → tenant_uuid retorna o uuid original."""
        original_uuid = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=original_uuid,
        )
        service = TenantMappingService(session)

        # Forward
        id_back = service.get_associacao_id(original_uuid)
        assert id_back == 1

        # Reverse
        uuid_back = service.get_tenant_uuid(id_back)
        assert uuid_back == original_uuid


# ── Independence between instances ─────────────────────────────────────
class TestIndependence:
    def REDACTED(
        self, session, make_associacao
    ):
        """Cada instância tem seu próprio cache (sem vazamento)."""
        uuid_v = "REDACTED"
        make_associacao(
            nome="A1", cnpj="00.000.000/0001-01", tenant_uuid=uuid_v,
        )

        s1 = TenantMappingService(session)
        s2 = TenantMappingService(session)

        # s1 popula, s2 não
        s1.get_associacao_id(uuid_v)
        assert s1._cache_uuid_to_id == {uuid_v: 1}
        assert s2._cache_uuid_to_id == {}
