"""
Ferramentas para verificação de cadastros de profissionais
"""
import re
import dns.resolver
from models import Profissional, SolicitacoesCadastro
from datetime import datetime

def validate_crm_format(crm: str, uf: str) -> dict:
    """
    Valida formato do CRM
    
    Args:
        crm: Número do CRM
        uf: UF do CRM (ex: SP, RJ)
    
    Returns:
        dict com resultado da validação
    """
    # CRM deve ter entre 4 e 6 dígitos
    if not crm or not crm.isdigit():
        return {
            "valid": False,
            "reason": "CRM deve conter apenas números",
            "confidence": 1.0
        }
    
    if len(crm) < 4 or len(crm) > 6:
        return {
            "valid": False,
            "reason": "CRM deve ter entre 4 e 6 dígitos",
            "confidence": 1.0
        }
    
    # UF deve ter 2 letras
    if not uf or len(uf) != 2 or not uf.isalpha():
        return {
            "valid": False,
            "reason": "UF inválida",
            "confidence": 1.0
        }
    
    return {
        "valid": True,
        "reason": "Formato válido",
        "confidence": 0.9
    }


def check_duplicate_crm(crm: str, uf: str, exclude_id: int = None) -> dict:
    """
    Verifica se CRM já está cadastrado
    
    Args:
        crm: Número do CRM
        uf: UF do CRM
    
    Returns:
        dict com resultado da verificação
    """
    # Verificar em profissionais aprovados
    existing_prof = Profissional.query.filter_by(crm=crm, uf_crm=uf).first()
    if existing_prof:
        return {
            "duplicate": True,
            "reason": f"CRM já cadastrado para {existing_prof.nome}",
            "confidence": 1.0
        }
    
    # Verificar em solicitações pendentes
    query = SolicitacoesCadastro.query.filter_by(
        crm=crm, 
        uf_crm=uf, 
        status='pendente'
    )
    if exclude_id:
        query = query.filter(SolicitacoesCadastro.id != exclude_id)
    
    existing_sol = query.first()
    if existing_sol:
        return {
            "duplicate": True,
            "reason": "CRM já possui solicitação pendente",
            "confidence": 1.0
        }
    
    return {
        "duplicate": False,
        "reason": "CRM não encontrado no sistema",
        "confidence": 1.0
    }


def validate_email_format(email: str) -> dict:
    """
    Valida formato do email
    
    Args:
        email: Endereço de email
    
    Returns:
        dict com resultado da validação
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email or not re.match(pattern, email):
        return {
            "valid": False,
            "reason": "Formato de email inválido",
            "confidence": 1.0
        }
    
    return {
        "valid": True,
        "reason": "Formato válido",
        "confidence": 0.95
    }


def verify_email_domain(email: str) -> dict:
    """
    Verifica se domínio do email existe e tem registros MX
    
    Args:
        email: Endereço de email
    
    Returns:
        dict com resultado da verificação
    """
    try:
        domain = email.split('@')[1]
        
        # Verificar registros MX
        mx_records = dns.resolver.resolve(domain, 'MX')
        
        if not mx_records:
            return {
                "valid": False,
                "reason": "Domínio sem servidores de email (MX)",
                "confidence": 0.9
            }
        
        return {
            "valid": True,
            "reason": f"Domínio válido com {len(mx_records)} servidor(es) MX",
            "confidence": 0.85
        }
        
    except dns.resolver.NXDOMAIN:
        return {
            "valid": False,
            "reason": "Domínio não existe",
            "confidence": 1.0
        }
    except dns.resolver.NoAnswer:
        return {
            "valid": False,
            "reason": "Domínio sem registros MX",
            "confidence": 0.8
        }
    except Exception as e:
        return {
            "valid": False,
            "reason": f"Erro ao verificar domínio: {str(e)}",
            "confidence": 0.5
        }


def detect_disposable_email(email: str) -> dict:
    """
    Detecta se email é de serviço descartável
    
    Args:
        email: Endereço de email
    
    Returns:
        dict com resultado da detecção
    """
    # Lista de domínios descartáveis conhecidos
    disposable_domains = [
        'tempmail.com', 'guerrillamail.com', '10minutemail.com',
        'mailinator.com', 'throwaway.email', 'temp-mail.org',
        'fakeinbox.com', 'trashmail.com', 'maildrop.cc'
    ]
    
    try:
        domain = email.split('@')[1].lower()
        
        if domain in disposable_domains:
            return {
                "disposable": True,
                "reason": f"Domínio {domain} é serviço de email descartável",
                "confidence": 1.0
            }
        
        return {
            "disposable": False,
            "reason": "Domínio não está na lista de descartáveis",
            "confidence": 0.9
        }
        
    except Exception as e:
        return {
            "disposable": False,
            "reason": f"Erro ao verificar: {str(e)}",
            "confidence": 0.5
        }


def check_duplicate_email(email: str, exclude_id: int = None) -> dict:
    """
    Verifica se email já está cadastrado
    
    Args:
        email: Endereço de email
    
    Returns:
        dict com resultado da verificação
    """
    # Verificar em profissionais
    existing_prof = Profissional.query.filter_by(email=email.lower()).first()
    if existing_prof:
        return {
            "duplicate": True,
            "reason": f"Email já cadastrado para {existing_prof.nome}",
            "confidence": 1.0
        }
    
    # Verificar em solicitações pendentes
    query = SolicitacoesCadastro.query.filter_by(
        email=email.lower(),
        status='pendente'
    )
    if exclude_id:
        query = query.filter(SolicitacoesCadastro.id != exclude_id)
        
    existing_sol = query.first()
    if existing_sol:
        return {
            "duplicate": True,
            "reason": "Email já possui solicitação pendente",
            "confidence": 1.0
        }
    
    return {
        "duplicate": False,
        "reason": "Email não encontrado no sistema",
        "confidence": 1.0
    }


def analyze_registration_timing(solicitacao_id: int) -> dict:
    """
    Analisa padrão temporal de cadastros
    
    Args:
        solicitacao_id: ID da solicitação
    
    Returns:
        dict com análise de risco
    """
    solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
    if not solicitacao:
        return {
            "risk": "unknown",
            "reason": "Solicitação não encontrada",
            "confidence": 0.0
        }
    
    # Verificar cadastros recentes do mesmo IP (se disponível)
    # Por enquanto, análise básica de timing
    
    # Verificar se há múltiplas solicitações em curto período
    recent_requests = SolicitacoesCadastro.query.filter(
        SolicitacoesCadastro.data_solicitacao >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    
    if recent_requests > 10:
        return {
            "risk": "medium",
            "reason": f"{recent_requests} solicitações hoje (possível spam)",
            "confidence": 0.6
        }
    
    return {
        "risk": "low",
        "reason": "Padrão de cadastro normal",
        "confidence": 0.9
    }
