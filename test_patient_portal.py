"""
Script para testar a API de autenticação de pacientes

Testa todos os endpoints:
1. Verificar CPF
2. Registrar paciente
3. Login
4. Acessar portal (dados do paciente)
"""

import requests
import json

BASE_URL = "http://localhost:5002"

def test_patient_auth_flow():
    print("🧪 Testando fluxo de autenticação de pacientes\n")
    print("=" * 60)
    
    # 1. Verificar se CPF existe
    print("\n1️⃣ Verificando CPF no sistema...")
    
    # Usar um CPF de paciente existente (vamos pegar da base)
    # Para o teste, vamos usar um CPF fictício - ajuste com CPF real do seu banco
    cpf_teste = "12345678900"  # AJUSTAR COM CPF REAL
    
    response = requests.post(
        f"{BASE_URL}/api/patient-auth/verify-cpf",
        json={"cpf": cpf_teste}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200 and response.json().get('exists'):
        print("✅ CPF encontrado!")
        
        # Verificar se já tem conta
        if response.json().get('has_account'):
            print("⚠️ Paciente já tem conta cadastrada. Pulando registro.")
            email_teste = input("Digite o email ja cadastrado: ")
        else:
            # 2. Registrar paciente
            print("\n2️⃣ Registrando conta do paciente...")
            
            email_teste = "paciente.teste@email.com"
            senha_teste = "senha123"
            
            response = requests.post(
                f"{BASE_URL}/api/patient-auth/register",
                json={
                    "cpf": cpf_teste,
                    "email": email_teste,
                    "senha": senha_teste
                }
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 201:
                print("✅ Conta criada com sucesso!")
            else:
                print("❌ Erro ao criar conta")
                return
        
        # 3. Login
        print("\n3️⃣ Fazendo login...")
        
        if 'email_teste' not in locals():
            email_teste = input("Digite o email: ")
        senha_teste = "senha123"
        
        response = requests.post(
            f"{BASE_URL}/api/patient-auth/login",
            json={
                "email": email_teste,
                "senha": senha_teste
            }
        )
        
        print(f"Status: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Login realizado com sucesso!")
            
            token = response_data['access_token']
            
            # 4. Acessar dados do portal
            print("\n4️⃣ Acessando portal do paciente...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 4.1 Dados do perfil
            print("\n  📋 Perfil do paciente:")
            response = requests.get(f"{BASE_URL}/api/patient-portal/me", headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                perfil = response.json()
                print(f"  Nome: {perfil.get('nome')}")
                print(f"  Email: {perfil.get('email')}")
                print(f"  CPF: {perfil.get('cpf')}")
            
            # 4.2 Estatísticas
            print("\n  📊 Estatísticas:")
            response = requests.get(f"{BASE_URL}/api/patient-portal/me/stats", headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                print(f"  Total de consultas: {stats.get('total_consultas')}")
                print(f"  Prescrições ativas: {stats.get('prescricoes_ativas')}")
                print(f"  Total de exames: {stats.get('total_exames')}")
            
            # 4.3 Prontuários
            print("\n  📄 Prontuários:")
            response = requests.get(f"{BASE_URL}/api/patient-portal/me/prontuario", headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                prontuarios = response.json()
                print(f"  Total: {prontuarios.get('total')}")
            
            # 4.4 Consultas
            print("\n  🏥 Consultas:")
            response = requests.get(f"{BASE_URL}/api/patient-portal/me/consultas", headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                consultas = response.json()
                print(f"  Total: {consultas.get('total')}")
            
            # 4.5 Prescrições
            print("\n  💊 Prescrições:")
            response = requests.get(f"{BASE_URL}/api/patient-portal/me/prescricoes", headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                prescricoes = response.json()
                print(f"  Total: {prescricoes.get('total')}")
            
            print("\n" + "=" * 60)
            print("✅ Todos os testes concluídos com sucesso!")
            
        else:
            print("❌ Erro ao fazer login")
    
    else:
        print("❌ CPF não encontrado no sistema")
        print("\n💡 Dica: Primeiro cadastre um paciente através do sistema médico,")
        print("   depois o paciente pode criar sua própria conta usando o CPF.")


if __name__ == '__main__':
    print("\n⚠️ IMPORTANTE: Ajuste o CPF_TESTE no código com um CPF real do seu banco de dados!\n")
    input("Pressione ENTER para começar os testes...")
    test_patient_auth_flow()
