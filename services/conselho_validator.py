"""
conselho_validator.py — Validação de conselhos de classe profissionais.

Mapeia tipo de conselho (CRM, CRP, COREN, CRN, CREFITO) para:
  - regex de validação do número
  - role correspondente no Profissional.role
  - label user-facing

Validação atual: apenas formato (regex por tipo).
Não consulta APIs externas (CFM, CFP, COFEN, CFN, COFFITO).

TODO (futuro): Integrar com agente de validação que consulta APIs externas:
  - CRM     → https://servicos.cfm.org.br/...
  - CRP     → https://cadastro.cfp.org.br/...
  - COREN   → https://www.cofen.gov.br/...
  - CRN     → https://www.cfn.org.br/...
  - CREFITO → https://www.coffito.gov.br/...
Ver issue #XXX. Por enquanto, validar_conselho() confia no formato.

Parte da feature feat/intelligent-import (fase I1).
"""
import re
from typing import Optional, Dict, Any


# Tipos de conselho suportados
CONSELHO_CRM = "CRM"           # Médico
CONSELHO_CRP = "CRP"           # Psicólogo
CONSELHO_COREN = "COREN"       # Enfermeiro
CONSELHO_CRN = "CRN"           # Nutricionista
CONSELHO_CREFITO = "CREFITO"   # Fisioterapeuta
CONSELHO_NONE = "NONE"         # Sem conselho (staff: secretária, gestor)

CONSELHOS_SUPORTADOS = [
    CONSELHO_CRM,
    CONSELHO_CRP,
    CONSELHO_COREN,
    CONSELHO_CRN,
    CONSELHO_CREFITO,
    CONSELHO_NONE,
]

# Mapeamento de label amigável por tipo
CONSELHO_LABELS = {
    CONSELHO_CRM: "Conselho Regional de Medicina",
    CONSELHO_CRP: "Conselho Regional de Psicologia",
    CONSELHO_COREN: "Conselho Regional de Enfermagem",
    CONSELHO_CRN: "Conselho Regional de Nutricionistas",
    CONSELHO_CREFITO: "Conselho Regional de Fisioterapia",
    CONSELHO_NONE: "Sem conselho (staff administrativo)",
}

# Abreviações alternativas (comum em planilhas, e.g. "CREFITO" → "CREFITO-3")
CONSELHO_ALIASES = {
    "CRM": CONSELHO_CRM,
    "CRP": CONSELHO_CRP,
    "COREN": CONSELHO_COREN,
    "CRN": CONSELHO_CRN,
    "CREFITO": CONSELHO_CREFITO,
    "CREFITO-3": CONSELHO_CREFITO,  # variação com dígito regional
    "COFFITO": CONSELHO_CREFITO,   # nome do conselho federal
    "": CONSELHO_NONE,
    "N/A": CONSELHO_NONE,
    "NENHUM": CONSELHO_NONE,
    "STAFF": CONSELHO_NONE,
}


# Tabela canônica: tipo -> {regex, role, label, profissao}
_CONSELHOS: Dict[str, Dict[str, Any]] = {
    CONSELHO_CRM: {
        "regex": re.compile(r"^\d{4,7}$"),
        "role": "profissional",
        "label": CONSELHO_LABELS[CONSELHO_CRM],
        "profissao": "Médico",
    },
    CONSELHO_CRP: {
        "regex": re.compile(r"^(\d{2,6})(/\d+)?$"),
        "role": "profissional",
        "label": CONSELHO_LABELS[CONSELHO_CRP],
        "profissao": "Psicólogo",
    },
    CONSELHO_COREN: {
        "regex": re.compile(r"^[A-Z]{2}\d{4,6}$"),
        "role": "profissional",
        "label": CONSELHO_LABELS[CONSELHO_COREN],
        "profissao": "Enfermeiro",
    },
    CONSELHO_CRN: {
        "regex": re.compile(r"^\d{1,2}/\d{1,5}$"),
        "role": "profissional",
        "label": CONSELHO_LABELS[CONSELHO_CRN],
        "profissao": "Nutricionista",
    },
    CONSELHO_CREFITO: {
        "regex": re.compile(r"^(\d{1,2}/\d{1,5}|\d{4,6})$"),
        "role": "profissional",
        "label": CONSELHO_LABELS[CONSELHO_CREFITO],
        "profissao": "Fisioterapeuta",
    },
    CONSELHO_NONE: {
        "regex": re.compile(r"^$|^None$|^null$|^N/A$", re.IGNORECASE),
        "role": "secretary",
        "label": CONSELHO_LABELS[CONSELHO_NONE],
        "profissao": "Staff administrativo",
    },
}


def normalizar_tipo_conselho(tipo_bruto: Optional[str]) -> str:
    """Normaliza string do tipo de conselho para o valor canônico.

    Aceita aliases (e.g. 'COFFITO' → 'CREFITO', 'STAFF' → 'NONE').
    Se não reconhecido, retorna o valor original em maiúsculas (vai falhar
    a validação depois com mensagem clara).
    """
    if not tipo_bruto:
        return CONSELHO_NONE
    tipo = str(tipo_bruto).strip().upper()
    return CONSELHO_ALIASES.get(tipo, tipo)


def get_conselho_info(tipo: str) -> Optional[Dict[str, Any]]:
    """Retorna metadata do tipo de conselho, ou None se não suportado."""
    tipo_norm = normalizar_tipo_conselho(tipo)
    return _CONSELHOS.get(tipo_norm)


def listar_conselhos() -> list[Dict[str, Any]]:
    """Retorna lista de todos os conselhos suportados com metadata.

    Útil para popular dropdowns na UI.
    """
    return [
        {
            "tipo": k,
            "label": v["label"],
            "profissao": v["profissao"],
            "role": v["role"],
            "exige_numero": k != CONSELHO_NONE,
        }
        for k, v in _CONSELHOS.items()
    ]


def validar_conselho(
    numero: Optional[str],
    uf: Optional[str],
    tipo: str,
) -> Dict[str, Any]:
    """Valida um número de conselho contra o tipo declarado.

    Args:
        numero: número do conselho (string ou None para staff)
        uf: sigla do estado (2 letras, maiúsculas)
        tipo: 'CRM' | 'CRP' | 'COREN' | 'CRN' | 'CREFITO' | 'NONE' (ou alias)

    Returns:
        Dict com:
          - valido: bool
          - erros: list[str] com mensagens de erro
          - tipo_normalizado: str (canônico)
          - role: str (role do Profissional)
          - profissao: str (label user-facing)
          - confianca: float (1.0 para validação só por formato)
    """
    tipo_norm = normalizar_tipo_conselho(tipo)
    info = _CONSELHOS.get(tipo_norm)

    resultado = {
        "valido": False,
        "erros": [],
        "tipo_normalizado": tipo_norm,
        "role": info["role"] if info else "profissional",
        "profissao": info["profissao"] if info else "Desconhecido",
        "confianca": 1.0,  # apenas formato
    }

    # Tipo não suportado
    if not info:
        resultado["erros"].append(
            f"Tipo de conselho '{tipo}' não é suportado. "
            f"Use um destes: {', '.join(CONSELHOS_SUPORTADOS)}"
        )
        return resultado

    # Staff sem conselho
    if tipo_norm == CONSELHO_NONE:
        # Se veio número, é inconsistência: staff não deveria ter número
        if numero and str(numero).strip() and str(numero).upper() not in ("N/A", "NONE", ""):
            resultado["erros"].append(
                f"Staff administrativo não deve ter número de conselho (recebido '{numero}')"
            )
            return resultado
        resultado["valido"] = True
        return resultado

    # Conselho de saúde: exige número + UF
    numero_limpo = (numero or "").strip()
    uf_limpa = (uf or "").strip().upper()

    if not numero_limpo:
        resultado["erros"].append(
            f"{info['profissao']} exige número de conselho {tipo_norm}"
        )
        return resultado

    if not uf_limpa or len(uf_limpa) != 2:
        resultado["erros"].append(
            f"UF inválida para {info['profissao']} (esperado 2 letras, recebido '{uf}')"
        )
        return resultado

    # Validação de regex
    if not info["regex"].match(numero_limpo):
        resultado["erros"].append(
            f"Número '{numero}' não bate o formato esperado para {tipo_norm} "
            f"({info['profissao']}). Exemplo válido: ver regex no código."
        )
        return resultado

    # Para CRM, número deve ser puramente dígitos
    # Para CRP, formato é "XXXXX" ou "XX/XXXXX" (antigo)
    # Para COREN, formato é "UFXXXXX" (ex: SP12345)
    # Validação específica por tipo
    if tipo_norm == CONSELHO_COREN:
        if not numero_limpo.startswith(uf_limpa):
            resultado["erros"].append(
                f"COREN {numero_limpo} deve começar com a UF '{uf_limpa}'"
            )
            return resultado

    resultado["valido"] = True
    return resultado


def inferir_tipo_pela_role(role: str) -> str:
    """Infer tipo de conselho padrão a partir do Profissional.role.

    Útil quando o tipo não é explícito (default assume CRM para 'profissional',
    NONE para staff).
    """
    role_lower = (role or "").lower()
    if role_lower in ("secretary", "manager", "auxiliar"):
        return CONSELHO_NONE
    return CONSELHO_CRM  # default


__all__ = [
    "CONSELHO_CRM",
    "CONSELHO_CRP",
    "CONSELHO_COREN",
    "CONSELHO_CRN",
    "CONSELHO_CREFITO",
    "CONSELHO_NONE",
    "CONSELHOS_SUPORTADOS",
    "CONSELHO_LABELS",
    "normalizar_tipo_conselho",
    "get_conselho_info",
    "listar_conselhos",
    "validar_conselho",
    "inferir_tipo_pela_role",
]
