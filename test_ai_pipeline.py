import requests
import json
import time

# Configurações do Ambiente Local (Docker)
BASE_URL = "http://localhost:5002/api" # Porta mapeada no docker-compose do backend (ajuste se for diferente)
USER_EMAIL = "admin@aracannabis.com.br" # Usuário existente (ou criar um mock)
USER_PASS = "admin123" # Senha padrão (ajuste conforme seu banco local)

def get_auth_token():
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"email": USER_EMAIL, "senha": USER_PASS})
        if resp.status_code == 200:
            token = resp.json().get('access_token')
            print("✅ Login realizado com sucesso. Token obtido.")
            return token
        else:
            print(f"❌ Falha no login: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ Erro de conexão ao tentar login: {e}")
        return None

def test_soap_generation(token):
    print("\n🧪 Testando Geração de SOAP Auditável (DeepSeek)...")
    
    # Texto Clínico com Dados Sensíveis (PII) para anonimização
    # "João da Silva" -> Deve virar [PERSON_XXX]
    # "123.456.789-00" -> Deve virar [CPF_XXX]
    clinical_text = """
    Paciente João da Silva, 45 anos, compareceu à consulta em 11/02/2025.
    Queixa principal: insônia e ansiedade leve.
    Relata uso de CBD 5% mas sente pouca melhora.
    PA: 120/80 mmHg. FC: 78 bpm.
    Plano: Aumentar dose para 10 gotas à noite.
    Retorno em 30 dias.
    CPF: 123.456.789-00.
    """
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "text": clinical_text,
        "patient_id": 1, # ID válido no banco
        "task": "soap_summary"
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/ai-clinical/generate-soap", json=payload, headers=headers)
        duration = time.time() - start_time
        
        if resp.status_code == 200:
            data = resp.json()
            soap = data.get('soap', {})
            meta = data.get('meta', {})
            
            print(f"✅ Sucesso! Tempo total: {duration:.2f}s")
            print(f"   Provider: {meta.get('provider')}")
            print(f"   Tokens usados: {meta.get('tokens_used')}")
            print("\n📋 Resumo SOAP Gerado:")
            print(json.dumps(soap, indent=2, ensure_ascii=False))
            
            # Validação básica de anonimização (se conseguirmos ver o log do backend, veríamos o texto anonimizado)
            # Aqui só vemos o output reidratado (se a reidratação funcionou) ou anonimizado (se falhou reidratação).
            # O ideal é que o médico veja o nome REAL (reidratado).
            
            if "João da Silva" in str(soap):
                print("\n✅ Reidratação funcionando: Nome original retornado no SOAP.")
            else:
                print("\n⚠️  Atenção: Nome original NÃO encontrado no SOAP (pode estar anonimizado).")
                
        else:
            print(f"❌ Erro na geração: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando Teste de Pipeline de IA Auditável...")
    token = get_auth_token()
    if token:
        test_soap_generation(token)
    else:
        print("⚠️  Pulei o teste de SOAP por falta de token. Verifique suas credenciais no script.")
