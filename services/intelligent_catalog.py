"""Motor de Cadastro Inteligente de Catálogo/Estoque — mesma lógica do SGAC.

Replica o pipeline `intelligent_onboarding` do SGAC aplicado a PRODUTOS e
ESTOQUE no SIAP:

    1. Extrator: chama o `CatalogoExtractionService` (LLM via `ai_manager`)
       para extrair produtos de PDF/planilha/imagem.
    2. Duplicidade: busca por código de barras (mais preciso), depois por
       nome normalizado com similaridade > 0.85 (padrão SGAC).
    3. Fusão: se duplicado, sugere `manter_existente` / `atualizar_existente`
       / `fundir_manual` (aguardando decisão do operador).
    4. Cadastro automático: se completo (nome + categoria + unidade), cria
       o produto direto (status `aplicado`).
    5. Pendência: se incompleto, vai para a fila de revisão humana
       (status `pendente_revisao`), espelhando `needs-review` do SGAC.

Onde aplicar, o fluxo também cria o `InventoryItem` (estoque) quando o
documento contém dados de lote/quantidade/validade.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from models import db, Produto
from models_extra import ICatalogProcess, InventoryItem

logger = logging.getLogger(__name__)


def _normalizar_nome(nome: str) -> str:
    """Normaliza nome de produto: minúsculas, sem acentos/pontuação extra."""
    if not nome:
        return ""
    n = unicodedata.normalize("NFD", nome.lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    n = re.sub(r"[^\w\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _similaridade(a: str, b: str) -> float:
    """Similaridade entre duas strings normalizadas (0..1)."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _parse_date(valor: Optional[str]) -> Optional[date]:
    if not valor:
        return None
    v = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


class IntelligentCatalogService:
    """Motor de cadastro inteligente de produtos + estoque."""

    def __init__(self, extraction_service=None):
        from services.catalogo_extraction_service import extraction_service as default_ext
        self.extraction = extraction_service or default_ext

    # REDACTED #
    # 1. PROCESSAR DOCUMENTO → extrai produtos e decide fluxo
    # REDACTED #
    def processar_arquivo(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        profissional_id: int,
        associacao_id: int,
    ) -> Dict[str, Any]:
        """Extrai produtos do documento e cria registros na fila de revisão.

        Retorna preview com as decisões (cadastrado / pendente / duplicado).
        """
        resultado = self.extraction.extract_from_file(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=mime_type,
            user_id=profissional_id,
        )

        if resultado.get("error"):
            return {
                "success": False,
                "error": resultado.get("error"),
                "message": resultado.get("message", resultado.get("error")),
                "processes": [],
            }

        produtos = resultado.get("detected_products", []) or []
        processes: List[Dict[str, Any]] = []

        for p in produtos:
            proc = self._processar_produto(
                produto=p,
                filename=filename,
                document_type=self._inferir_documento(p),
                profissional_id=profissional_id,
                associacao_id=associacao_id,
            )
            processes.append(proc)

        db.session.commit()

        return {
            "success": True,
            "detected_count": len(produtos),
            "processes": processes,
        }

    def _processar_produto(
        self,
        produto: Dict[str, Any],
        filename: str,
        document_type: str,
        profissional_id: int,
        associacao_id: int,
    ) -> Dict[str, Any]:
        """Aplica a lógica SGAC (duplicidade → fusão → cadastro/pendência)."""
        nome = (produto.get("nome") or "").strip()
        if not nome:
            return {
                "status": "erro",
                "action_taken": "Produto sem nome extraído",
                "extracted_data": produto,
            }

        codigo_barras = produto.get("codigo_barras")
        duplicado = self._verificar_duplicidade(nome, codigo_barras, associacao_id)

        # 1. Duplicado → sugestão de fusão (aguardando decisão)
        if duplicado:
            sugestao = self._sugerir_fusao(produto, duplicado)
            proc = ICatalogProcess(
                associacao_id=associacao_id,
                original_filename=filename,
                document_type=document_type,
                status="pendente_revisao",
                extracted_data=produto,
                confidence=produto.get("confidence") or 70,
                match_result={
                    "produto_id": duplicado.id,
                    "produto_nome": duplicado.nome,
                    "acao_sugerida": sugestao["acao"],
                    "motivo": sugestao["motivo"],
                },
                missing_fields=[],
                completeness_score=self._completude(produto),
                action_taken="aguardando_decisao",
                criado_por=profissional_id,
            )
            db.session.add(proc)
            db.session.flush()
            return proc.to_dict()

        # 2. Completo o suficiente → cadastra automaticamente (produto + estoque)
        if self._pode_cadastrar_automaticamente(produto):
            produto_id, inventory_id = self._aplicar_cadastro(produto, associacao_id)
            proc = ICatalogProcess(
                associacao_id=associacao_id,
                original_filename=filename,
                document_type=document_type,
                status="aplicado",
                extracted_data=produto,
                confidence=produto.get("confidence") or 70,
                match_result=None,
                missing_fields=self._campos_faltantes(produto),
                completeness_score=self._completude(produto),
                action_taken="created",
                produto_id=produto_id,
                criado_por=profissional_id,
            )
            db.session.add(proc)
            db.session.flush()
            d = proc.to_dict()
            d["inventory_id"] = inventory_id
            return d

        # 3. Incompleto → fila de revisão humana
        missing = self._campos_faltantes(produto)
        proc = ICatalogProcess(
            associacao_id=associacao_id,
            original_filename=filename,
            document_type=document_type,
            status="pendente_revisao",
            extracted_data=produto,
            confidence=produto.get("confidence") or 50,
            match_result=None,
            missing_fields=missing,
            completeness_score=self._completude(produto),
            action_taken="pending_review",
            criado_por=profissional_id,
        )
        db.session.add(proc)
        db.session.flush()
        return proc.to_dict()

    # REDACTED #
    # 2. DUPLICIDADE (padrão SGAC)
    # REDACTED #
    def _verificar_duplicidade(
        self, nome: str, codigo_barras: Optional[str], associacao_id: int
    ) -> Optional[Produto]:
        """Busca produto já existente: por código de barras (preciso), depois
        por nome normalizado com similaridade > 0.85."""
        if codigo_barras:
            cb = codigo_barras.strip()
            if cb:
                p = Produto.query.filter(
                    db.func.lower(Produto.codigo_barras) == cb.lower()
                ).first()
                if p:
                    return p

        nome_norm = _normalizar_nome(nome)
        if not nome_norm:
            return None

        candidatos = Produto.query.filter(Produto.ativo == True).all()  # noqa: E712
        for p in candidatos:
            if _similaridade(nome_norm, _normalizar_nome(p.nome)) > 0.85:
                return p
        return None

    def _sugerir_fusao(self, novo: Dict[str, Any], existente: Produto) -> Dict[str, Any]:
        """Compara completude entre novo e existente e sugere ação (padrão SGAC)."""
        campos_novos = {
            "nome": novo.get("nome"),
            "categoria": novo.get("categoria"),
            "unidade": novo.get("unidade"),
            "fabricante": novo.get("fabricante"),
            "codigo_barras": novo.get("codigo_barras"),
        }
        campos_existentes = {
            "nome": existente.nome,
            "categoria": existente.categoria,
            "unidade": existente.unidade,
            "fabricante": existente.fabricante,
            "codigo_barras": existente.codigo_barras,
        }
        completude_nova = sum(1 for v in campos_novos.values() if v)
        completude_existente = sum(1 for v in campos_existentes.values() if v)

        if completude_existente >= 4 and completude_existente >= completude_nova:
            return {
                "acao": "manter_existente",
                "motivo": "Cadastro existente está mais completo",
                "dados_para_fusao": {
                    "mantem": "existente",
                    "novos_dados": {
                        k: v for k, v in campos_novos.items()
                        if v and not campos_existentes.get(k)
                    },
                },
            }
        if completude_nova > completude_existente:
            return {
                "acao": "atualizar_existente",
                "motivo": "Novos dados estão mais completos",
                "dados_para_fusao": {"mantem": "novo", "novos_dados": campos_novos},
            }
        return {
            "acao": "fundir_manual",
            "motivo": "Cadastros com completudes similares - requer análise manual",
            "dados_para_fusao": {
                "opcoes": [
                    f"Manter {existente.nome} (ID {existente.id})",
                    f"Manter novo cadastro: {novo.get('nome')}",
                    "Fundir mantendo o mais completo",
                ]
            },
        }

    # REDACTED #
    # 3. COMPLETUDE / CRITÉRIOS
    # REDACTED #
    def _campos_faltantes(self, produto: Dict[str, Any]) -> List[str]:
        faltantes = []
        for campo in ("nome", "categoria", "unidade"):
            if not produto.get(campo):
                faltantes.append(campo)
        return faltantes

    def _completude(self, produto: Dict[str, Any]) -> int:
        campos = ("nome", "categoria", "unidade", "concentracao", "fabricante")
        presentes = sum(1 for c in campos if produto.get(c))
        return round(presentes / len(campos) * 100)

    def _pode_cadastrar_automaticamente(self, produto: Dict[str, Any]) -> bool:
        """Regra SGAC: cadastra automaticamente quando nome + categoria + unidade."""
        return bool(
            produto.get("nome")
            and produto.get("categoria")
            and produto.get("unidade")
        )

    def _inferir_documento(self, produto: Dict[str, Any]) -> str:
        if produto.get("lote") or produto.get("validade") or produto.get("quantidade"):
            return "estoque"
        return "catalogo"

    # REDACTED #
    # 4. APLICAR CADASTRO (cria Produto + InventoryItem)
    # REDACTED #
    def _aplicar_cadastro(
        self, produto: Dict[str, Any], associacao_id: int
    ) -> Optional[tuple]:
        """Cria o Produto (e InventoryItem se houver lote/validade/quantidade)."""
        p = Produto(
            nome=produto.get("nome"),
            tipo=produto.get("tipo") or "oleo",
            categoria=produto.get("categoria"),
            unidade=produto.get("unidade"),
            concentracao=produto.get("concentracao"),
            codigo_barras=produto.get("codigo_barras"),
            fabricante=produto.get("fabricante"),
            descricao=produto.get("descricao"),
            ativo=True,
        )
        db.session.add(p)
        db.session.flush()

        inventory_id = None
        if produto.get("lote") or produto.get("validade") or produto.get("quantidade"):
            item = InventoryItem(
                tenant_id=associacao_id,
                produto_id=p.id,
                lote=produto.get("lote"),
                quantidade=int(produto.get("quantidade") or 0),
                localizacao=produto.get("localizacao"),
                validade=_parse_date(produto.get("validade")),
            )
            db.session.add(item)
            db.session.flush()
            inventory_id = item.id

        return p.id, inventory_id

    # REDACTED #
    # 5. REVISÃO HUMANA (aplicar ação no registro pendente)
    # REDACTED #
    def listar_pendentes(self, associacao_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = ICatalogProcess.query.filter(
            ICatalogProcess.status == "pendente_revisao"
        )
        if associacao_id:
            query = query.filter(ICatalogProcess.associacao_id == associacao_id)
        return [p.to_dict() for p in query.order_by(ICatalogProcess.criado_em.desc()).all()]

    def estatisticas(self, associacao_id: Optional[int] = None) -> Dict[str, Any]:
        query = ICatalogProcess.query
        if associacao_id:
            query = query.filter(ICatalogProcess.associacao_id == associacao_id)
        total = query.count()
        by_status: Dict[str, int] = {}
        for status, in query.with_entities(ICatalogProcess.status).all():
            by_status[status] = by_status.get(status, 0) + 1
        return {"total": total, "by_status": by_status}

    def aplicar_revisao(
        self,
        process_id: int,
        decisao: str,
        profissional_id: int,
    ) -> Dict[str, Any]:
        """Aplica a decisão do operador sobre um registro pendente.

        decisao: 'aprovar' (cria/atualiza), 'rejeitar' (descarta),
                 'atualizar_existente' (merge no produto já existente).
        """
        proc = db.session.get(ICatalogProcess, process_id)
        if not proc:
            return {"success": False, "error": "Registro não encontrado"}

        if proc.status == "aplicado":
            return {"success": False, "error": "Registro já aplicado"}

        produto = proc.extracted_data or {}
        nome = (produto.get("nome") or "").strip()

        try:
            if decisao == "aprovar":
                produto_id, inventory_id = self._aplicar_cadastro(produto, proc.associacao_id)
                proc.produto_id = produto_id
                proc.action_taken = "created"
                proc.status = "aplicado"
                proc.revisado_por = profissional_id
                proc.revisado_em = datetime.utcnow()
                db.session.commit()
                return {
                    "success": True,
                    "process_id": proc.id,
                    "produto_id": produto_id,
                    "inventory_id": inventory_id,
                }

            if decisao == "rejeitar":
                proc.status = "ignorado"
                proc.action_taken = "rejected"
                proc.revisado_por = profissional_id
                proc.revisado_em = datetime.utcnow()
                db.session.commit()
                return {"success": True, "process_id": proc.id, "status": "ignorado"}

            if decisao == "atualizar_existente":
                match = proc.match_result or {}
                existing_id = match.get("produto_id")
                if not existing_id or not nome:
                    return {
                        "success": False,
                        "error": "Sem produto existente para atualizar",
                    }
                existente = db.session.get(Produto, existing_id)
                if not existente:
                    return {
                        "success": False,
                        "error": "Produto existente não encontrado",
                    }
                for campo in (
                    "categoria",
                    "unidade",
                    "concentracao",
                    "fabricante",
                    "codigo_barras",
                    "descricao",
                ):
                    valor = produto.get(campo)
                    if valor and not getattr(existente, campo):
                        setattr(existente, campo, valor)
                proc.produto_id = existente.id
                proc.action_taken = "merged"
                proc.status = "aplicado"
                proc.revisado_por = profissional_id
                proc.revisado_em = datetime.utcnow()
                db.session.commit()
                return {"success": True, "process_id": proc.id, "produto_id": existente.id}

            return {"success": False, "error": f"Decisão inválida: {decisao}"}
        except Exception as e:
            db.session.rollback()
            logger.exception("Erro ao aplicar revisão %s", process_id)
            return {"success": False, "error": str(e)}


intelligent_catalog_service = IntelligentCatalogService()
