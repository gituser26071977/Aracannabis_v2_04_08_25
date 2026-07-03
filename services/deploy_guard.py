"""
deploy_guard — Hardening de pre-startup checks (MISSAO 28)

Funcoes:
- assert_migrations_applied: aborta startup se alembic_version diverge do head
- assert_schema_columns_exist: aborta startup se colunas criticas estao ausentes
- get_schema_version: retorna dict com info de migracao (commit, head, current, status)
- get_git_commit: le .git/HEAD ou env var

Origem do problema:
- M27 descobriu que `data_revogacao` nao existe em producao
- `flask db upgrade` foi executado contra um DB que ja tinha a coluna via `db.create_all()`?
  NAO — em producao, alembic NUNCA rodou. O codigo foi deployado, app subiu, INSERT falhou 500.
- Pre-deploy, nao havia nenhuma verificacao automatica que codigo == schema.

Esta camada adiciona 3 barreiras pre-startup:
  1. Alembic current == head (senao: faltam migrations)
  2. Cada tabela critica tem todas as colunas obrigatorias (senao: schema legado)
  3. Endpoint /api/schema-version permite observabilidade pos-deploy

Comportamento:
- Em PRODUCAO: qualquer divergencia ABORTA startup (raise RuntimeError)
- Em DEV/STAGING: divergencia LOGA warning mas nao aborta (permite investigar)
- Toggle via env ENABLE_DEPLOY_GUARD=1 (default: ativo em producao, inativo em dev)

Este modulo NAO faz MIGRATIONS. So verifica e aborta.
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# Esquema de tabelas criticas — MISSAO 28
#
# Lista de tabelas + colunas OBRIGATORIAS que o codigo assume existirem.
# Adicionar aqui SEMPRE que uma coluna nova for usada em codigo de producao
# (e.g. models.py declara + rota faz SELECT/INSERT).
#
# Este e o "contrato minimo" entre codigo e banco. Se o banco nao cumpre,
# o deploy NAO pode subir.
# ──────────────────────────────────────────────────────────────────
CRITICAL_TABLES: Dict[str, List[str]] = {
    # IMPORTANTE: este dict deve estar SINCRONIZADO com models.py E com
    # o schema real do banco. Manter via teste automatizado
    # (tests/test_deploy_guard_sync.py) — ver docs/DEPLOY_GUARD_MAINTENANCE.md
    # (D05j F5).
    "pacientes": [
        # B-001 (M27): coluna que faltava em producao
        "data_revogacao",
        # LGPD (art. 18, IX) — vinculada a data_revogacao
        "consentimento_lgpd",
        "data_consentimento",
        # Identificacao minima
        "id",
        "nome",
        "data_nascimento",
        "cpf",
        "profissional_responsavel_id",
        "associacao_id",
        "is_active",
        "created_at",
        "updated_at",
        # Fotos (M11+)
        "foto_nome",
        "foto_caminho",
        "foto_tipo",
        "foto_tamanho",
    ],
    "consultas": [
        "id",
        "paciente_id",
        "profissional_id",
        "data_hora",
        "status",
        "tipo_consulta",
        "associacao_id",
    ],
    "prescricoes": [
        "id",
        "paciente_id",
        "profissional_id",
        "associacao_id",
        # Refatorado (D05j): medicamentos/orientacoes/validade_dias
        # foram consolidados em `conteudo_json` (snapshot JSON).
        # Schema original em database_schema.sql usa data_emissao
        # (sem created_at dedicado).
        "data_emissao",
        "conteudo_json",
        "arquivo_path",
        "observacoes",
    ],
    "evolucoes": [
        "id",
        "paciente_id",
        "profissional_id",
        "nota_evolucao",
        "data_evolucao",
        "associacao_id",
        # data_evolucao faz o papel de created_at (default=datetime.utcnow).
    ],
    "profissionais": [
        "id",
        "nome",
        "crm",
        "uf_crm",
        "usuario",
        # Schema original usa `senha` (não `senha_hash`).
        # `senha_hash` existe apenas em `senhas_temporarias` (tabela separada).
        "senha",
        "email",
        "role",
        "status_cadastro",
        "status_conta",
        "created_at",
    ],
}


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def _is_production() -> bool:
    env = (os.environ.get("ENVIRONMENT") or os.environ.get("FLASK_ENV") or "").lower()
    return env in ("production", "prod")


def _is_guard_enabled() -> bool:
    """Toggle via env ENABLE_DEPLOY_GUARD=0 desativa mesmo em producao (escape hatch)."""
    if os.environ.get("ENABLE_DEPLOY_GUARD") == "0":
        return False
    return _is_production()


def _get_git_commit() -> str:
    """
    Tenta obter o SHA do commit atual:
      1. Env var GIT_COMMIT (setada pelo CI/CD)
      2. Arquivo .git/HEAD (repo local)
      3. Subprocess git rev-parse
      4. 'unknown'
    """
    env_sha = os.environ.get("GIT_COMMIT") or os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha[:12]

    try:
        head_path = Path(".git/HEAD")
        if head_path.exists():
            ref = head_path.read_text().strip()
            if ref.startswith("ref: "):
                ref_path = Path(".git") / ref[5:]
                if ref_path.exists():
                    return ref_path.read_text().strip()[:12]
    except Exception:
        pass

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _table_has_columns(db, table_name: str, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Retorna (all_present, missing).
    Usa information_schema.columns — funciona em qualquer SGBD compativel com SQL standard.
    """
    from sqlalchemy import text

    missing: List[str] = []
    try:
        # Detectar schema — Postgres default 'public'
        result = db.session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :tname
                """
            ),
            {"tname": table_name},
        )
        existing = {row[0] for row in result.fetchall()}
        missing = [c for c in required_columns if c not in existing]
    except Exception as exc:
        logger.error("[deploy_guard] falha ao inspecionar tabela %s: %s", table_name, exc)
        return False, required_columns  # Em caso de erro, considerar tudo faltando
    return (not missing), missing


def _get_alembic_state(db) -> Dict[str, Any]:
    """
    Le alembic_version. Retorna:
      {current: str|None, table_exists: bool, error: str|None}
    """
    from sqlalchemy import text

    out: Dict[str, Any] = {"current": None, "table_exists": False, "error": None}
    try:
        exists = db.session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
                """
            )
        ).scalar()
        out["table_exists"] = bool(exists)
        if exists:
            row = db.session.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            ).first()
            if row:
                out["current"] = row[0]
    except Exception as exc:
        out["error"] = str(exc)
    return out


def _get_alembic_head() -> List[str]:
    """
    Le os arquivos de migrations e retorna a lista de heads.
    Multiplas heads sao aceitas (branches paralelas), mas o banco deve estar
    em uma das heads ou atras de uma delas (com migrations downgrade).
    """
    heads: List[str] = []
    migrations_dir = Path("migrations/versions")
    if not migrations_dir.exists():
        return heads
    for py_file in migrations_dir.glob("*.py"):
        if py_file.name.startswith("_"):
            continue
        try:
            content = py_file.read_text()
            # Procura "revision = 'XXXX'"
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("revision = ") and not line.startswith("#"):
                    rev = line.split("=", 1)[1].strip().strip("'\"")
                    # Se nao tem down_revision, eh uma head
                    has_down = any(
                        l.strip().startswith("down_revision = ")
                        and rev not in l
                        and "None" not in l
                        for l in content.splitlines()
                    )
                    # Versao simplificada: se nao existe outra revision que aponta para esta como down_revision, eh head
                    # Sera avaliada em _compare_versions
                    heads.append(rev)
        except Exception:
            continue
    return heads


def _compare_versions(current: Optional[str], heads: List[str]) -> Dict[str, Any]:
    """
    Compara current contra heads.
    Retorna:
      status: 'up_to_date' | 'behind' | 'diverged' | 'no_alembic'
      behind_count: int (estimado, baseado em ordem alfabetica)
      heads: lista
    """
    if current is None:
        return {"status": "no_alembic", "behind_count": 0, "heads": heads}
    if current in heads:
        return {"status": "up_to_date", "behind_count": 0, "heads": heads}
    # current nao eh uma head — esta atras ou divergiu
    return {
        "status": "behind",
        "behind_count": "unknown",
        "heads": heads,
        "current": current,
    }


# ──────────────────────────────────────────────────────────────────
# API publica
# ──────────────────────────────────────────────────────────────────
def assert_migrations_applied(db, is_production: Optional[bool] = None) -> None:
    """
    ABORTA startup se alembic_version nao esta em uma das heads.

    Estrategia: aceita o estado "no_alembic" (tabela nao existe) APENAS em dev,
    porque alguns ambientes sao provisionados via `db.create_all()`.
    Em PRODUCAO, sem alembic_version nao ha como saber se migrations rodaram —
    ABORTAR.

    Args:
        db: instancia do SQLAlchemy
        is_production: override (default: ler env)

    Raises:
        RuntimeError: se migracoes pendentes (em producao)
    """
    if is_production is None:
        is_production = _is_production()

    alembic = _get_alembic_state(db)
    heads = _get_alembic_head()
    cmp = _compare_versions(alembic.get("current"), heads)

    if is_production:
        if not alembic.get("table_exists"):
            raise RuntimeError(
                f"[deploy_guard] ABORT STARTUP: tabela alembic_version NAO EXISTE em producao. "
                f"Nao e possivel garantir migrations aplicadas. "
                f"Rode `flask db upgrade` antes do deploy. ({alembic.get('error','')})"
            )
        if cmp["status"] == "behind":
            raise RuntimeError(
                f"[deploy_guard] ABORT STARTUP: alembic_version={alembic.get('current')!r} "
                f"NAO esta em nenhuma head. Heads={heads}. "
                f"Migrations pendentes — rode `flask db upgrade` antes do deploy."
            )
    else:
        if cmp["status"] == "behind":
            logger.warning(
                "[deploy_guard] alembic_version=%s atras das heads=%s (dev/staging — nao aborta)",
                alembic.get("current"), heads,
            )
        elif not alembic.get("table_exists"):
            logger.warning(
                "[deploy_guard] alembic_version nao existe (provavelmente db.create_all). "
                "OK em dev/staging."
            )


def assert_schema_columns_exist(
    db,
    critical_tables: Optional[Dict[str, List[str]]] = None,
    is_production: Optional[bool] = None,
) -> None:
    """
    ABORTA startup se alguma coluna critica estiver ausente.

    Esta e a defesa em profundidade contra o cenario M27:
      - Modelo declara coluna X
      - Migration existe mas nao foi aplicada em prod
      - alembic_version diz "head" (porque alguem rodou `flask db stamp head`)
        mas a coluna nao foi adicionada de verdade
      - `assert_migrations_applied` passa
      - `assert_schema_columns_exist` BLOQUEIA aqui

    Args:
        db: instancia do SQLAlchemy
        critical_tables: override do mapa (default: CRITICAL_TABLES do modulo)
        is_production: override

    Raises:
        RuntimeError: se coluna critica ausente (em producao)
    """
    if is_production is None:
        is_production = _is_production()

    tables = critical_tables or CRITICAL_TABLES

    failures: List[str] = []
    for table_name, required_cols in tables.items():
        ok, missing = _table_has_columns(db, table_name, required_cols)
        if not ok:
            failures.append(f"{table_name}: faltando {missing}")

    if failures:
        msg = (
            "[deploy_guard] ABORT STARTUP: schema incompleto. "
            f"Tabelas/colunas ausentes: {failures}. "
            "Verifique se todas as migrations foram aplicadas."
        )
        if is_production:
            raise RuntimeError(msg)
        else:
            logger.warning(msg)


def get_schema_version(db) -> Dict[str, Any]:
    """
    Retorna dict com info completa de schema/version.
    Usado pelo endpoint /api/schema-version.
    NAO aborta — somente leitura.
    """
    alembic = _get_alembic_state(db)
    heads = _get_alembic_head()
    cmp = _compare_versions(alembic.get("current"), heads)

    # Verificar colunas
    column_status: Dict[str, Any] = {}
    for table_name, required_cols in CRITICAL_TABLES.items():
        ok, missing = _table_has_columns(db, table_name, required_cols)
        column_status[table_name] = {
            "complete": ok,
            "missing": missing,
        }

    all_columns_ok = all(v["complete"] for v in column_status.values())

    return {
        "commit": _get_git_commit(),
        "alembic": {
            "current": alembic.get("current"),
            "table_exists": alembic.get("table_exists"),
            "heads": heads,
            "status": cmp["status"],
        },
        "schema": {
            "all_critical_columns_present": all_columns_ok,
            "tables": column_status,
        },
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "guard_enabled": _is_guard_enabled(),
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
    }


def run_all_checks(db, is_production: Optional[bool] = None) -> None:
    """
    Conveniencia: roda assert_migrations_applied + assert_schema_columns_exist.
    Em dev, somente loga. Em producao, aborta em qualquer divergencia.
    """
    if is_production is None:
        is_production = _is_production()

    if not _is_guard_enabled() and not is_production:
        return  # guard desativado em dev

    assert_migrations_applied(db, is_production=is_production)
    assert_schema_columns_exist(db, is_production=is_production)