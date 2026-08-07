"""Certificação digital — assinatura de documentos (Bird ID e outros).

Abstração sobre provedores de assinatura digital (Bird ID, Valid, etc.).
Fluxo típico:
  1. OAuth2 client-credentials → access token.
  2. Cria uma sessão de assinatura com o documento (PDF) → URL de assinatura.
  3. O profissional autentica e assina na plataforma (link/iframe).
  4. Documento assinado é recuperado (ou entregue por webhook).

Cada provedor implementa a interface `DigitalSignatureProvider`.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

from models import db, DigitalSignatureConfig

logger = logging.getLogger(__name__)

PROVEDORES = ("birdid", "valid", "outro")


def obter_config(profissional_id: int) -> Optional[DigitalSignatureConfig]:
    return DigitalSignatureConfig.query.filter_by(profissional_id=profissional_id).first()


def salvar_config(
    profissional_id: int,
    *,
    provedor: str,
    client_id: str,
    client_secret: str,
    base_url: Optional[str] = None,
    criado_por: Optional[str] = None,
) -> DigitalSignatureConfig:
    provedor = provedor if provedor in PROVEDORES else "birdid"
    if not client_id or not client_secret:
        raise ValueError("client_id e client_secret são obrigatórios")
    cfg = obter_config(profissional_id)
    if cfg is None:
        cfg = DigitalSignatureConfig(
            profissional_id=profissional_id, provedor=provedor,
            client_id=client_id, client_secret=client_secret,
            base_url=base_url or None, status="pendente",
            criado_por=criado_por,
        )
        db.session.add(cfg)
    else:
        cfg.provedor = provedor
        cfg.client_id = client_id
        cfg.client_secret = client_secret
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

    def assinar_pdf(
        self,
        pdf_bytes: bytes,
        *,
        nome_assinante: str,
        cpf_assinante: str,
        motivo: str = "",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class BirdIDProvider(DigitalSignatureProvider):
    """Integração com a plataforma Bird ID (assinatura digital).

    Endpoints configuráveis via `config.base_url` ou env `BIRD_ID_BASE_URL`
    (default https://api.birdid.com.br). O fluxo padrão da Bird ID usa
    OAuth2 client-credentials para token e uma sessão de assinatura.
    """

    BASE_URL = "https://api.birdid.com.br"

    def _url(self) -> str:
        return self._config.base_url or os.environ.get("BIRD_ID_BASE_URL", self.BASE_URL)

    async def _token(self) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{self._url()}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                },
            )
            r.raise_for_status()
            return r.json().get("access_token") or ""

    def assinar_pdf(
        self,
        pdf_bytes: bytes,
        *,
        nome_assinante: str,
        cpf_assinante: str,
        motivo: str = "",
    ) -> Dict[str, Any]:
        import asyncio

        return asyncio.run(self._assinar(pdf_bytes, nome_assinante, cpf_assinante, motivo))

    async def _assinar(
        self, pdf_bytes: bytes, nome_assinante: str, cpf_assinante: str, motivo: str
    ) -> Dict[str, Any]:
        token = await self._token()
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("documento.pdf", pdf_bytes, "application/pdf")}
        data = {
            "signer_name": nome_assinante,
            "signer_cpf": cpf_assinante,
            "reason": motivo or "Assinatura digital",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{self._url()}/documents", headers=headers, files=files, data=data
            )
            r.raise_for_status()
            body = r.json()
        return {
            "status": "enviado",
            "provedor": "birdid",
            "assinatura_id": body.get("id") or body.get("document_id"),
            "url_assinatura": body.get("signing_url") or body.get("url"),
            "detalhe": "Documento enviado para assinatura. O profissional conclui na plataforma.",
        }


def assinar_pdf(
    pdf_bytes: bytes,
    *,
    provedor: str,
    profissional_id: int,
    nome_assinante: str,
    cpf_assinante: str,
    motivo: str = "",
) -> Dict[str, Any]:
    """Assina um PDF com a configuração do profissional."""
    config = obter_config(profissional_id)
    if config is None:
        raise ValueError("certificação digital não configurada para este profissional")
    provider = _provider(provedor or config.provedor, config)
    try:
        resultado = provider.assinar_pdf(
            pdf_bytes, nome_assinante=nome_assinante, cpf_assinante=cpf_assinante, motivo=motivo
        )
        config.status = "ativo"
    except Exception as exc:  # noqa: BLE001
        config.status = "erro"
        db.session.commit()
        logger.warning("assinatura_digital_falhou: %s", exc)
        raise
    db.session.commit()
    return resultado
