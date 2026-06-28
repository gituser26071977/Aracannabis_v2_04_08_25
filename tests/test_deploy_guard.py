"""
test_deploy_guard — Testes do guard de migrations + schema (MISSAO 28)

Cenarios cobertos:
  1. Banco completo (todas colunas criticas presentes) — guard passa
  2. Coluna critica ausente (simula B-001 / data_revogacao faltando)
     - Em producao: RuntimeError (aborta startup)
     - Em dev: loga warning (nao aborta)
  3. Tabela critica ausente — mesmo comportamento
  4. Alembic_version atras da head — aborta em producao
  5. Alembic_version = head — passa
  6. Endpoint /api/schema-version retorna JSON correto

Para rodar:
  pytest tests/test_deploy_guard.py -v
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# ──────────────────────────────────────────────────────────────────
# Helpers para mockar SQLAlchemy
# ──────────────────────────────────────────────────────────────────
def make_db_mock(columns_by_table: dict, alembic_state: dict = None):
    """
    columns_by_table: { 'pacientes': {'id', 'nome', ...}, ... }
    alembic_state:   { 'table_exists': bool, 'current': str|None }
    """
    db = MagicMock()
    alembic_state = alembic_state or {"table_exists": True, "current": "REDACTED"}

    def execute(query, params=None):
        text = str(query).lower()
        if "information_schema.tables" in text and "table_name = 'alembic_version'" in text.replace('"', "'"):
            # Query "table exists"
            res = MagicMock()
            res.scalar.return_value = alembic_state["table_exists"]
            return res
        if "select version_num from alembic_version" in text:
            res = MagicMock()
            if alembic_state.get("current"):
                res.first.return_value = (alembic_state["current"],)
            else:
                res.first.return_value = None
            return res
        if "information_schema.columns" in text and "table_name" in text:
            tname = params.get("tname") if params else None
            cols = columns_by_table.get(tname, set())
            res = MagicMock()
            res.fetchall.return_value = [(c,) for c in cols]
            return res
        # fallback
        res = MagicMock()
        res.fetchall.return_value = []
        return res

    db.session.execute.side_effect = execute
    return db


# ──────────────────────────────────────────────────────────────────
# Testes do schema preflight (FASE 3)
# ──────────────────────────────────────────────────────────────────
class TestSchemaColumnsExist:
    def REDACTED(self):
        from services.deploy_guard import assert_schema_columns_exist
        # Banco completo — todas as colunas criticas
        full_cols = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento","data_revogacao"},
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(full_cols)
        # Nao deve levantar em prod nem em dev
        assert_schema_columns_exist(db, is_production=True)  # passa
        assert_schema_columns_exist(db, is_production=False)  # passa

    def REDACTED(self):
        """Cenario M27: coluna data_revogacao ausente em producao"""
        from services.deploy_guard import assert_schema_columns_exist
        cols_without_b001 = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento"},  # SEM data_revogacao
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(cols_without_b001)
        with pytest.raises(RuntimeError, match="ABORT STARTUP"):
            assert_schema_columns_exist(db, is_production=True)

    def REDACTED(self):
        """Em dev, somente loga warning — nao aborta"""
        from services.deploy_guard import assert_schema_columns_exist
        cols_without_b001 = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento"},  # SEM data_revogacao
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(cols_without_b001)
        # Em dev NAO deve levantar
        assert_schema_columns_exist(db, is_production=False)  # passa

    def test_missing_entire_table_aborts(self):
        """Tabela inteira ausente"""
        from services.deploy_guard import assert_schema_columns_exist
        empty = {"pacientes": set(), "consultas": set(), "prescricoes": set(),
                 "evolucoes": set(), "profissionais": set()}
        db = make_db_mock(empty)
        with pytest.raises(RuntimeError, match="ABORT STARTUP"):
            assert_schema_columns_exist(db, is_production=True)


# ──────────────────────────────────────────────────────────────────
# Testes do alembic guard (FASE 2)
# ──────────────────────────────────────────────────────────────────
class TestMigrationsApplied:
    def test_alembic_up_to_date_passes(self):
        from services.deploy_guard import assert_migrations_applied
        # alembic_version = head
        db = make_db_mock({}, alembic_state={"table_exists": True, "current": "REDACTED"})
        assert_migrations_applied(db, is_production=True)  # passa

    def REDACTED(self):
        """M27 cenario: alembic nunca rodou, tabela nao existe"""
        from services.deploy_guard import assert_migrations_applied
        db = make_db_mock({}, alembic_state={"table_exists": False, "current": None})
        with pytest.raises(RuntimeError, match="ABORT STARTUP"):
            assert_migrations_applied(db, is_production=True)

    def REDACTED(self):
        from services.deploy_guard import assert_migrations_applied
        db = make_db_mock({}, alembic_state={"table_exists": False, "current": None})
        # Em dev NAO aborta
        assert_migrations_applied(db, is_production=False)  # passa

    def REDACTED(self):
        """current eh uma revisao antiga, nao esta em heads"""
        from services.deploy_guard import assert_migrations_applied
        db = make_db_mock({}, alembic_state={"table_exists": True, "current": "alguma_rev_antiga_2025"})
        with pytest.raises(RuntimeError, match="ABORT STARTUP"):
            assert_migrations_applied(db, is_production=True)


# ──────────────────────────────────────────────────────────────────
# Testes do endpoint /api/schema-version (FASE 4)
# ──────────────────────────────────────────────────────────────────
class TestSchemaVersionEndpoint:
    def test_returns_complete_info(self):
        from services.deploy_guard import get_schema_version
        full_cols = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento","data_revogacao"},
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(full_cols)
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "GIT_COMMIT": "abc123def456"}):
            info = get_schema_version(db)

        # Campos obrigatorios presentes
        assert "commit" in info
        assert "alembic" in info
        assert "schema" in info
        assert info["commit"] == "abc123def456"
        assert info["schema"]["all_critical_columns_present"] is True
        assert info["alembic"]["status"] == "up_to_date"

    def test_reports_missing_columns(self):
        from services.deploy_guard import get_schema_version
        cols_without_b001 = {
            "pacientes": {"id","nome","data_nascimento"},  # muitos faltando
            "consultas": {"id","paciente_id"},
            "prescricoes": {"id"},
            "evolucoes": {"id"},
            "profissionais": {"id"},
        }
        db = make_db_mock(cols_without_b001)
        info = get_schema_version(db)
        assert info["schema"]["all_critical_columns_present"] is False
        assert "data_revogacao" in info["schema"]["tables"]["pacientes"]["missing"]


# ──────────────────────────────────────────────────────────────────
# Teste do run_all_checks (integracao)
# ──────────────────────────────────────────────────────────────────
class TestRunAllChecks:
    def REDACTED(self):
        from services.deploy_guard import run_all_checks
        full_cols = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento","data_revogacao"},
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(full_cols, {"table_exists": True, "current": "REDACTED"})
        run_all_checks(db, is_production=True)  # passa

    def REDACTED(self):
        """Replica exata do cenario M27: data_revogacao ausente"""
        from services.deploy_guard import run_all_checks
        cols_without_b001 = {
            "pacientes": {"id","nome","data_nascimento","cpf","profissional_responsavel_id",
                          "associacao_id","is_active","created_at","updated_at",
                          "foto_nome","foto_caminho","foto_tipo","foto_tamanho",
                          "consentimento_lgpd","data_consentimento"},  # SEM data_revogacao
            "consultas": {"id","paciente_id","profissional_id","data_hora","status","tipo_consulta","associacao_id"},
            "prescricoes": {"id","paciente_id","profissional_id","medicamentos","orientacoes","validade_dias","associacao_id","created_at"},
            "evolucoes": {"id","paciente_id","profissional_id","nota_evolucao","data_evolucao","associacao_id","created_at"},
            "profissionais": {"id","nome","email","senha_hash","is_active","created_at"},
        }
        db = make_db_mock(cols_without_b001, {"table_exists": True, "current": "REDACTED"})
        # alembic diz "head" (alguem rodou `flask db stamp head`) mas coluna nao existe
        # O guard DEVE pegar isso — defesa em profundidade
        with pytest.raises(RuntimeError, match="ABORT STARTUP"):
            run_all_checks(db, is_production=True)