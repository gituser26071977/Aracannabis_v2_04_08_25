"""Certificação digital — assinatura via CESS (Bird ID / Soluti).

Integração real com o Cloud Electronic Signature Service (CESS) da Bird ID
(documentação: docs.vaultid.com.br). Fluxo assíncrono:

  1. `POST /signature-service`        → cria transação com o certificate_alias
     do profissional (tipo PDFSignature) → retorna `tcn`.
  2. `POST /file-transfer/<tcn>/eot/` → upload do PDF.
  3. O profissional valida no app Bird ID (push/QR) — assinatura na nuvem.
  4. `GET /signature-service/<tcn>`   → status (SIGNED) + URL de download.
  5. `GET /file-transfer/<tcn>/<id>`  → PDF assinado.

Credenciais corporativas: env `BIRD_ID_CLIENT_ID`/`BIRD_ID_CLIENT_SECRET` ou
no config do profissional. `certificate_alias` é por profissional.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from models import db, DigitalSignatureConfig, SignatureTransaction

logger = logging.getLogger(__name__)

PROVEDORES = ("birdid", "valid", "outro")


def obter_config(profissional_id: int) -> Optional[DigitalSignatureConfig]:
    return DigitalSignatureConfig.query.filter_by(profissional_id=profissional_id).first()


def salvar_config(
    profissional_id: int,
    *,
    provedor: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    certificate_alias: Optional[str] = None,
    base_url: Optional[str] = None,
    criado_por: Optional[str] = None,
) -> DigitalSignatureConfig:
    provedor = provedor if provedor in PROVEDORES else "birdid"
    cfg = obter_config(profissional_id)
    if cfg is None:
        cfg = DigitalSignatureConfig(
            profissional_id=profissional_id, provedor=provedor,
            client_id=client_id or None, client_secret=client_secret or None,
            certificate_alias=certificate_alias or None,
            base_url=base_url or None, status="pendente",
            criado_por=criado_por,
        )
        db.session.add(cfg)
    else:
        cfg.provedor = provedor
        if client_id is not None:
            cfg.client_id = client_id or None
        if client_secret is not None:
            cfg.client_secret = client_secret or None
        if certificate_alias is not None:
            cfg.certificate_alias = certificate_alias or None
        if base_url:
            cfg.base_url = base_url
        cfg.status = "pendente"
    db.session.commit()
    return cfg


def _provider(provedor: str, config: DigitalSignatureConfig) -> "DigitalSignatureProvider":
    if provedor == "birdid":
        return BirdIDProvider(config)
    raise NotImplementedError(f"provedor '{provedor}' ainda não implementado")


class DigitalSignatureProvider:
    """Interface comum de provedores de assinatura digital."""

    def __init__(self, config: DigitalSignatureConfig) -> None:
        self._config = config

    def iniciar_assinatura(self, pdf_bytes: bytes, *, nome_documento: str, motivo: str = "") -> Dict[str, Any]:
        raise NotImplementedError

    def consultar_transacao(self, tcn: str) -> Dict[str, Any]:
        raise NotImplementedError

    def baixar_assinado(self, tcn: str, document_id: int) -> bytes:
        raise NotImplementedError


class BirdIDProvider(DigitalSignatureProvider):
    """Cliente do CESS (Bird ID)."""

    BASE_URL = "https://cess.lab.vaultid.com.br"

    def _base(self) -> str:
        return self._config.base_url or os.environ.get("BIRD_ID_BASE_URL", self.BASE_URL)

    def _client_id(self) -> str:
        return self._config.client_id or os.environ.get("BIRD_ID_CLIENT_ID", "")

    def _client_secret(self) -> str:
        return self._config.client_secret or os.environ.get("BIRD_ID_CLIENT_SECRET", "")

    def _auth(self) -> httpx.BasicAuth:
        cid, csec = self._client_id(), self._client_secret()
        if not cid or not csec:
            raise ValueError("credenciais corporativas Bird ID não configuradas (env ou config)")
        return httpx.BasicAuth(cid, csec)

    def _alias(self) -> str:
        alias = self._config.certificate_alias or os.environ.get("BIRD_ID_CERTIFICATE_ALIAS", "")
        if not alias:
            raise ValueError("certificate_alias não configurado para o profissional")
        return alias

    def iniciar_assinatura(
        self, pdf_bytes: bytes, *, nome_documento: str, motivo: str = ""
    ) -> Dict[str, Any]:
        import asyncio

        return asyncio.run(self._iniciar(nome_documento, motivo))

    async def _iniciar(self, nome_documento: str, motivo: str) -> Dict[str, Any]:
        # 1. Criar transação
        payload = {
            "certificate_alias": self._alias(),
            "type": "PDFSignature",
            "hash_algorithm": "SHA256",
            "auto_fix_document": True,
            "signature_settings": [
                {
                    "id": "default",
                    "reason": motivo or "Assinatura digital",
                    "visible_signature": True,
                    "visible_sign_x": 0,
                    "visible_sign_y": 0,
                    "visible_sign_width": 230,
                    "visible_sign_height": 50,
                    "visible_sign_page": 1,
                }
            ],
            "documents_source": "UPLOAD_REFERENCE",
        }
        base = self._base()
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{base}/signature-service", json=payload, auth=self._auth(),
                headers={"Accept": "application/json"},
            )
            r.raise_for_status()
            tcn = r.json().get("tcn")
            if not tcn:
                raise RuntimeError(f"resposta sem TCN: {r.text[:200]}")

            # 2. Upload do documento
            files = {"document": (nome_documento or "documento.pdf", pdf_bytes, "application/pdf")}
            r2 = await client.post(
                f"{base}/file-transfer/{tcn}/eot/default",
                files=files, auth=self._auth(), headers={"Accept": "application/json"},
            )
            r2.raise_for_status()

        return {"tcn": tcn, "status": "aguardando"}

    def consultar_transacao(self, tcn: str) -> Dict[str, Any]:
        import asyncio

        return asyncio.run(self._consultar(tcn))

    async def _consultar(self, tcn: str) -> Dict[str, Any]:
        base = self._base()
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{base}/signature-service/{tcn}", auth=self._auth(),
                                 headers={"Accept": "application/json"})
            r.raise_for_status()
            body = r.json()
        docs = body.get("documents") or []
        doc0 = docs[0] if docs else {}
        return {
            "tcn": tcn,
            "status_documento": doc0.get("status"),  # SIGNED | WAITING | ERROR
            "resultado_url": doc0.get("result"),
            "document_id": doc0.get("id"),
            "transacao_status": body.get("status"),
        }

    def baixar_assinado(self, tcn: str, document_id: int) -> bytes:
        import asyncio

        return asyncio.run(self._baixar(tcn, document_id))

    async def _baixar(self, tcn: str, document_id: int) -> bytes:
        base = self._base()
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(f"{base}/file-transfer/{tcn}/{document_id}", auth=self._auth())
            r.raise_for_status()
            return r.content


def iniciar_assinatura(
    pdf_bytes: bytes,
    *,
    provedor: str,
    profissional_id: int,
    nome_documento: str = "documento.pdf",
    motivo: str = "",
) -> SignatureTransaction:
    """Inicia a assinatura: cria transação CESS + upload. Salva o TCN."""
    config = obter_config(profissional_id)
    if config is None:
        raise ValueError("certificação digital não configurada para este profissional")
    provider = _provider(provedor or config.provedor, config)
    try:
        resultado = provider.iniciar_assinatura(
            pdf_bytes, nome_documento=nome_documento, motivo=motivo
        )
        config.status = "ativo"
    except Exception as exc:  # noqa: BLE001
        config.status = "erro"
        db.session.commit()
        logger.warning("assinatura_digital_inicio_falhou: %s", exc)
        raise
    db.session.commit()

    tx = SignatureTransaction(
        config_id=config.id,
        tcn=resultado["tcn"],
        documento_nome=nome_documento,
        status="aguardando",
    )
    db.session.add(tx)
    db.session.commit()
    return tx


def consultar_transacao(tx: SignatureTransaction) -> Dict[str, Any]:
    """Consulta o status da transação e atualiza no banco."""
    config = DigitalSignatureConfig.query.get(tx.config_id)
    if config is None:
        raise ValueError("configuração da transação não encontrada")
    provider = _provider(config.provedor, config)
    resultado = provider.consultar_transacao(tx.tcn)
    doc_status = resultado.get("status_documento")
    if doc_status == "SIGNED":
        tx.status = "assinado"
        tx.resultado_url = resultado.get("resultado_url")
    elif doc_status == "ERROR":
        tx.status = "erro"
        tx.erro = "erro na assinatura na plataforma"
    else:
        tx.status = "aguardando"
    db.session.commit()
    return tx.to_dict()


def baixar_assinado(tx: SignatureTransaction) -> bytes:
    """Baixa e guarda o PDF assinado."""
    config = DigitalSignatureConfig.query.get(tx.config_id)
    if config is None:
        raise ValueError("configuração da transação não encontrada")
    if tx.status != "assinado":
        raise ValueError("documento ainda não assinado")
    provider = _provider(config.provedor, config)
    resultado = provider.consultar_transacao(tx.tcn)
    document_id = resultado.get("document_id")
    if document_id is None:
        raise ValueError("não foi possível obter o id do documento")
    bytes_pdf = provider.baixar_assinado(tx.tcn, int(document_id))
    tx.documento_assinado = bytes_pdf
    db.session.commit()
    return bytes_pdf
