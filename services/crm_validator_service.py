"""
CRM Validation Service for Brazilian Medical Council verification

Integrates with CFM and regional CRM websites to validate
medical professional credentials automatically.
"""

import logging
import re
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CRMValidatorService:
    """Service for validating CRM (medical license) authenticity via web scraping"""

    REGIONAL_PORTALS = {
        "AC": {
            "name": "CRM-AC",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "AL": {
            "name": "CREMAL",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "AM": {
            "name": "CREMAM",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "AP": {"name": "CRM-AP", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "BA": {
            "name": "CREMEB",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "CE": {
            "name": "CREMEC",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "DF": {"name": "CRM-DF", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "ES": {"name": "CRM-ES", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "GO": {
            "name": "CREMEGO",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "MA": {"name": "CRM-MA", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "MG": {"name": "CRM-MG", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "MS": {"name": "CRM-MS", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "MT": {"name": "CRM-MT", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "PA": {
            "name": "CREMEPA",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "PB": {"name": "CRM-PB", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "PE": {
            "name": "CREMEPE",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "PI": {
            "name": "CREMEPI",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "PR": {"name": "CRM-PR", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "RJ": {
            "name": "CREMERJ",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "RN": {
            "name": "CREMERN",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "RO": {
            "name": "CREMERO",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "RR": {"name": "CRM-RR", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
        "RS": {
            "name": "CREMERS",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "SE": {
            "name": "CREMESE",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "SC": {
            "name": "CREMESC",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "SP": {
            "name": "CREMESP",
            "url": "https://servicos.cfm.org.br",
            "search_path": "/busca-medicos",
        },
        "TO": {"name": "CRM-TO", "url": "https://servicos.cfm.org.br", "search_path": "/busca-medicos"},
    }

    # Fontes de consulta direta (API ou scraping) por conselho
    # None significa que usaremos o portal generico do CFM
    DIRECT_SOURCES: Dict[str, Optional[str]] = {
        "CRM": None,
        "CRP": None,
        "COREN": None,
        "CRN": None,
        "CREFITO": None,
    }

    @staticmethod
    def _valid_uf(uf: str) -> bool:
        return uf.upper() in CRMValidatorService.REGIONAL_PORTALS

    @staticmethod
    def validate_crm_format(crm: str, uf: str) -> Tuple[bool, Optional[str]]:
        if not re.match(r"^\d{4,6}$", crm):
            return False, "CRM deve conter entre 4 e 6 dígitos"
        if not re.match(r"^[A-Z]{2}$", uf.upper()):
            return False, "UF deve conter 2 letras"
        if not CRMValidatorService._valid_uf(uf.upper()):
            return False, f"UF {uf} nao reconhecida"
        return True, None

    @staticmethod
    def _scrape_cfm_portal(crm: str, uf: str) -> Dict:
        """Tenta consultar o CRM no portal CFM (servicos.cfm.org.br)"""
        try:
            portal = CRMValidatorService.REGIONAL_PORTALS.get(uf.upper())
            if not portal:
                return {"success": False, "error": f"CRM-{uf} nao configurado"}

            url = f"{portal['url']}{portal['search_path']}"
            params = {"crm": crm, "uf": uf.upper()}

            response = requests.get(
                url,
                params=params,
                timeout=15,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )

            if response.status_code != 200:
                return {"success": False, "error": f"HTTP {response.status_code}"}

            soup = BeautifulSoup(response.text, "lxml")

            page_text = soup.get_text(separator=" ", strip=True).lower()

            found_crm = crm in page_text
            found_uf = uf.lower() in page_text

            if found_crm or found_uf:
                nome_element = soup.find(
                    "div", class_=re.compile(r"nome|name", re.I)
                ) or soup.find("h1")

                nome = nome_element.get_text(strip=True) if nome_element else None

                situacao_element = soup.find(
                    "div", class_=re.compile(r"situac|status", re.I)
                ) or soup.find("span", class_=re.compile(r"situac|status", re.I))

                situacao = situacao_element.get_text(strip=True) if situacao_element else None

                return {
                    "success": True,
                    "source": "cfm_portal_scrape",
                    "data": {
                        "crm": crm,
                        "uf": uf.upper(),
                        "nome_encontrado": nome,
                        "situacao": situacao,
                        "url_consulta": response.request.url,
                    },
                    "validated_at": datetime.utcnow().isoformat(),
                }

            if "nao encontrado" in page_text or "nenhum resultado" in page_text:
                return {
                    "success": False,
                    "source": "cfm_portal_scrape",
                    "error": "CRM nao encontrado no portal CFM",
                    "data": None,
                }

            return {
                "success": True,
                "source": "cfm_portal_scrape",
                "data": {
                    "crm": crm,
                    "uf": uf.upper(),
                    "nome_encontrado": None,
                    "situacao": None,
                    "url_consulta": response.request.url,
                    "observacao": "Resultado indeterminado - pode exigir verificacao manual",
                },
                "validated_at": datetime.utcnow().isoformat(),
            }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao consultar CFM para CRM {crm}/{uf}")
            return {"success": False, "source": "cfm_portal_scrape", "error": "Timeout"}
        except Exception as e:
            logger.error(f"Erro ao consultar CFM para CRM {crm}/{uf}: {e}")
            return {"success": False, "source": "cfm_portal_scrape", "error": str(e)}

    @staticmethod
    def validate_crm(crm: str, uf: str) -> Dict:
        """Valida CRM tentando todas as fontes disponiveis"""
        is_valid_format, error = CRMValidatorService.validate_crm_format(crm, uf)
        if not is_valid_format:
            return {
                "success": False,
                "source": "format_validation",
                "error": error,
                "data": None,
            }

        results = {
            "crm": crm,
            "uf": uf.upper(),
            "validated_at": datetime.utcnow().isoformat(),
            "sources_tried": [],
            "status": "validation_failed",
        }

        portal_result = CRMValidatorService._scrape_cfm_portal(crm, uf)
        results["sources_tried"].append({"name": "cfm_portal", "result": portal_result})

        if portal_result.get("success") and portal_result.get("data", {}).get("nome_encontrado"):
            results["status"] = "validated"
            results["source"] = "cfm_portal"
            results["data"] = portal_result["data"]
            return results

        if portal_result.get("success"):
            results["status"] = "possible_match"
            results["source"] = "cfm_portal"
            results["data"] = portal_result["data"]
            return results

        results["status"] = "validation_failed"
        results["error"] = "Nao foi possivel validar o CRM em nenhuma fonte disponivel"
        return results

    @staticmethod
    def validate_crm_cfm(crm: str, uf: str) -> Dict:
        """Alias para compatibilidade com codigo existente"""
        return CRMValidatorService._scrape_cfm_portal(crm, uf)

    @staticmethod
    def validate_crm_regional(crm: str, uf: str) -> Dict:
        """Alias para compatibilidade com codigo existente"""
        return CRMValidatorService.validate_crm(crm, uf)

    @staticmethod
    def extract_professional_data(validation_result: Dict) -> Optional[Dict]:
        if validation_result.get("status") not in ("validated", "possible_match"):
            return None
        data = validation_result.get("data", {})
        return {
            "nome_completo": data.get("nome_encontrado"),
            "crm": validation_result.get("crm"),
            "uf": validation_result.get("uf"),
            "situacao": data.get("situacao"),
            "validated_at": validation_result.get("validated_at"),
        }