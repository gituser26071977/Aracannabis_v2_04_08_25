#!/usr/bin/env python3
"""
Teste da API de compartilhamento de pacientes
"""

import requests
import json

# Configurações
BASE_URL = "http://localhost:5010/api"
LOGIN_DATA = {
    "usuario": "admin",
    "senha": "Aracannabis@2025"
}

def test_compartilhamento_api():
    """Testa a API de compartilhamento"""
    
    print("🧪 Testando API de Compartilhamento de Pacientes")
    print("=" * 50)
    
    # 1. Obter token CSRF
    print("1. Obtendo token CSRF...")
    try:
        csrf_response = requests.get(f"{BASE_URL}/csrf-token")
        print(f"   Status: {csrf_response.status_code}")
        
        if csrf_response.status_code == 200:
            csrf_token = csrf_response.json().get('csrf_token')
            print(f"   ✅ Token CSRF obtido")
        else:
            print(f"   ❌ Erro ao obter CSRF: {csrf_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erro de conexão ao obter CSRF: {e}")
        return
    
    # 2. Fazer login
    print("\n2. Fazendo login...")
    try:
        headers_login = {"X-CSRF-Token": csrf_token}
        login_response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA, headers=headers_login)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print(f"   ✅ Login realizado com sucesso")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"   ❌ Erro no login: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erro de conexão no login: {e}")
        return
    
    # 3. Listar pacientes
    print("\n3. Listando pacientes...")
    try:
        pacientes_response = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
        print(f"   Status: {pacientes_response.status_code}")
        
        if pacientes_response.status_code == 200:
            pacientes_data = pacientes_response.json()
            pacientes = pacientes_data.get('pacientes', [])
            print(f"   ✅ {len(pacientes)} pacientes encontrados")
            
            if pacientes:
                primeiro_paciente = pacientes[0]
                print(f"   Primeiro paciente: {primeiro_paciente.get('nome')} (ID: {primeiro_paciente.get('id')})")
                print(f"   É responsável: {primeiro_paciente.get('eh_responsavel')}")
                print(f"   Nível de acesso: {primeiro_paciente.get('nivel_acesso')}")
            else:
                print("   ⚠️  Nenhum paciente encontrado")
                return
        else:
            print(f"   ❌ Erro ao listar pacientes: {pacientes_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erro de conexão ao listar pacientes: {e}")
        return
    
    # 3. Listar profissionais
    print("\n3. Listando profissionais...")
    try:
        profissionais_response = requests.get(f"{BASE_URL}/pacientes/profissionais", headers=headers)
        print(f"   Status: {profissionais_response.status_code}")
        
        if profissionais_response.status_code == 200:
            profissionais_data = profissionais_response.json()
            profissionais = profissionais_data.get('profissionais', [])
            print(f"   ✅ {len(profissionais)} profissionais encontrados")
            
            for prof in profissionais:
                print(f"   - {prof.get('nome')} (ID: {prof.get('id')}, CRM: {prof.get('crm')})")
        else:
            print(f"   ❌ Erro ao listar profissionais: {profissionais_response.text}")
    except Exception as e:
        print(f"   ❌ Erro de conexão ao listar profissionais: {e}")
    
    # 4. Testar compartilhamentos de um paciente
    if pacientes and primeiro_paciente.get('eh_responsavel'):
        paciente_id = primeiro_paciente.get('id')
        print(f"\n4. Listando compartilhamentos do paciente {paciente_id}...")
        try:
            compartilhamentos_response = requests.get(
                f"{BASE_URL}/pacientes/{paciente_id}/compartilhamentos", 
                headers=headers
            )
            print(f"   Status: {compartilhamentos_response.status_code}")
            
            if compartilhamentos_response.status_code == 200:
                compartilhamentos_data = compartilhamentos_response.json()
                compartilhamentos = compartilhamentos_data.get('compartilhamentos', [])
                print(f"   ✅ {len(compartilhamentos)} compartilhamentos encontrados")
                
                for comp in compartilhamentos:
                    print(f"   - Com: {comp.get('profissional_nome')} (Nível: {comp.get('nivel_acesso')})")
            else:
                print(f"   ❌ Erro ao listar compartilhamentos: {compartilhamentos_response.text}")
        except Exception as e:
            print(f"   ❌ Erro de conexão ao listar compartilhamentos: {e}")
    
    # 5. Testar endpoint de status
    print("\n5. Testando endpoint de status...")
    try:
        status_response = requests.get(f"{BASE_URL}/status")
        print(f"   Status: {status_response.status_code}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            print(f"   ✅ API Status: {status_data.get('status')}")
            print(f"   Versão: {status_data.get('version')}")
            print(f"   IA habilitada: {status_data.get('features', {}).get('ai_enabled')}")
        else:
            print(f"   ❌ Erro no status: {status_response.text}")
    except Exception as e:
        print(f"   ❌ Erro de conexão no status: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Teste concluído!")

if __name__ == "__main__":
    test_compartilhamento_api()
