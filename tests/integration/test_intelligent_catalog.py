"""Testes do Motor de Cadastro Inteligente de Catálogo/Estoque (ICatalog).

Cobre a mesma lógica do pipeline `intelligent_onboarding` do SGAC:
    - duplicidade (código de barras → nome normalizado similar > 0.85)
    - sugestão de fusão (manter_existente / atualizar_existente / fundir_manual)
    - cadastro automático quando completo (nome + categoria + unidade)
    - criação de InventoryItem quando o documento tem dados de estoque
    - fila de revisão humana (pendente → aprovar/rejeitar)
    - merge em produto existente via decisão 'atualizar_existente'
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que o pacote `association` (importado por models_extra) resolva.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from config import TestingConfig  # noqa: E402
from app_cors_livre import create_app  # noqa: E402
from models import db, Produto  # noqa: E402
from models_extra import InventoryItem  # noqa: E402


@pytest.fixture
def app():
    a = create_app(TestingConfig)
    with a.app_context():
        db.create_all()
    yield a
    with a.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def svc(app):
    from services.intelligent_catalog import IntelligentCatalogService

    class FakeExtraction:
        def __init__(self, products):
            self.products = products

        def extract_from_file(self, **kw):
            return {"detected_products": self.products}

    return IntelligentCatalogService


class _Extraction:
    """Fake do CatalogoExtractionService: retorna produtos pré-definidos."""

    def __init__(self, products):
        self.products = products

    def extract_from_file(self, **kw):
        return {"detected_products": self.products}


def REDACTED(app, svc):
    with app.app_context():
        ex = Produto(
            nome="Óleo CBD Equilibrado",
            categoria="oleo",
            unidade="ml",
            fabricante="AgraTech",
        )
        db.session.add(ex)
        db.session.commit()

        s = svc(_Extraction([
            {"nome": "Óleo CBD Equilibrado", "categoria": "oleo", "unidade": "ml"},
        ]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)

        proc = resultado["processes"][0]
        assert proc["status"] == "pendente_revisao"
        assert proc["action_taken"] == "aguardando_decisao"
        assert proc["match_result"]["produto_id"] == ex.id
        assert proc["match_result"]["acao_sugerida"] == "manter_existente"


def test_duplicado_por_codigo_barras(app, svc):
    with app.app_context():
        ex = Produto(nome="Outro Nome", categoria="oleo", unidade="ml", codigo_barras="78910")
        db.session.add(ex)
        db.session.commit()

        s = svc(_Extraction([
            {"nome": "Nome Totalmente Diferente", "categoria": "oleo", "unidade": "ml",
             "codigo_barras": "78910"},
        ]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)

        proc = resultado["processes"][0]
        assert proc["status"] == "pendente_revisao"
        assert proc["match_result"]["produto_id"] == ex.id


def REDACTED(app, svc):
    with app.app_context():
        s = svc(_Extraction([
            {"nome": "Gummy Relax 10mg", "categoria": "gummy", "unidade": "un",
             "lote": "L2026-01", "quantidade": 50, "validade": "30/06/2027"},
        ]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)

        proc = resultado["processes"][0]
        assert proc["status"] == "aplicado"
        assert proc["action_taken"] == "created"

        item = InventoryItem.query.filter_by(produto_id=proc["produto_id"]).first()
        assert item is not None
        assert item.quantidade == 50
        assert item.lote == "L2026-01"


def REDACTED(app, svc):
    with app.app_context():
        s = svc(_Extraction([{"nome": "Flor com nome incompleto"}]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)

        proc = resultado["processes"][0]
        assert proc["status"] == "pendente_revisao"
        assert proc["action_taken"] == "pending_review"
        assert proc["missing_fields"] == ["categoria", "unidade"]


def test_revisao_aprovar_e_rejeitar(app, svc):
    with app.app_context():
        s = svc(_Extraction([
            {"nome": "Produto Completo", "categoria": "oleo", "unidade": "ml"},
            {"nome": "Só Nome"},
        ]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)

        pendentes = [p for p in resultado["processes"] if p["status"] == "pendente_revisao"]
        assert len(pendentes) == 1

        # Aprovar
        res = s.aplicar_revisao(pendentes[0]["id"], "aprovar", profissional_id=1)
        assert res["success"] is True
        assert res["produto_id"]

        # Rejeitar o automático não se aplica; usa um novo fluxo
        s2 = svc(_Extraction([{"nome": "Só Nome 2"}]))
        r2 = s2.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)
        res2 = s2.aplicar_revisao(r2["processes"][0]["id"], "rejeitar", profissional_id=1)
        assert res2["success"] is True
        assert res2["status"] == "ignorado"

        stats = s2.estatisticas(1)
        assert stats["by_status"].get("ignorado", 0) >= 1


def REDACTED(app, svc):
    with app.app_context():
        ex = Produto(
            nome="Oleo CBD",
            categoria="oleo",
            unidade="ml",
            fabricante=None,
            codigo_barras=None,
        )
        db.session.add(ex)
        db.session.commit()

        s = svc(_Extraction([
            {"nome": "Oleo CBD", "categoria": "oleo", "unidade": "ml",
             "concentracao": "5000mg", "fabricante": "NovaFab", "codigo_barras": "789"},
        ]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)
        proc = resultado["processes"][0]
        assert proc["match_result"]["acao_sugerida"] == "atualizar_existente"

        res = s.aplicar_revisao(proc["id"], "atualizar_existente", profissional_id=1)
        assert res["success"] is True
        assert res["produto_id"] == ex.id

        db.session.refresh(ex)
        assert ex.concentracao == "5000mg"
        assert ex.fabricante == "NovaFab"
        assert ex.codigo_barras == "789"


def test_decisao_invalida_rejeitada(app, svc):
    with app.app_context():
        s = svc(_Extraction([{"nome": "Só Nome 3"}]))
        resultado = s.processar_arquivo(b"x", "cat.xlsx", "octet", 1, 1)
        res = s.aplicar_revisao(resultado["processes"][0]["id"], "banana", 1)
        assert res["success"] is False
