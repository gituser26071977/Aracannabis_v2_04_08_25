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
