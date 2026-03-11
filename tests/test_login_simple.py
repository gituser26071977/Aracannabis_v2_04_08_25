#!/usr/bin/env python3
"""
Teste simples de login para verificar se a API está funcionando
"""

import requests

def test_login():
    print("🔍 Testando API de Login...")
    
    try:
        # 1. Testar se a API está respondendo
        print("1. Testando conexão com a API...")
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ API está respondendo")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
        print("   Verifique se o backend está rodando em http://localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return False
    
    try:
        # 2. Testar obtenção do token CSRF
        print("\n2. Obtendo token CSRF...")
        csrf_response = requests.get("http://localhost:5000/api/csrf-token", timeout=5)
        if csrf_response.status_code == 200:
            csrf_token = csrf_response.json()['csrf_token']
            print("✅ Token CSRF obtido com sucesso")
        else:
            print(f"❌ Erro ao obter CSRF token: {csrf_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao obter CSRF token: {e}")
        return False
    
    try:
        # 3. Testar login
        print("\n3. Testando login...")
        login_data = {
            'usuario': 'admin',
            'senha': 'Aracannabis@2025'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        }
        
        login_response = requests.post(
            "http://localhost:5000/api/auth/login", 
            json=login_data, 
            headers=headers,
            timeout=5
        )
        
        if login_response.status_code == 200:
            print("✅ Login realizado com sucesso!")
            data = login_response.json()
            print(f"   Usuário: {data.get('user', {}).get('nome', 'N/A')}")
            print(f"   Token recebido: {'Sim' if data.get('access_token') else 'Não'}")
            return True
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(f"   Erro: {error_data.get('error', 'Erro desconhecido')}")
            except:
                print(f"   Resposta: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o login: {e}")
        return False

def test_frontend():
    print("\n🌐 Testando Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend está respondendo")
            if "Aracannabis" in response.text:
                print("✅ Página carregada corretamente")
            else:
                print("⚠️ Página carregada mas conteúdo pode estar incorreto")
        else:
            print(f"❌ Frontend retornou status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao frontend")
        print("   Verifique se o React está rodando em http://localhost:3000")
    except Exception as e:
        print(f"❌ Erro ao conectar ao frontend: {e}")

if __name__ == '__main__':
    print("🚀 Teste de Diagnóstico do Sistema Aracannabis")
    print("=" * 50)
    
    # Testar API
    api_ok = test_login()
    
    # Testar Frontend
    test_frontend()
    
    print("\n" + "=" * 50)
    if api_ok:
        print("✅ DIAGNÓSTICO: API está funcionando corretamente")
        print("💡 SUGESTÃO: Verifique o console do navegador (F12) para erros de JavaScript")
        print("💡 SUGESTÃO: Tente recarregar a página (Ctrl+F5)")
        print("💡 SUGESTÃO: Limpe o cache do navegador")
    else:
        print("❌ DIAGNÓSTICO: Problema na API")
        print("💡 SUGESTÃO: Reinicie o backend Python")
    
    print("\n🔐 Credenciais para teste:")
    print("   Usuário: admin")
    print("   Senha: Aracannabis@2025")
