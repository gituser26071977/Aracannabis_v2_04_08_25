#!/usr/bin/env python3
"""
Script para testar o login do frontend
"""

import requests

BASE_URL = "http://localhost:5000"

def test_frontend_login():
    """Simular exatamente o que o frontend faz"""
    print("🔍 TESTANDO LOGIN DO FRONTEND")
    print("=" * 50)
    
    try:
        # 1. Obter token CSRF (como o frontend faz)
        print("1. Obtendo token CSRF...")
        csrf_response = requests.get(f"{BASE_URL}/api/csrf-token")
        print(f"   Status: {csrf_response.status_code}")
        
        if csrf_response.status_code != 200:
            print(f"   ❌ Erro: {csrf_response.text}")
            return
        
        csrf_data = csrf_response.json()
        csrf_token = csrf_data.get('csrf_token')
        print(f"   ✅ Token CSRF: {csrf_token[:20]}...")
        
        # 2. Fazer login (como o frontend faz)
        print("\n2. Fazendo login...")
        login_data = {
            "usuario": "admin",
            "senha": "Aracannabis@2025"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf_token
        }
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login", 
            json=login_data, 
            headers=headers
        )
        
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            print("   ✅ Login bem-sucedido!")
            print(f"   👤 Usuário: {login_result.get('user', {}).get('nome', 'N/A')}")
            print(f"   🔑 Token: {login_result.get('access_token', 'N/A')[:20]}...")
            
            # 3. Testar acesso autenticado
            print("\n3. Testando acesso autenticado...")
            auth_headers = {
                "Authorization": f"Bearer {login_result.get('access_token')}",
                "Content-Type": "application/json"
            }
            
            profile_response = requests.get(f"{BASE_URL}/api/auth/profile", headers=auth_headers)
            print(f"   Status perfil: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                print("   ✅ Acesso autenticado funcionando!")
            else:
                print(f"   ❌ Erro no acesso: {profile_response.text}")
                
        else:
            print(f"   ❌ Erro no login: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")

def test_frontend_connection():
    """Testar se o frontend está acessível"""
    print("\n🌐 TESTANDO CONEXÃO COM FRONTEND")
    print("=" * 50)
    
    try:
        frontend_response = requests.get("http://localhost:3000", timeout=5)
        print(f"Status frontend: {frontend_response.status_code}")
        
        if frontend_response.status_code == 200:
            print("✅ Frontend está respondendo")
        else:
            print("❌ Frontend com problemas")
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend não está acessível")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    test_frontend_login()
    test_frontend_connection()
    
    print("\n" + "=" * 50)
    print("💡 INSTRUÇÕES PARA TESTE MANUAL:")
    print("1. Abra http://localhost:3000 no navegador")
    print("2. Abra o console do navegador (F12)")
    print("3. Tente fazer login com:")
    print("   Usuário: admin")
    print("   Senha: Aracannabis@2025")
    print("4. Verifique os logs no console")
    print("5. Verifique a aba Network para ver as requisições")
