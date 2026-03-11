import re

def validate_cpf(cpf):
    """
    Valida formato de CPF (apenas regex, sem dígito verificador, conforme spec).
    Aceita: 000.000.000-00 ou 00000000000
    """
    if not cpf:
        return False
    
    # Remove não numéricos
    clean_cpf = re.sub(r'\D', '', str(cpf))
    
    # Verifica tamanho (11 dígitos)
    if len(clean_cpf) != 11:
        return False
        
    return True

def validate_required_fields(row, required_fields):
    """
    Valida se campos obrigatórios estão presentes e não vazios.
    """
    missing = []
    data_json = row.get('dados_json', {})
    
    # Se dados_json for string (vem do Excel), tentar parsear? 
    # O mapper fará isso antes. Aqui assumimos dict.
    
    for field in required_fields:
        val = data_json.get(field) if isinstance(data_json, dict) else None
        if not val:
            missing.append(field)
            
    return missing

def resolve_associacao(associacao_str, default_id):
    """
    Resolve nome/slug para ID. 
    Se vazio, retorna default (Legacy).
    """
    # Lógica de map simples por enquanto
    # Futuramente pode consultar banco
    if not associacao_str:
        return default_id
        
    term = str(associacao_str).lower().strip()
    
    if 'abrace' in term:
        return 'ASSOCIACAO_ID_ABRACE_FIXO' # Placeholder
    elif 'santa' in term:
        return 'ASSOCIACAO_ID_SANTA_FIXO' # Placeholder
        
    return default_id
