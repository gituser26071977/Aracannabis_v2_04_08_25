"""
Validadores de CPF e CNPJ para o módulo de associações.
"""
import re


def _remove_non_digits(value: str) -> str:
    """Remove todos os caracteres não numéricos de uma string."""
    return re.sub(r'\D', '', value)


def _is_all_same_digit(value: str) -> bool:
    """Verifica se todos os dígitos da string são iguais."""
    return len(set(value)) == 1


def validar_cpf(cpf: str) -> bool:
    """
    Valida um CPF (Cadastro de Pessoas Físicas).
    
    Args:
        cpf: String contendo o CPF (com ou sem formatação)
        
    Returns:
        True se o CPF for válido, False caso contrário
    """
    if not cpf:
        return False
    
    # Remove caracteres não numéricos
    cpf = _remove_non_digits(cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Rejeita CPFs com todos os dígitos iguais (ex: 111.111.111-11)
    if _is_all_same_digit(cpf):
        return False
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[10]) != digito2:
        return False
    
    return True


def validar_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ (Cadastro Nacional de Pessoas Jurídicas).
    
    Args:
        cnpj: String contendo o CNPJ (com ou sem formatação)
        
    Returns:
        True se o CNPJ for válido, False caso contrário
    """
    if not cnpj:
        return False
    
    # Remove caracteres não numéricos
    cnpj = _remove_non_digits(cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Rejeita CNPJs com todos os dígitos iguais (ex: 11.111.111/1111-11)
    if _is_all_same_digit(cnpj):
        return False
    
    # Pesos para cálculo do primeiro dígito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(12):
        soma += int(cnpj[i]) * pesos1[i]
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1:
        return False
    
    # Pesos para cálculo do segundo dígito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(13):
        soma += int(cnpj[i]) * pesos2[i]
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[13]) != digito2:
        return False
    
    return True


def normalizar_cpf(cpf: str) -> str:
    """
    Normaliza um CPF, retornando apenas os números.
    
    Args:
        cpf: String contendo o CPF (com ou sem formatação)
        
    Returns:
        String contendo apenas os 11 dígitos do CPF
        
    Raises:
        ValueError: Se o CPF for inválido
    """
    if not cpf:
        raise ValueError("CPF não pode ser vazio")
    
    cpf = _remove_non_digits(cpf)
    
    if len(cpf) != 11:
        raise ValueError(f"CPF deve ter 11 dígitos, encontrado {len(cpf)}")
    
    return cpf


def normalizar_cnpj(cnpj: str) -> str:
    """
    Normaliza um CNPJ, retornando apenas os números.

    Args:
        cnpj: String contendo o CNPJ (com ou sem formatação)

    Returns:
        String contendo apenas os 14 dígitos do CNPJ

    Raises:
        ValueError: Se o CNPJ for inválido
    """
    if not cnpj:
        raise ValueError("CNPJ não pode ser vazio")

    cnpj = _remove_non_digits(cnpj)

    if len(cnpj) != 14:
        raise ValueError(f"CNPJ deve ter 14 dígitos, encontrado {len(cnpj)}")

    return cnpj


# ═══════════════════════════════════════════════════════════════════════
# STAFF VALIDATORS (Fase 2 — RBAC Secretária)
# ═══════════════════════════════════════════════════════════════════════

# Roles permitidas em UsuarioAssociacao.role
ROLES_INSTITUCIONAIS_VALIDAS = frozenset({"admin", "member", "secretary", "manager"})

# Roles globais válidas para staff (Profissional.role) — re-export para evitar import circular
def _get_staff_roles():
    from models import ProfissionalRole
    return ProfissionalRole.STAFF_ROLES


def validar_role_institucional(role: str) -> bool:
    """
    Valida que a role é uma das aceitas para UsuarioAssociacao.

    Aceitas: admin, member, secretary, manager.
    """
    if not role:
        return False
    return role in ROLES_INSTITUCIONAIS_VALIDAS


def validar_role_staff(role: str) -> bool:
    """
    Valida que a role global é uma das aceitas para Profissional staff.

    Aceitas: secretary, manager, admin (e auxiliar deprecated).
    Bloqueia: profissional (deve usar cadastro de profissional com CRM).
    """
    if not role:
        return False
    staff_roles = _get_staff_roles()
    # 'admin' e 'superadmin' também são permitidos para staff elevated
    return role in staff_roles or role in ("admin",)


def validar_crm_opcional(crm: str, uf_crm: str, role: str) -> tuple[bool, str | None]:
    """
    Valida CRM de forma contextual ao role.

    Regras:
      - Staff (secretary/manager/auxiliar): CRM e UF_CRM opcionais (None/vazio permitidos)
      - Profissional: CRM e UF_CRM obrigatórios (formato >=4 chars + UF 2 chars)
      - Admin: CRM opcional (admin não prescreve)

    Returns:
        (is_valid, error_message_or_None)
    """
    from models import ProfissionalRole

    role_normalized = ProfissionalRole.normalize(role or "")

    # Staff: CRM opcional
    if ProfissionalRole.is_staff(role_normalized) and role_normalized != ProfissionalRole.ADMIN:
        if crm and (len(crm) < 4 or len(crm) > 20):
            return False, "CRM inválido (deve ter entre 4 e 20 caracteres ou ser vazio)"
        if uf_crm and len(uf_crm) != 2:
            return False, "UF do CRM inválida (deve ter 2 caracteres ou ser vazia)"
        return True, None

    # Admin: CRM opcional
    if role_normalized == ProfissionalRole.ADMIN:
        if crm and (len(crm) < 4 or len(crm) > 20):
            return False, "CRM inválido"
        if uf_crm and len(uf_crm) != 2:
            return False, "UF do CRM inválida"
        return True, None

    # Profissional: CRM obrigatório
    if not crm or len(crm) < 4 or len(crm) > 20:
        return False, "CRM é obrigatório para profissionais (mínimo 4 caracteres)"
    if not uf_crm or len(uf_crm) != 2:
        return False, "UF do CRM é obrigatória (2 caracteres)"

    return True, None
