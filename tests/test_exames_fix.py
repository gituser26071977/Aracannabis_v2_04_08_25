#!/usr/bin/env python3
"""
Script para testar o sistema de exames após as correções
"""

import requests
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5004/api"
TEST_USER = {
    "usuario": "admin",
    "senha": "123456"
}

def test_login():
    """Testa o login e retorna o token"""
    print("🔐 Testando login...")
    
    response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        user = data.get('user')
        print(f"✅ Login realizado com sucesso! Usuário: {user.get('nome')}")
        return token, user
    else:
        print(f"❌ Erro no login: {response.status_code} - {response.text}")
        return None, None

def test_create_exam(token, user_id, patient_id=1):
    """Testa a criação de exames"""
    print("\n📋 Testando criação de exames...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Teste 1: Exame de texto
    print("📝 Testando exame de texto...")
    exam_data = {
        "paciente_id": patient_id,
        "profissional_id": user_id,
        "tipo_exame": "texto",
        "titulo": "Avaliação Clínica",
        "descricao": "Paciente apresenta melhora significativa nos sintomas",
        "data_exame": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = requests.post(f"{BASE_URL}/exames", json=exam_data)
    
    if response.status_code == 201:
        exam = response.json()
        print(f"✅ Exame de texto criado com sucesso! ID: {exam.get('id')}")
        print(f"   Título: {exam.get('titulo')}")
        print(f"   Data: {exam.get('data_exame')}")
    else:
        print(f"❌ Erro ao criar exame de texto: {response.status_code} - {response.text}")
    
    # Teste 2: Exame numérico
    print("\n🔢 Testando exame numérico...")
    exam_data = {
        "paciente_id": patient_id,
        "profissional_id": user_id,
        "tipo_exame": "numerico",
        "titulo": "Pressão Arterial",
        "valor": 120.0,
        "unidade": "mmHg",
        "data_exame": datetime.now().strftime("%Y-%m-%d")
    }
    
    response = requests.post(f"{BASE_URL}/exames", json=exam_data)
    
    if response.status_code == 201:
        exam = response.json()
        print(f"✅ Exame numérico criado com sucesso! ID: {exam.get('id')}")
        print(f"   Título: {exam.get('titulo')}")
        print(f"   Valor: {exam.get('valor')} {exam.get('unidade')}")
        print(f"   Data: {exam.get('data_exame')}")
    else:
        print(f"❌ Erro ao criar exame numérico: {response.status_code} - {response.text}")

def test_list_exams(token, patient_id=1):
    """Testa a listagem de exames"""
    print(f"\n📋 Testando listagem de exames do paciente {patient_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/pacientes/{patient_id}/exames", headers=headers)
    
    if response.status_code == 200:
        exams = response.json()
        print(f"✅ Listagem realizada com sucesso! Total de exames: {len(exams)}")
        
        for exam in exams:
            print(f"   - ID: {exam.get('id')} | Título: {exam.get('titulo')} | Tipo: {exam.get('tipo_exame')} | Data: {exam.get('data_exame')}")
        
        return exams
    else:
        print(f"❌ Erro ao listar exames: {response.status_code} - {response.text}")
        return []

def test_delete_exam(token, exam_id):
    """Testa a exclusão de exame"""
    print(f"\n🗑️ Testando exclusão do exame {exam_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.delete(f"{BASE_URL}/exames/{exam_id}", headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Exame {exam_id} excluído com sucesso!")
    else:
        print(f"❌ Erro ao excluir exame: {response.status_code} - {response.text}")

def main():
    print("🧪 TESTE DO SISTEMA DE EXAMES - CORREÇÃO DE DATAS")
    print("=" * 60)
    
    # Fazer login
    token, user = test_login()
    if not token:
        print("❌ Não foi possível fazer login. Encerrando teste.")
        return
    
    user_id = user.get('id')
    
    # Testar criação de exames
    test_create_exam(token, user_id)
    
    # Testar listagem de exames
    exams = test_list_exams(token)
    
    # Testar exclusão (se houver exames)
    if exams:
        first_exam_id = exams[0].get('id')
        test_delete_exam(token, first_exam_id)
        
        # Listar novamente para confirmar exclusão
        print("\n📋 Verificando listagem após exclusão...")
        test_list_exams(token)
    
    print("\n✅ Teste concluído!")
    print("\nSe todos os testes passaram, o problema com 'invalid date' foi corrigido!")

if __name__ == "__main__":
    main()
