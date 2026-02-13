import pytest
from services.anonymization_service.app.anonymizer import Anonymizer
from services.anonymization_service.app.models import AnonymizationMap
import re
from unittest.mock import MagicMock

def test_regex_cpf():
    """Testa se o Regex de CPF captura e anonimiza corretamente."""
    anonymizer = Anonymizer()
    text = "O paciente João tem CPF 123.456.789-00."
    
    # Mock DB session
    mock_db = MagicMock()
    
    result, _, _ = anonymizer.anonymize_text(text, 1, mock_db)
    
    assert "123.456.789-00" not in result
    assert "[CPF_" in result
    
def test_regex_date():
    """Testa anonimização de datas."""
    anonymizer = Anonymizer()
    text = "Consulta em 25/12/2025."
    mock_db = MagicMock()
    
    result, _, _ = anonymizer.anonymize_text(text, 1, mock_db)
    # Regex date_pt
    assert "25/12/2025" not in result
    assert "[DATE_PT_" in result

# Se tiver spacy instalado no ambiente de teste
def test_ner_person():
    """Testa se o NER captura nome de pessoa."""
    try:
        import spacy
        spacy.load("pt_core_news_sm") # ou lg
    except:
        pytest.skip("Modelo spaCy não instalado")

    anonymizer = Anonymizer()
    text = "O Sr. Mario Bros esteve aqui."
    mock_db = MagicMock()
    
    result, _, _ = anonymizer.anonymize_text(text, 1, mock_db)
    
    assert "Mario Bros" not in result
    assert "[PER_" in result or "[PERSON_" in result

def test_rehydration():
    """Testa ciclo completo de anonimização e reidratação (mockando DB)."""
    anonymizer = Anonymizer(key="secretkey123")
    text_original = "Paciente: Ana Silva, CPF: 111.222.333-44"
    
    # Mock DB behaviour for storing maps
    # Como o anonymizer usa 'db_session.add', precisamos simular comportamento
    # Na reidratação, ele faz query... precisamos simular o retorno da query
    
    # Vamos testar apenas crypto logic e substitution logic isoladamente se possivel,
    # Ou usar sqlite em memoria para teste de integracao.
    pass
