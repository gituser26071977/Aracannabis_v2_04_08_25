#!/usr/bin/env python3
"""
Script de teste completo para funcionalidades de importação/exportação e chat com IA
"""

import requests

# Configurações
BASE_URL = "http://localhost:5000"
PATIENT_ID = 5  # ID do paciente para teste

def get_auth_token():
    """Obter token de autenticação"""
    # Primeiro, obter token CSRF
    csrf_response = requests.get(f"{BASE_URL}/api/csrf-token")
    if csrf_response.status_code != 200:
        print(f"Erro ao obter token CSRF: {csrf_response.status_code}")
        return None
    
    csrf_token = csrf_response.json().get('csrf_token')
    
    login_data = {
        "usuario": "admin",
        "senha": "Aracannabis@2025"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf_token
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Erro no login: {response.status_code} - {response.text}")
        return None

def test_export_json(token):
    """Testar exportação em JSON"""
    print("\n=== TESTE: Exportação JSON ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/import-export/export/patient/{PATIENT_ID}", headers=headers)
    
    if response.status_code == 200:
        print("✅ Exportação JSON funcionando!")
        # Salvar arquivo para teste
        with open("export_test.json", "wb") as f:
            f.write(response.content)
        print("📁 Arquivo export_test.json salvo")
    else:
        print(f"❌ Erro na exportação JSON: {response.status_code} - {response.text}")

def test_export_csv(token):
    """Testar exportação em CSV"""
    print("\n=== TESTE: Exportação CSV ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    for csv_type in ['evolucoes', 'dosagens', 'sintomas']:
        response = requests.get(f"{BASE_URL}/api/import-export/export/csv/patient/{PATIENT_ID}?type={csv_type}", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Exportação CSV {csv_type} funcionando!")
            with open(f"export_{csv_type}_test.csv", "wb") as f:
                f.write(response.content)
            print(f"📁 Arquivo export_{csv_type}_test.csv salvo")
        else:
            print(f"❌ Erro na exportação CSV {csv_type}: {response.status_code} - {response.text}")

def test_import_text(token):
    """Testar importação de arquivo de texto"""
    print("\n=== TESTE: Importação de Texto ===")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Usar o arquivo de teste que criamos
    with open("test_import_simple.txt", "rb") as f:
        files = {"file": ("test_import_simple.txt", f, "text/plain")}
        response = requests.post(f"{BASE_URL}/api/import-export/import/patient/{PATIENT_ID}", 
                               headers=headers, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Importação de texto funcionando!")
        print(f"📊 Evoluções criadas: {result.get('evolucoes_criadas', 0)}")
        print(f"📊 Dosagens criadas: {result.get('dosagens_criadas', 0)}")
        print(f"📊 Sintomas criados: {result.get('sintomas_criados', 0)}")
        if result.get('erros'):
            print(f"⚠️ Erros: {result['erros']}")
    else:
        print(f"❌ Erro na importação de texto: {response.status_code} - {response.text}")

def test_chat_ai(token):
    """Testar chat com IA"""
    print("\n=== TESTE: Chat com IA ===")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    questions = [
        "Como está a evolução do tratamento?",
        "Qual a dosagem atual do paciente?",
        "Há algum padrão nos sintomas?"
    ]
    
    for question in questions:
        print(f"\n🤖 Pergunta: {question}")
        
        chat_data = {"question": question}
        response = requests.post(f"{BASE_URL}/api/import-export/chat/patient/{PATIENT_ID}", 
                               headers=headers, json=chat_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat com IA funcionando!")
            
            # Verificar se a resposta tem a estrutura esperada
            if 'response' in result:
                ai_response = result['response']
                if isinstance(ai_response, dict):
                    print(f"💬 Resposta: {ai_response.get('resposta', 'Resposta não estruturada')}")
                    if ai_response.get('insights'):
                        print(f"💡 Insights: {ai_response['insights']}")
                    if ai_response.get('sugestoes'):
                        print(f"💊 Sugestões: {ai_response['sugestoes']}")
                else:
                    print(f"💬 Resposta: {ai_response}")
            
            if 'context_summary' in result:
                summary = result['context_summary']
                print(f"📈 Contexto analisado: {summary}")
        else:
            print(f"❌ Erro no chat: {response.status_code} - {response.text}")

def test_api_status():
    """Testar status da API"""
    print("\n=== TESTE: Status da API ===")
    
    response = requests.get(f"{BASE_URL}/api/status")
    if response.status_code == 200:
        status = response.json()
        print("✅ API funcionando!")
        print(f"📊 Status: {status.get('status')}")
        print(f"🔒 Segurança: {status.get('security')}")
    else:
        print(f"❌ Erro no status da API: {response.status_code}")

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES COMPLETOS DO SISTEMA ARACANNABIS")
    print("=" * 60)
    
    # Testar status da API
    test_api_status()
    
    # Obter token de autenticação
    print("\n=== AUTENTICAÇÃO ===")
    token = get_auth_token()
    if not token:
        print("❌ Falha na autenticação. Encerrando testes.")
        return
    
    print("✅ Autenticação bem-sucedida!")
    
    # Executar todos os testes
    test_export_json(token)
    test_export_csv(token)
    test_import_text(token)
    test_chat_ai(token)
    
    print("\n" + "=" * 60)
    print("🎉 TESTES CONCLUÍDOS!")
    print("\nArquivos gerados:")
    print("- export_test.json")
    print("- export_evolucoes_test.csv")
    print("- export_dosagens_test.csv") 
    print("- export_sintomas_test.csv")

if __name__ == "__main__":
    main()
