"""
test_deploy_guard_sync — Sincronizacao CRITICAL_TABLES ↔ models.py (D05j F3)

Este teste garante que:
  - Toda coluna exigida em CRITICAL_TABLES esta DECLARADA em models.py.
  - O teste so falha se o codigo pedir coluna que nao existe na model.

Isso evita o problema de D05i: deploy_guard exigindo colunas que nunca
existiram (medicamentos/orientacoes/validade_dias, created_at em evolucoes,
senha_hash/is_active em profissionais).

Quando adicionar coluna nova:
  1. Adicionar em models.py
  2. Adicionar em CRITICAL_TABLES se for coluna "critica" para startup
  3. Criar migration
  4. CI roda este teste — se falhar, o PR esta desalinhado

Para rodar:
  pytest tests/test_deploy_guard_sync.py -v
"""
import importlib
import sys
from pathlib import Path

import pytest


# Garante que a raiz do projeto esta no sys.path quando pytest roda este arquivo
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _try_import_models():
    """
    Tenta importar models.py. Se o ambiente nao tiver DB configurado
    (e.g., CI sem Postgres), o teste e pulado — porque nao faz sentido
    validar sync quando nao se consegue ler models.

    A CI de verdade roda contra uma fixture leve — vide tests/conftest.py.
    """
    try:
        import models  # noqa: F401
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def models_module():
    if not _try_import_models():
        pytest.skip("models.py nao importavel neste ambiente (sem DB/Flask context)")
    return importlib.import_module("models")


def _columns_of(db_model) -> set:
    """Retorna o conjunto de nomes de colunas declaradas em um modelo SQLAlchemy."""
    return {c.name for c in db_model.__table__.columns}


class TestDeployGuardSync:
    """
    CRITICAL_TABLES x models.py.

    Cada tabela critica TEM QUE ter todas as colunas declaradas em models.py.
    Se voce adicionou uma coluna em CRITICAL_TABLES, ela PRECISA estar em
    models.py tambem (e vice-versa para colunas criticas).
    """

    def REDACTED(self):
        from services.deploy_guard import CRITICAL_TABLES
        import models

        required = set(CRITICAL_TABLES["pacientes"])
        actual = _columns_of(models.Paciente)
        missing_in_model = required - actual
        assert not missing_in_model, (
            f"CRITICAL_TABLES['pacientes'] exige colunas que nao existem "
            f"em models.Paciente: {sorted(missing_in_model)}. "
            f"Adicione em models.py OU remova do CRITICAL_TABLES."
        )

    def REDACTED(self):
        from services.deploy_guard import CRITICAL_TABLES
        import models

        required = set(CRITICAL_TABLES["consultas"])
        actual = _columns_of(models.Consulta)
        missing_in_model = required - actual
        assert not missing_in_model, (
            f"CRITICAL_TABLES['consultas'] exige colunas que nao existem "
            f"em models.Consulta: {sorted(missing_in_model)}."
        )

    def REDACTED(self):
        from services.deploy_guard import CRITICAL_TABLES
        import models

        required = set(CRITICAL_TABLES["prescricoes"])
        actual = _columns_of(models.Prescricao)
        missing_in_model = required - actual
        assert not missing_in_model, (
            f"CRITICAL_TABLES['prescricoes'] exige colunas que nao existem "
            f"em models.Prescricao: {sorted(missing_in_model)}. "
            f"Lembrete D05j: medicamentos/orientacoes/validade_dias foram "
            f"consolidados em `conteudo_json`."
        )

    def REDACTED(self):
        from services.deploy_guard import CRITICAL_TABLES
        import models

        required = set(CRITICAL_TABLES["evolucoes"])
        actual = _columns_of(models.Evolucao)
        missing_in_model = required - actual
        assert not missing_in_model, (
            f"CRITICAL_TABLES['evolucoes'] exige colunas que nao existem "
            f"em models.Evolucao: {sorted(missing_in_model)}. "
            f"Lembrete D05j: `data_evolucao` faz o papel de created_at."
        )

    def REDACTED(self):
        from services.deploy_guard import CRITICAL_TABLES
        import models

        required = set(CRITICAL_TABLES["profissionais"])
        actual = _columns_of(models.Profissional)
        missing_in_model = required - actual
        assert not missing_in_model, (
            f"CRITICAL_TABLES['profissionais'] exige colunas que nao existem "
            f"em models.Profissional: {sorted(missing_in_model)}. "
            f"Lembrete D05j: schema usa `senha` (nao `senha_hash`) e NAO "
            f"tem `is_active` (tabela usa `ativo` so em outros contextos)."
        )


class TestNoLegacyColumns:
    """
    Defesas contra o bug D05i: ter CRITICAL_TABLES com nomes de coluna
    que NUNCA existiram (sintomas do drift historico).

    Estes testes sao negativos — falham se o drift voltar.
    """

    # (coluna_legacy, tabela_onde_nao_deve_estar)
    # - is_active EXISTS legitimamente em pacientes, mas NAO em profissionais
    # - senha_hash NAO deve voltar em profissionais (refactor D05j)
    # - medicamentos/orientacoes/validade_dias NAO devem voltar em prescricoes
    @pytest.mark.parametrize("legacy_col,forbidden_tables", [
        ("senha_hash", ["profissionais"]),
        ("is_active", ["profissionais", "consultas", "prescricoes", "evolucoes"]),
        ("medicamentos", ["prescricoes"]),
        ("orientacoes", ["prescricoes"]),
        ("validade_dias", ["prescricoes"]),
        ("validade_receita", ["prescricoes"]),
    ])
    def REDACTED(self, legacy_col, forbidden_tables):
        from services.deploy_guard import CRITICAL_TABLES
        for table in forbidden_tables:
            cols = CRITICAL_TABLES.get(table, [])
            assert legacy_col not in cols, (
                f"Coluna legacy {legacy_col!r} voltou em "
                f"CRITICAL_TABLES[{table!r}] — drift historico (ver D05i)."
            )
