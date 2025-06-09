#!/usr/bin/env python3
import requests
import json

def test_login(port, usuario, senha, csrf_token=None):
    print(f"\n🔍 Testando login na porta {port}")
    print(f"Usuário: {usuario}")
    print(f"Senha: {senha}")
    
    try:
        # Testar conexão básica
        status_url = f"http://localhost:{port}/api/status"
        print(f"Testando conexão: {status_url}")
        status_response = requests.get(status_url, timeout=5)
        print(f"Status da conexão: {status_response.status_code}")
        
        # Obter token CSRF se necessário
        if not csrf_token:
            csrf_url = f"http://localhost:{port}/api/csrf-token"
            print(f"Obtendo CSRF token: {csrf_url}")
            csrf_response = requests.get(csrf_url, timeout=5)
            print(f"CSRF Response Status: {csrf_response.status_code}")
            
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                csrf_token = csrf_data.get('csrf_token', 'test-csrf-token-123')
                print(f"CSRF Token obtido: {csrf_token[:20]}...")
            else:
                csrf_token = 'test-csrf-token-123'
                print(f"Usando CSRF token padrão: {csrf_token}")
        
        # Testar login
        login_url = f"http://localhost:{port}/api/auth/login"
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        }
        
        login_data = {
            'usuario': usuario,
            'senha': senha
        }
        
        print(f"Fazendo login em: {login_url}")
        print(f"Headers: {headers}")
        print(f"Data: {login_data}")
        
        login_response = requests.post(login_url, headers=headers, json=login_data, timeout=10)
        
        print(f"Login Response Status: {login_response.status_code}")
        print(f"Login Response Headers: {dict(login_response.headers)}")
        print(f"Login Response Text: {login_response.text}")
        
        if login_response.status_code == 200:
            print("✅ LOGIN FUNCIONANDO!")
            data = login_response.json()
            if 'access_token' in data:
                print(f"Token recebido: {data['access_token'][:50]}...")
            if 'user' in data:
                print(f"Usuário: {data['user'].get('nome', 'N/A')}")
            return True
        else:
            print("❌ Erro no login")
            return False
            
    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False

def main():
    print("🚀 DIAGNÓSTICO DE LOGIN - SISTEMA ARACANNABIS")
    print("=" * 60)
    
    # Credenciais para testar
    credenciais = [
        ("admin3", "Admin@123456"),
        ("admin", "Aracannabis@2025"),
        ("admin", "admin"),
        ("admin2", "Admin@123456")
    ]
    
    # Portas para testar
    portas = [5000, 5001, 5002]
    
    resultados = {}
    
    for porta in portas:
        print(f"\n{'='*20} PORTA {porta} {'='*20}")
        resultados[porta] = {}
        
        for usuario, senha in credenciais:
            resultado = test_login(porta, usuario, senha)
            resultados[porta][f"{usuario}/{senha}"] = resultado
            
            if resultado:
                print(f"✅ SUCESSO: Porta {porta} - {usuario}/{senha}")
                break
        
        print(f"\n{'='*50}")
    
    # Resumo final
    print("\n🎯 RESUMO DOS RESULTADOS:")
    print("=" * 60)
    
    for porta, testes in resultados.items():
        print(f"\nPorta {porta}:")
        for credencial, sucesso in testes.items():
            status = "✅ FUNCIONANDO" if sucesso else "❌ FALHOU"
            print(f"  {credencial}: {status}")
    
    # Recomendações
    print("\n💡 RECOMENDAÇÕES:")
    print("=" * 60)
    
    funcionando = []
    for porta, testes in resultados.items():
        for credencial, sucesso in testes.items():
            if sucesso:
                funcionando.append(f"Porta {porta} - {credencial}")
    
    if funcionando:
        print("✅ Configurações funcionando:")
        for config in funcionando:
            print(f"  - {config}")
    else:
        print("❌ Nenhuma configuração funcionando!")
        print("Possíveis soluções:")
        print("  1. Verificar se os servidores estão rodando")
        print("  2. Criar novo usuário admin")
        print("  3. Verificar configuração do banco de dados")

if __name__ == "__main__":
    main()
