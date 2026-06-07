import requests

# Configurações
BASE_URL = "http://localhost:5002/api"
TEST_USER = "admin"  # Usuário admin
TEST_PASSWORD = "Aracannabis@2025"   # Senha do usuário admin

def test_api_endpoint(endpoint, method="GET", data=None, headers=None):
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        else:
            print(f"Método {method} não suportado")
            return
            
        print(f"\nEndpoint: {endpoint}")
        print(f"Status Code: {response.status_code}")
        print("Resposta:")
        print(response.json() if response.text else "Sem conteúdo")
        return response
        
    except Exception as e:
        print(f"Erro ao acessar {endpoint}: {str(e)}")

if __name__ == "__main__":
    # Teste de login - usando 'usuario' e 'senha' conforme documentação
    login_response = test_api_endpoint(
        endpoint="/auth/login",
        method="POST",
        data={"usuario": TEST_USER, "senha": TEST_PASSWORD}
    )
    
    if login_response and login_response.status_code == 200:
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Testar endpoints autenticados
        test_api_endpoint("/auth/profile", headers=headers)
        test_api_endpoint("/pacientes/", headers=headers)
        test_api_endpoint("/sintomas/sintomas-padrao", headers=headers)
        test_api_endpoint("/status", headers=headers)
    else:
        print("Falha no login, não foi possível testar endpoints protegidos")
