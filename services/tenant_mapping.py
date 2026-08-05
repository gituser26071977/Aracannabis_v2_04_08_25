"""
Sprint S2 — Commit C2: TenantMappingService.

Único ponto de acesso para a resolução entre:
  - ``associacoes.id`` (Integer, PK legacy SaaS)
  - ``associacoes.tenant_uuid`` (String(36) UUID, AraOS canônico)

A partir deste commit, **nenhum código novo** pode resolver essa relação
diretamente via SQL — toda consulta deve passar por este serviço.

Conformidade arquitetural:
  - Sem dependência de Flask (``current_app``, ``g``, ``request``).
  - Sem decorators, sem middleware, sem feature flags.
  - Injeção de dependência: ``Session`` SQLAlchemy passada no construtor.
  - Sem novas dependências externas (sem Redis, sem Flask-Caching).

Modelo de dados:
  A coluna ``tenant_uuid`` foi adicionada pela migration C1
  (``2026_08_02_s2_tenant_uuid_mapping``) sem alteração do ORM model
  ``Associacao``. Por isso este serviço usa SQL direto via ``text()`` —
  é a única leitora oficial desta coluna. Consumidores não devem
  referenciar a coluna diretamente.

Cache:
  - Dicionários em memória, per-instance.
  - Vida útil = vida útil da instância. Consumidores (C3+) devem
    instanciar o serviço por request.
  - Sem TTL explícito; a invalidação é implícita pela recriação.
  - Estrutura: ``dict[str, int]`` (UUID → id) e ``dict[int, str]``
    (id → UUID). Populados em pares por lookups.
"""

from __future__ import annotations

import uuid as _uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


# ── Exceptions ──────────────────────────────────────────────────────────
class TenantNotFound(LookupError):
    """tenant_uuid não encontrado no mapping (não existe em associacoes)."""


class InvalidTenantUUID(ValueError):
    """String fornecida não é um UUID válido (formato)."""


# ── SQL statements (prepared uma vez) ───────────────────────────────────
_SELECT_BY_ID = text(
    "SELECT tenant_uuid FROM associacoes WHERE id = :id LIMIT 1"
)
_SELECT_BY_UUID = text(
    "SELECT id FROM associacoes WHERE tenant_uuid = :t LIMIT 1"
)


# ── Service ────────────────────────────────────────────────────────────
class TenantMappingService:
    """Resolve associacoes.id ↔ associacoes.tenant_uuid.

    Thread-safety: o cache é per-instance e não é protegido por locks.
    Consumidores devem instanciar um service por thread/request.

    Zero acoplamento a Flask: o construtor recebe apenas uma ``Session``
    SQLAlchemy.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._cache_uuid_to_id: dict[str, int] = {}
        self._cache_id_to_uuid: dict[int, str] = {}

    # ── Read API ──────────────────────────────────────────────────────
    def get_tenant_uuid(self, associacao_id: int) -> Optional[str]:
        """Resolve ``associacao_id`` → ``tenant_uuid``.

        Returns:
            O tenant_uuid se existir e estiver mapeado, ``None`` caso
            contrário (id não existe OU row existe mas ``tenant_uuid`` é NULL).

        Caches both directions on hit.
        """
        if associacao_id in self._cache_id_to_uuid:
            return self._cache_id_to_uuid[associacao_id]

        row = self._session.execute(
            _SELECT_BY_ID, {"id": associacao_id}
        ).fetchone()

        if row is None or row[0] is None:
            return None

        tenant_uuid = row[0]
        self._populate_caches(associacao_id, tenant_uuid)
        return tenant_uuid

    def get_associacao_id(self, tenant_uuid: str) -> Optional[int]:
        """Resolve ``tenant_uuid`` → ``associacao_id``.

        Raises:
            InvalidTenantUUID: se ``tenant_uuid`` não é UUID válido
                (formato). Esta validação acontece antes da query
                para evitar custo desnecessário.

        Returns:
            O associacao_id se o mapping existir, ``None`` caso contrário.
        """
        self._validate_uuid(tenant_uuid)

        if tenant_uuid in self._cache_uuid_to_id:
            return self._cache_uuid_to_id[tenant_uuid]

        row = self._session.execute(
            _SELECT_BY_UUID, {"t": tenant_uuid}
        ).fetchone()

        if row is None:
            return None

        assoc_id = row[0]
        self._populate_caches(assoc_id, tenant_uuid)
        return assoc_id

    def exists(self, tenant_uuid: str) -> bool:
        """True se ``tenant_uuid`` é UUID válido E existe no mapping.

        Não levanta ``InvalidTenantUUID`` — entradas malformadas
        retornam False (a função é segura para uso em predicates).
        """
        try:
            return self.get_associacao_id(tenant_uuid) is not None
        except InvalidTenantUUID:
            return False

    def get_or_raise(self, tenant_uuid: str) -> int:
        """Resolve ``tenant_uuid`` → ``associacao_id``, levantando erro.

        Raises:
            InvalidTenantUUID: se o formato for inválido.
            TenantNotFound: se o UUID for válido mas não estiver mapeado.

        Returns:
            O associacao_id.

        Uso típico: decorators de autenticação onde ausência = 401.
        """
        assoc_id = self.get_associacao_id(tenant_uuid)
        if assoc_id is None:
            raise TenantNotFound(
                f"tenant_uuid not found: {tenant_uuid!r}"
            )
        return assoc_id

    # ── Internals ─────────────────────────────────────────────────────
    @staticmethod
    def _validate_uuid(value: str) -> None:
        """Levanta ``InvalidTenantUUID`` se ``value`` não for UUID válido."""
        try:
            _uuid.UUID(value)
        except (ValueError, AttributeError, TypeError) as exc:
            raise InvalidTenantUUID(
                f"Invalid UUID format: {value!r}"
            ) from exc

    def _populate_caches(self, assoc_id: int, tenant_uuid: str) -> None:
        """Atualiza ambos os sentidos do cache."""
        self._cache_id_to_uuid[assoc_id] = tenant_uuid
        self._cache_uuid_to_id[tenant_uuid] = assoc_id
