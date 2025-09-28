#!/usr/bin/env python3
import requests
import json

# Configurações
BASE_URL = "http://localhost:5004/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
# Testar ambos os endpoints
DOSAGENS_URL_1 = f"{BASE_URL}/grafico/paciente/1"  # Endpoint antigo
DOSAGENS_URL_2 = f"{BASE_URL}/dosagens/grafico/paciente/1"  # Endpoint novo (usado pelo frontend)

def test_dosagens_endpoint():
    print("=== TESTE DE DEBUG - ENDPOINT DE DOSAGENS ===\n")
    
    # Passo 1: Fazer login
    print("1. Tentando fazer login...")
    # Tentar diferentes combinações de usuário/senha
    credentials_to_try = [
        {"usuario": "teste_debug", "senha": "123456"},
        {"usuario": "admin", "senha": "admin"},
        {"usuario": "admin", "senha": "admin123"},
        {"usuario": "teste", "senha": "teste"}
    ]
    
    token = None
    for login_data in credentials_to_try:
        print(f"Tentando: {login_data['usuario']}/{login_data['senha']}")
    
        try:
            login_response = requests.post(LOGIN_URL, json=login_data)
            print(f"Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_result = login_response.json()
                token = login_result.get('access_token')
                print(f"✅ LOGIN SUCESSO! Token: {token[:50]}..." if token else "Token não encontrado")
                break
            else:
                print(f"❌ Falhou: {login_response.text}")
                
        except Exception as e:
            print(f"ERRO na requisição: {e}")
    
    if not token:
        print("ERRO: Não foi possível fazer login com nenhuma credencial")
        return
    
    # Passo 2: Testar ambos os endpoints de dosagens
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    params = {"periodo": "integral"}
    
    for i, url in enumerate([DOSAGENS_URL_1, DOSAGENS_URL_2], 1):
        print(f"\n{i+1}. Testando endpoint: {url}")
        
        try:
            dosagens_response = requests.get(url, headers=headers, params=params)
            print(f"Status: {dosagens_response.status_code}")
            
            if dosagens_response.status_code == 200:
                dosagens_result = dosagens_response.json()
                
                # Verificar estrutura da resposta
                if 'dados_grafico' in dosagens_result:
                    dados = dosagens_result['dados_grafico']
                    print(f"Pontos no gráfico: {len(dados)}")
                    if dados:
                        print(f"Primeiro ponto: {dados[0]}")
                        print(f"Tipo de valor Y: {type(dados[0]['y'])}, Valor: {dados[0]['y']}")
                    else:
                        print("AVISO: Array de dados_grafico está vazio")
                else:
                    print("ERRO: Campo 'dados_grafico' não encontrado na resposta")
                    
            else:
                print(f"ERRO: {dosagens_response.text}")
                
        except Exception as e:
            print(f"ERRO na requisição: {e}")

if __name__ == "__main__":
    test_dosagens_endpoint()
