from pydantic import BaseModel, ValidationError
import re
import json

REQUIRED_SOAP_FIELDS = ['subjective', 'objective', 'assessment', 'plan']

def validate_soap_response(response_text: str) -> dict:
    """Verifica se há JSON válido e os campos obrigatórios."""
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Tentar extrair json de dentro de markdown
        match = re.search(r'```json(.*?)```', response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1).strip())
            except:
                raise ValueError("JSON inválido na resposta da LLM")
        else:
            raise ValueError("Resposta da LLM não é um JSON válido")
            
    # Validar campos
    missing = [f for f in REQUIRED_SOAP_FIELDS if f not in data]
    if missing:
        raise ValueError(f"Resposta SOAP incompleta. Campos faltantes: {missing}")

    return data
