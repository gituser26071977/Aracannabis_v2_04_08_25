#!/usr/bin/env python3
"""
Teste rápido e simples para verificar o login
"""

import requests
import json

def test_quick():
    print("🔍 Testando conexão rápida...")
    
    try:
        # Teste básico de conexão
        print("1. Testando se backend responde...")
        response = requests.get('http://localhost:5005/api/status', timeout=3)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Resposta: {response.json()}")
        
        # Teste CSRF
        print("\n2. Testando CSRF token...")
        csrf_response = requests.get('http://localhost:5005/api/csrf-token', timeout=3)
        print(f"   Status: {csrf_response.status_code}")
        if csrf_response.status_code == 200:
            csrf_data = csrf_response.json()
            print(f"   Token obtido: {csrf_data.get('csrf_token', 'ERRO')[:20]}...")
            
            # Teste login
            print("\n3. Testando login...")
            login_data = {
                'usuario': 'teste_debug',
                'senha': '123456'
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_data['csrf_token']
            }
            
            login_response = requests.post(
                'http://localhost:5005/api/auth/login',
                json=login_data,
                headers=headers,
                timeout=5
            )
            
            print(f"   Status: {login_response.status_code}")
            if login_response.status_code == 200:
                login_result = login_response.json()
                print(f"   ✅ LOGIN SUCESSO!")
                print(f"   Token: {login_result.get('access_token', 'ERRO')[:30]}...")
            else:
                print(f"   ❌ ERRO NO LOGIN: {login_response.text}")
        else:
            print(f"   ❌ ERRO CSRF: {csrf_response.text}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    test_quick()
