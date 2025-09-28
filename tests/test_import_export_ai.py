#!/usr/bin/env python3
"""
Teste das funcionalidades de importação/exportação e chat com IA
"""

import requests
import json
import os
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5000"
PATIENT_ID = 5  # ID do paciente de teste

def get_auth_token():
    """Obter token de autenticação"""
    # Obter token CSRF
    csrf_response = requests.get(f"{BASE_URL}/api/csrf-token")
    csrf_token = csrf_response.json()['csrf_token']
    
    # Fazer login
    login_data = {
        'usuario': 'admin',
        'senha': 'Aracannabis@2025'
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", 
                           json=login_data, 
                           headers=headers)
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Erro no login: {response.text}")

def test_export_json(token):
    """Testar exportação em JSON"""
    print("🧪 Testando exportação JSON...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{BASE_URL}/api/import-export/export/patient/{PATIENT_ID}", 
                          headers=headers)
    
    if response.status_code == 200:
        print("✅ Exportação JSON realizada com sucesso!")
        
        # Salvar arquivo para teste
        with open(f'export_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'wb') as f:
            f.write(response.content)
        print("📁 Arquivo JSON salvo para teste")
        return True
    else:
        print(f"❌ Erro na exportação JSON: {response.text}")
        return False

def test_export_csv(token):
    """Testar exportação em CSV"""
    print("🧪 Testando exportação CSV...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Testar exportação de evoluções
    response = requests.get(f"{BASE_URL}/api/import-export/export/csv/patient/{PATIENT_ID}?type=evolucoes", 
                          headers=headers)
    
    if response.status_code == 200:
        print("✅ Exportação CSV (evoluções) realizada com sucesso!")
        
        # Salvar arquivo para teste
        with open(f'export_evolucoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', 'wb') as f:
            f.write(response.content)
        print("📁 Arquivo CSV salvo para teste")
        return True
    else:
        print(f"❌ Erro na exportação CSV: {response.text}")
        return False

def test_import_text(token):
    """Testar importação de texto com IA"""
    print("🧪 Testando importação de texto com IA...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Criar arquivo de teste
    test_content = """
    Data: 2025-05-24
    Paciente relata melhora significativa da ansiedade.
    Iniciou com Óleo CBD Full Spectrum 20mg/ml.
    Dosagem: 5 gotas, 2 vezes ao dia.
    Concentração CBD: 20mg/ml
    Concentração THC: 0.2mg/ml
    Observações: Paciente mais calmo, sono melhorou.
    """
    
    # Criar arquivo temporário
    with open('test_import.txt', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    # Fazer upload
    files = {
        'file': ('test_import.txt', open('test_import.txt', 'rb'), 'text/plain')
    }
    
    response = requests.post(f"{BASE_URL}/api/import-export/import/patient/{PATIENT_ID}", 
                           files=files, 
                           headers={'Authorization': f'Bearer {token}'})
    
    # Limpar arquivo temporário
    os.remove('test_import.txt')
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Importação de texto realizada com sucesso!")
        print(f"   📊 Evoluções criadas: {result.get('evolucoes_criadas', 0)}")
        print(f"   💊 Dosagens criadas: {result.get('dosagens_criadas', 0)}")
        if result.get('ai_analysis'):
            print(f"   🤖 Análise da IA disponível")
        return True
    else:
        print(f"❌ Erro na importação: {response.text}")
        return False

def test_chat_ai(token):
    """Testar chat com IA"""
    print("🧪 Testando chat com IA...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    questions = [
        "Como está a evolução do tratamento?",
        "Qual a eficácia das dosagens atuais?",
        "Há algum padrão nos sintomas?"
    ]
    
    success_count = 0
    
    for question in questions:
        print(f"   ❓ Pergunta: {question}")
        
        data = {
            'question': question
        }
        
        response = requests.post(f"{BASE_URL}/api/import-export/chat/patient/{PATIENT_ID}", 
                               json=data, 
                               headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Resposta recebida!")
            
            if isinstance(result.get('response'), dict):
                if result['response'].get('resposta'):
                    print(f"   🤖 IA: {result['response']['resposta'][:100]}...")
                if result['response'].get('insights'):
                    print(f"   💡 Insights: {len(result['response']['insights'])} encontrados")
                if result['response'].get('sugestoes'):
                    print(f"   💭 Sugestões: {len(result['response']['sugestoes'])} encontradas")
            else:
                print(f"   🤖 IA: {str(result.get('response', ''))[:100]}...")
            
            success_count += 1
        else:
            print(f"   ❌ Erro: {response.text}")
        
        print()
    
    if success_count == len(questions):
        print("✅ Todos os testes de chat com IA foram bem-sucedidos!")
        return True
    else:
        print(f"⚠️ {success_count}/{len(questions)} testes de chat foram bem-sucedidos")
        return False

def main():
    """Executar todos os testes"""
    print("🚀 Iniciando testes de Importação/Exportação e Chat com IA")
    print("=" * 60)
    
    try:
        # Obter token de autenticação
        print("🔐 Fazendo login...")
        token = get_auth_token()
        print("✅ Login realizado com sucesso!")
        print()
        
        # Executar testes
        tests = [
            ("Exportação JSON", test_export_json),
            ("Exportação CSV", test_export_csv),
            ("Importação com IA", test_import_text),
            ("Chat com IA", test_chat_ai)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"📋 Executando: {test_name}")
            print("-" * 40)
            
            try:
                success = test_func(token)
                results.append((test_name, success))
            except Exception as e:
                print(f"❌ Erro no teste {test_name}: {str(e)}")
                results.append((test_name, False))
            
            print()
        
        # Resumo dos resultados
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"{test_name}: {status}")
            if success:
                passed += 1
        
        print()
        print(f"🎯 Resultado Final: {passed}/{total} testes passaram")
        
        if passed == total:
            print("🎉 Todos os testes foram bem-sucedidos!")
            print("🚀 Sistema de Importação/Exportação e IA está funcionando perfeitamente!")
        else:
            print("⚠️ Alguns testes falharam. Verifique os logs acima.")
        
    except Exception as e:
        print(f"💥 Erro crítico: {str(e)}")
        return False
    
    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
