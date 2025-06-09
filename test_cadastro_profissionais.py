#!/usr/bin/env python3
"""
Teste para o sistema de cadastro de profissionais
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_solicitar_cadastro():
    """Testar solicitação de cadastro"""
    print("🧪 Testando solicitação de cadastro...")
    
    url = f"{BASE_URL}/api/cadastro-profissionais/solicitar-cadastro"
    
    data = {
        "nome": "Dr. João Silva",
        "email": "joao.silva@email.com",
        "crm": "12345",
        "uf_crm": "SP",
        "telefone": "(11) 99999-9999",
        "especialidade": "Neurologia",
        "instituicao": "Hospital das Clínicas"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Solicitação de cadastro enviada com sucesso!")
            return response.json().get('solicitacao_id')
        else:
            print("❌ Erro na solicitação de cadastro")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def test_listar_solicitacoes():
    """Testar listagem de solicitações"""
    print("\n🧪 Testando listagem de solicitações...")
    
    url = f"{BASE_URL}/api/cadastro-profissionais/listar-solicitacoes"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data.get('solicitacoes', []))} solicitações encontradas")
            
            for sol in data.get('solicitacoes', []):
                print(f"   - {sol['nome']} ({sol['email']}) - Status: {sol['status']}")
                
            return data.get('solicitacoes', [])
        else:
            print("❌ Erro ao listar solicitações")
            return []
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return []

def test_aprovar_solicitacao(solicitacao_id):
    """Testar aprovação de solicitação"""
    print(f"\n🧪 Testando aprovação da solicitação {solicitacao_id}...")
    
    url = f"{BASE_URL}/api/cadastro-profissionais/aprovar-solicitacao/{solicitacao_id}"
    
    data = {
        "observacoes": "Aprovado para teste do sistema"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Solicitação aprovada com sucesso!")
            print(f"   Usuário: {result.get('usuario')}")
            print(f"   Senha temporária: {result.get('senha_temporaria')}")
            print(f"   Expira em: {result.get('data_expiracao')}")
            return True
        else:
            print("❌ Erro na aprovação")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_status_solicitacao(email):
    """Testar verificação de status"""
    print(f"\n🧪 Testando status da solicitação para {email}...")
    
    url = f"{BASE_URL}/api/cadastro-profissionais/status-solicitacao/{email}"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"   Data solicitação: {data.get('data_solicitacao')}")
            print(f"   Data aprovação: {data.get('data_aprovacao')}")
            return True
        else:
            print("❌ Erro ao verificar status")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_validacoes():
    """Testar validações de dados"""
    print("\n🧪 Testando validações...")
    
    # Teste com email inválido
    print("   Testando email inválido...")
    url = f"{BASE_URL}/api/cadastro-profissionais/solicitar-cadastro"
    data = {
        "nome": "Dr. Teste",
        "email": "email_invalido",
        "crm": "12345",
        "uf_crm": "SP"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 400:
            print("   ✅ Validação de email funcionando")
        else:
            print("   ❌ Validação de email não funcionou")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # Teste com CRM inválido
    print("   Testando CRM inválido...")
    data = {
        "nome": "Dr. Teste",
        "email": "teste@email.com",
        "crm": "123",  # Muito curto
        "uf_crm": "SP"
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 400:
            print("   ✅ Validação de CRM funcionando")
        else:
            print("   ❌ Validação de CRM não funcionou")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

def main():
    """Executar todos os testes"""
    print("🚀 Iniciando testes do sistema de cadastro de profissionais...")
    
    # Teste 1: Validações
    test_validacoes()
    
    # Teste 2: Solicitar cadastro
    solicitacao_id = test_solicitar_cadastro()
    
    # Teste 3: Listar solicitações
    solicitacoes = test_listar_solicitacoes()
    
    # Teste 4: Verificar status
    test_status_solicitacao("joao.silva@email.com")
    
    # Teste 5: Aprovar solicitação (se houver)
    if solicitacao_id:
        test_aprovar_solicitacao(solicitacao_id)
    elif solicitacoes:
        # Aprovar a primeira solicitação pendente
        for sol in solicitacoes:
            if sol['status'] == 'pendente':
                test_aprovar_solicitacao(sol['id'])
                break
    
    print("\n🎉 Testes concluídos!")

if __name__ == "__main__":
    main()
