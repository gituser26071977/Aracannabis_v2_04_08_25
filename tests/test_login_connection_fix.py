#!/usr/bin/env python3
"""
Teste para verificar se a correção da porta resolveu o problema de conexão no login
"""

import requests
import json
import time

def test_backend_connection():
    """Testa se o backend está respondendo na porta correta"""
    print("🔍 TESTANDO CONEXÃO COM O BACKEND...")
    
    try:
        # Testar porta 5000 (correta)
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        if response.status_code == 200:
            print("✅ Backend respondendo na porta 5000 (CORRETO)")
            print(f"   Status: {response.json()}")
            return True
        else:
            print(f"❌ Backend na porta 5000 retornou status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend não está respondendo na porta 5000")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com backend: {e}")
        return False

def test_csrf_token():
    """Testa se o token CSRF está sendo obtido corretamente"""
    print("\n🔐 TESTANDO TOKEN CSRF...")
    
    try:
        response = requests.get('http://localhost:5000/api/csrf-token', timeout=5)
        if response.status_code == 200:
            csrf_data = response.json()
            if 'csrf_token' in csrf_data:
                print("✅ Token CSRF obtido com sucesso")
                print(f"   Token: {csrf_data['csrf_token'][:20]}...")
                return csrf_data['csrf_token']
            else:
                print("❌ Resposta não contém token CSRF")
                return None
        else:
            print(f"❌ Erro ao obter CSRF token: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao obter CSRF token: {e}")
        return None

def test_login_endpoint(csrf_token):
    """Testa o endpoint de login com as credenciais padrão"""
    print("\n🔑 TESTANDO LOGIN...")
    
    if not csrf_token:
        print("❌ Não é possível testar login sem token CSRF")
        return False
    
    try:
        login_data = {
            'usuario': 'admin',
            'senha': 'Aracannabis@2025'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        }
        
        response = requests.post(
            'http://localhost:5000/api/auth/login',
            json=login_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            login_response = response.json()
            if 'access_token' in login_response:
                print("✅ Login realizado com sucesso!")
                print(f"   Token JWT: {login_response['access_token'][:30]}...")
                print(f"   Usuário: {login_response.get('user', {}).get('nome', 'N/A')}")
                return True
            else:
                print("❌ Resposta de login não contém access_token")
                print(f"   Resposta: {login_response}")
                return False
        else:
            print(f"❌ Erro no login: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Erro: {error_data}")
            except:
                print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante login: {e}")
        return False

def test_cors_headers():
    """Testa se os headers CORS estão configurados corretamente"""
    print("\n🌐 TESTANDO CONFIGURAÇÃO CORS...")
    
    try:
        # Fazer uma requisição OPTIONS para simular preflight
        response = requests.options(
            'http://localhost:5000/api/auth/login',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,X-CSRF-Token'
            },
            timeout=5
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print("✅ Headers CORS encontrados:")
        for header, value in cors_headers.items():
            if value:
                print(f"   {header}: {value}")
            else:
                print(f"   {header}: ❌ NÃO ENCONTRADO")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar CORS: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DE CORREÇÃO DO PROBLEMA DE CONEXÃO NO LOGIN")
    print("=" * 60)
    
    # Teste 1: Conexão com backend
    backend_ok = test_backend_connection()
    
    if not backend_ok:
        print("\n❌ FALHA: Backend não está respondendo. Verifique se o servidor está rodando.")
        print("   Execute: python app.py")
        return
    
    # Teste 2: Token CSRF
    csrf_token = test_csrf_token()
    
    # Teste 3: Login
    login_ok = test_login_endpoint(csrf_token)
    
    # Teste 4: CORS
    cors_ok = test_cors_headers()
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Backend (porta 5000):     {'✅ OK' if backend_ok else '❌ FALHA'}")
    print(f"Token CSRF:               {'✅ OK' if csrf_token else '❌ FALHA'}")
    print(f"Login:                    {'✅ OK' if login_ok else '❌ FALHA'}")
    print(f"CORS:                     {'✅ OK' if cors_ok else '❌ FALHA'}")
    
    if backend_ok and csrf_token and login_ok:
        print("\n🎉 SUCESSO! O problema de conexão foi resolvido!")
        print("   O login simplificado agora deve funcionar corretamente.")
        print("   Teste no frontend: http://localhost:3000")
    else:
        print("\n⚠️  ATENÇÃO: Ainda há problemas que precisam ser resolvidos.")
        
        if not backend_ok:
            print("   - Inicie o backend: python app.py")
        if not csrf_token:
            print("   - Verifique a configuração do CSRF no backend")
        if not login_ok:
            print("   - Verifique as credenciais e configuração de autenticação")

if __name__ == "__main__":
    main()
