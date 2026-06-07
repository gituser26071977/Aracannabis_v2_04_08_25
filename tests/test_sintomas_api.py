#!/usr/bin/env python3
"""
Teste das APIs de sintomas
"""

import requests

# Configuração
BASE_URL = "http://localhost:5004/api"

def test_sintomas_api():
    print("🧪 Testando APIs de Sintomas...")
    
    # 0. Obter token CSRF
    print("\n0. Obtendo token CSRF...")
    try:
        csrf_response = requests.get(f"{BASE_URL}/csrf-token")
        csrf_token = csrf_response.json().get('csrf_token', 'test-csrf-token-123')
        print(f"CSRF Token: {csrf_token}")
    except:
        csrf_token = 'test-csrf-token-123'
    
    # 1. Fazer login para obter token
    print("\n1. Fazendo login...")
    login_data = {
        "usuario": "admin@aracannabis.com",
        "senha": "admin123"
    }
    
    login_headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=login_headers)
        print(f"Status login: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print("✅ Login realizado com sucesso")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # 2. Testar listagem de sintomas padrão
            print("\n2. Testando listagem de sintomas padrão...")
            response = requests.get(f"{BASE_URL}/sintomas/sintomas-padrao", headers=headers)
            print(f"Status sintomas padrão: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Sintomas padrão obtidos:")
                print(f"   Padrão: {data.get('sintomas_padrao', [])}")
                print(f"   Personalizados: {data.get('sintomas_personalizados', [])}")
            else:
                print(f"❌ Erro ao obter sintomas padrão: {response.text}")
            
            # 3. Testar criação de sintoma personalizado
            print("\n3. Testando criação de sintoma personalizado...")
            sintoma_data = {
                "nome_sintoma": "Teste Sintoma Personalizado"
            }
            
            response = requests.post(f"{BASE_URL}/sintomas/sintoma-personalizado", 
                                   json=sintoma_data, headers=headers)
            print(f"Status criação sintoma: {response.status_code}")
            
            if response.status_code == 201:
                print("✅ Sintoma personalizado criado com sucesso")
            else:
                print(f"❌ Erro ao criar sintoma: {response.text}")
            
            # 4. Testar listagem de sintomas de um paciente (ID 1)
            print("\n4. Testando listagem de sintomas do paciente...")
            response = requests.get(f"{BASE_URL}/sintomas/paciente/1", headers=headers)
            print(f"Status listagem sintomas: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sintomas do paciente: {len(data.get('sintomas', []))} registros")
            else:
                print(f"❌ Erro ao listar sintomas: {response.text}")
            
            # 5. Testar registro de sintoma
            print("\n5. Testando registro de sintoma...")
            sintoma_registro = {
                "data": "2025-01-26",
                "sintoma": "Insônia",
                "intensidade": 7
            }
            
            response = requests.post(f"{BASE_URL}/sintomas/paciente/1", 
                                   json=sintoma_registro, headers=headers)
            print(f"Status registro sintoma: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("✅ Sintoma registrado com sucesso")
            else:
                print(f"❌ Erro ao registrar sintoma: {response.text}")
            
            # 6. Testar dados do gráfico
            print("\n6. Testando dados do gráfico...")
            response = requests.get(f"{BASE_URL}/sintomas/grafico/paciente/1", headers=headers)
            print(f"Status gráfico: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Dados do gráfico: {len(data.get('dados_grafico', []))} datasets")
            else:
                print(f"❌ Erro ao obter dados do gráfico: {response.text}")
                
        else:
            print(f"❌ Erro no login: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor")
        print("   Certifique-se de que o servidor está rodando em localhost:5004")
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    test_sintomas_api()
