#!/usr/bin/env python3
"""
Teste completo da funcionalidade de compartilhamento
"""

import requests
import json

# Configurações
BASE_URL = "http://localhost:5010/api"
LOGIN_DATA = {
    "usuario": "admin",
    "senha": "Aracannabis@2025"
}

def test_compartilhamento_completo():
    """Testa a funcionalidade completa de compartilhamento"""
    
    print("🧪 Teste Completo de Compartilhamento")
    print("=" * 50)
    
    # 1. Obter token CSRF e fazer login
    print("1. Fazendo login...")
    try:
        csrf_response = requests.get(f"{BASE_URL}/csrf-token")
        csrf_token = csrf_response.json().get('csrf_token')
        
        headers_login = {"X-CSRF-Token": csrf_token}
        login_response = requests.post(f"{BASE_URL}/auth/login", json=LOGIN_DATA, headers=headers_login)
        
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}", "X-CSRF-Token": csrf_token}
            print("   ✅ Login realizado com sucesso")
        else:
            print(f"   ❌ Erro no login: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    # 2. Obter dados para teste
    print("\n2. Obtendo dados para teste...")
    try:
        # Listar pacientes
        pacientes_response = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
        pacientes = pacientes_response.json().get('pacientes', [])
        
        # Listar profissionais
        profissionais_response = requests.get(f"{BASE_URL}/pacientes/profissionais", headers=headers)
        profissionais = profissionais_response.json().get('profissionais', [])
        
        if not pacientes:
            print("   ❌ Nenhum paciente encontrado")
            return
        
        if not profissionais:
            print("   ❌ Nenhum profissional encontrado para compartilhamento")
            return
        
        paciente = pacientes[0]
        profissional = profissionais[0]
        
        print(f"   ✅ Paciente: {paciente['nome']} (ID: {paciente['id']})")
        print(f"   ✅ Profissional: {profissional['nome']} (ID: {profissional['id']})")
        
    except Exception as e:
        print(f"   ❌ Erro ao obter dados: {e}")
        return
    
    # 3. Testar compartilhamento
    print("\n3. Testando compartilhamento...")
    try:
        compartilhamento_data = {
            "profissional_id": profissional['id'],
            "nivel_acesso": "leitura"
        }
        
        compartilhar_response = requests.post(
            f"{BASE_URL}/pacientes/{paciente['id']}/compartilhar",
            json=compartilhamento_data,
            headers=headers
        )
        
        print(f"   Status: {compartilhar_response.status_code}")
        
        if compartilhar_response.status_code == 200:
            print("   ✅ Compartilhamento criado com sucesso!")
            print(f"   Resposta: {compartilhar_response.json().get('message')}")
        else:
            print(f"   ❌ Erro ao compartilhar: {compartilhar_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Erro no compartilhamento: {e}")
        return
    
    # 4. Verificar compartilhamento criado
    print("\n4. Verificando compartilhamento criado...")
    try:
        compartilhamentos_response = requests.get(
            f"{BASE_URL}/pacientes/{paciente['id']}/compartilhamentos",
            headers=headers
        )
        
        if compartilhamentos_response.status_code == 200:
            compartilhamentos = compartilhamentos_response.json().get('compartilhamentos', [])
            print(f"   ✅ {len(compartilhamentos)} compartilhamentos encontrados")
            
            for comp in compartilhamentos:
                print(f"   - Com: {comp.get('profissional_nome')} (Nível: {comp.get('nivel_acesso')})")
                compartilhamento_id = comp.get('id')
        else:
            print(f"   ❌ Erro ao listar compartilhamentos: {compartilhamentos_response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar compartilhamentos: {e}")
        return
    
    # 5. Testar remoção de compartilhamento
    if compartilhamentos:
        print("\n5. Testando remoção de compartilhamento...")
        try:
            remover_response = requests.delete(
                f"{BASE_URL}/pacientes/{paciente['id']}/compartilhamentos/{compartilhamento_id}",
                headers=headers
            )
            
            print(f"   Status: {remover_response.status_code}")
            
            if remover_response.status_code == 200:
                print("   ✅ Compartilhamento removido com sucesso!")
                print(f"   Resposta: {remover_response.json().get('message')}")
            else:
                print(f"   ❌ Erro ao remover: {remover_response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro na remoção: {e}")
    
    # 6. Verificar remoção
    print("\n6. Verificando remoção...")
    try:
        compartilhamentos_response = requests.get(
            f"{BASE_URL}/pacientes/{paciente['id']}/compartilhamentos",
            headers=headers
        )
        
        if compartilhamentos_response.status_code == 200:
            compartilhamentos = compartilhamentos_response.json().get('compartilhamentos', [])
            print(f"   ✅ {len(compartilhamentos)} compartilhamentos restantes")
        else:
            print(f"   ❌ Erro ao verificar: {compartilhamentos_response.text}")
            
    except Exception as e:
        print(f"   ❌ Erro na verificação: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Teste completo concluído!")

if __name__ == "__main__":
    test_compartilhamento_completo()
