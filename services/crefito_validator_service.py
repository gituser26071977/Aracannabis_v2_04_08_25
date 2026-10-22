"""
crefito_validator_service.py — Validação de registro CREFITO.

Cobre Fisioterapia e Terapia Ocupacional (conselho CREFITO / COFFITO).

Espelha o contrato de ``CRMValidatorService.validate_crm()`` para que o fluxo de
verificação de cadastro (``RegistrationVerificationService``) possa rotear por
tipo de conselho sem alterar o restante da agregação.

Contexto (2026)
---------------
- O COFFITO **não** expõe uma API/consulta nacional única. A consulta pública de
  inscritos é feita por conselho regional (CREFITO-1 .. CREFITO-N) e a maioria
  usa a plataforma "Implanta" (ex.: ``crefito-07.implanta.net.br``).
- As páginas de consulta da Implanta estão protegidas por **CAPTCHA**
  (Cloudflare Turnstile / reCAPTCHA). Isso impede validação 100% automática por
  scraping.
- Por isso: a validação de **formato** é automática; a validação **externa**
  tenta a consulta e, quando bloqueada por CAPTCHA (ou sem endpoint
  configurado), retorna ``status="validation_failed"`` com
  ``manual_review_required=True`` — nunca inventa um resultado. O cadastro cai
  em revisão manual, porém SEM gerar o falso alerta de "incompatibilidade com
  CRM" que existia antes.

Para habilitar validação externa automática no futuro: preencha ``REGIONAIS``
com o endpoint direto de cada regional (API/JSON) ou integre um serviço de
resolução de CAPTCHA / a base oficial do conselho.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapa UF -> portal de consulta do CREFITO regional.
# `url` = página pública de consulta de inscritos (plataforma Implanta).
# Somente entradas VERIFICADAS são preenchidas; UFs sem endpoint confirmado
# ficam com url=None e caem em revisão manual. Fácil de estender.
# ---------------------------------------------------------------------------
REGIONAIS: Dict[str, Dict[str, Optional[str]]] = {
    # CREFITO-7 (BA/SE) — portal Implanta verificado em 2026-10.
    "SE": {
        "regional": "CREFITO-7",
        "url": "https://crefito-07.implanta.net.br/servicosOnline/Publico/ConsultaInscritos/",
    },
    "BA": {
        "regional": "CREFITO-7",
        "url": "https://crefito-07.implanta.net.br/servicosOnline/Publico/ConsultaInscritos/",
    },
}

# Padrão do portal Implanta (usado como fallback quando só se conhece a regional).
_IMPLANTA_TEMPLATE = "https://crefito-{nn:02d}.implanta.net.br/servicosOnline/Publico/ConsultaInscritos/"

# Número de inscrição: aceita "123456" (até 6 dígitos) ou "3/123456".
_REGEX_NUMERO = re.compile(r"^(\d{1,2}/\d{1,5}|\d{4,6})$")

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def implanta_url(regional_numero: int) -> str:
    """Monta a URL do portal Implanta de uma regional (ex.: 7 -> CREFITO-7)."""
    return _IMPLANTA_TEMPLATE.format(nn=int(regional_numero))


class CREFITOValidatorService:
    """Validação de registro CREFITO — formato automático, externa best-effort."""

    # ------------------------------------------------------------------ #
    # Formato
    # ------------------------------------------------------------------ #
    @staticmethod
    def _valid_uf(uf: str) -> bool:
        return bool(uf) and uf.upper() in REGIONAIS

    @staticmethod
    def validate_crefito_format(numero: str, uf: str) -> Tuple[bool, Optional[str]]:
        numero = (numero or "").strip()
        uf = (uf or "").strip().upper()
        if not numero:
            return False, "Informe o número de inscrição no CREFITO"
        if not re.match(r"^[A-Z]{2}$", uf):
            return False, "UF deve conter 2 letras"
        if not CREFITOValidatorService._valid_uf(uf):
            return False, f"UF {uf} não reconhecida"
        if not _REGEX_NUMERO.match(numero):
            return False, (
                "Número de CREFITO inválido (use até 6 dígitos, "
                "ex.: 123456 ou 3/123456)"
            )
        return True, None

    # ------------------------------------------------------------------ #
    # Consulta externa (best-effort)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _detect_captcha(html: str) -> bool:
        low = (html or "").lower()
        return any(
            k in low
            for k in ("turnstile", "cf-turnstile", "recaptcha", "grecaptcha")
        )

    @staticmethod
    def _scrape_implanta(portal_url: str, numero: str, uf: str) -> Dict:
        try:
            resp = requests.get(
                portal_url,
                timeout=20,
                headers={
                    "User-Agent": _UA,
                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                },
            )
            if resp.status_code != 200:
                return {
                    "success": False,
                    "source": "crefito_implanta",
                    "error": f"HTTP {resp.status_code}",
                }
            if CREFITOValidatorService._detect_captcha(resp.text):
                return {
                    "success": False,
                    "source": "crefito_implanta",
                    "error": (
                        "Portal do conselho protegido por CAPTCHA — "
                        "validação automática indisponível"
                    ),
                    "captcha": True,
                    "url_consulta": resp.url,
                }
            soup = BeautifulSoup(resp.text, "lxml")
            page_text = soup.get_text(separator=" ", strip=True).lower()
            if numero in page_text or uf.lower() in page_text:
                return {
                    "success": True,
                    "source": "crefito_implanta",
                    "data": {"numero": numero, "uf": uf, "url_consulta": resp.url},
                    "validated_at": datetime.utcnow().isoformat(),
                }
            return {
                "success": False,
                "source": "crefito_implanta",
                "error": "Inscrição não localizada na consulta pública",
            }
        except requests.exceptions.Timeout:
            return {"success": False, "source": "crefito_implanta", "error": "Timeout"}
        except Exception as e:  # noqa: BLE001
            logger.error(f"Erro ao consultar CREFITO {numero}/{uf}: {e}")
            return {"success": False, "source": "crefito_implanta", "error": str(e)}

    # ------------------------------------------------------------------ #
    # API pública (mesmo contrato de CRMValidatorService.validate_crm)
    # ------------------------------------------------------------------ #
    @staticmethod
    def validate_crefito(numero: str, uf: str) -> Dict:
        ok, err = CREFITOValidatorService.validate_crefito_format(numero, uf)
        if not ok:
            return {
                "success": False,
                "source": "format_validation",
                "error": err,
                "data": None,
                "status": "validation_failed",
            }

        uf = uf.upper()
        regional = REGIONAIS.get(uf, {})
        results: Dict = {
            "crefito": numero,
            "uf": uf,
            "regional": regional.get("regional"),
            "validated_at": datetime.utcnow().isoformat(),
            "sources_tried": [],
            "status": "validation_failed",
        }

        portal_url = regional.get("url")
        if not portal_url:
            results["error"] = (
                f"Endpoint de consulta do {regional.get('regional') or 'CREFITO'} "
                f"não configurado — validação manual necessária"
            )
            results["manual_review_required"] = True
            return results

        scrape = CREFITOValidatorService._scrape_implanta(portal_url, numero, uf)
        results["sources_tried"].append({"name": "crefito_implanta", "result": scrape})

        if scrape.get("success") and scrape.get("data"):
            results["status"] = "validated"
            results["source"] = "crefito_implanta"
            results["data"] = scrape["data"]
            return results

        if scrape.get("success"):
            results["status"] = "possible_match"
            results["source"] = "crefito_implanta"
            results["data"] = scrape.get("data")
            return results

        results["status"] = "validation_failed"
        results["error"] = scrape.get(
            "error", "Não foi possível validar o CREFITO automaticamente"
        )
        results["manual_review_required"] = True
        return results


__all__ = ["CREFITOValidatorService", "REGIONAIS", "implanta_url"]
