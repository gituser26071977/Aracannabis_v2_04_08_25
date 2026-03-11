#!/usr/bin/env python3
"""
Script para debugar problemas com exames
"""

import requests
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5004/api"
TEST_USER = {
    "usuario": "teste_debug",
    "senha": "123456"
}

def test_login():
    """Testa o login e retorna o token"""
    print("🔐 Testando login...")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=TEST_USER)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            user = data.get('user')
            print(f"✅ Login OK! Usuário: {user.get('nome')}")
            return token, user
        else:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None, None

def test_create_numeric_exam(token, user_id, patient_id=1):
    """Testa criação de exame numérico"""
    print("\n🔢 Testando criação de exame numérico...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Usar FormData em vez de JSON
    exam_data = {
        "paciente_id": str(patient_id),
        "profissional_id": str(user_id),
        "tipo_exame": "numerico",
        "titulo": "Pressão Arterial",
        "valor": "120.0",
        "unidade": "mmHg",
        "data_exame": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.post(f"{BASE_URL}/exames", data=exam_data, headers=headers)
        
        if response.status_code == 201:
            exam = response.json()
            print(f"✅ Exame criado! ID: {exam.get('id')}")
            print(f"   Título: {exam.get('titulo')}")
            print(f"   Valor: {exam.get('valor')} {exam.get('unidade')}")
            return exam
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None

def test_list_exams(token, patient_id=1):
    """Testa listagem de exames"""
    print("\n📋 Testando listagem de exames...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/pacientes/{patient_id}/exames", headers=headers)
        
        if response.status_code == 200:
            exams = response.json()
            print(f"✅ Listagem OK! Total: {len(exams)}")
            
            for exam in exams:
                print(f"   - ID: {exam.get('id')} | {exam.get('titulo')} | {exam.get('tipo_exame')} | {exam.get('data_exame')}")
                if exam.get('valor'):
                    print(f"     Valor: {exam.get('valor')} {exam.get('unidade', '')}")
            
            return exams
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return []

def test_exam_images(token, exam_id):
    """Testa listagem de imagens"""
    print(f"\n🖼️ Testando imagens do exame {exam_id}...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/exames/{exam_id}/imagens", headers=headers)
        
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Imagens OK! Total: {len(images)}")
            for img in images:
                print(f"   - {img.get('arquivo_nome')} | {img.get('created_at')}")
            return images
        else:
            print(f"❌ Erro: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return []

def test_server_status():
    """Testa se o servidor está rodando"""
    print("🌐 Testando status do servidor...")
    
    try:
        response = requests.get(f"{BASE_URL}/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Servidor OK! Status: {data.get('status')}")
            return True
        else:
            print(f"❌ Servidor com problema: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Servidor não está rodando: {e}")
        return False

def main():
    print("🔧 DEBUG DO SISTEMA DE EXAMES")
    print("=" * 50)
    
    # Testar servidor
    if not test_server_status():
        print("\n❌ ERRO: Servidor não está rodando!")
        print("Execute: python app_cors_livre.py")
        return
    
    # Testar login
    token, user = test_login()
    if not token:
        print("\n❌ ERRO: Não foi possível fazer login!")
        return
    
    user_id = user.get('id')
    patient_id = 1
    
    # Testar criação de exame
    exam = test_create_numeric_exam(token, user_id, patient_id)
    
    # Testar listagem
    exams = test_list_exams(token, patient_id)
    
    # Testar imagens (se houver exames de arquivo)
    for exam in exams:
        if exam.get('tipo_exame') == 'arquivo':
            test_exam_images(token, exam.get('id'))
            break
    
    print("\n" + "=" * 50)
    print("🔧 DEBUG CONCLUÍDO!")
    
    if exams:
        print("\n✅ PROBLEMAS IDENTIFICADOS E SOLUÇÕES:")
        print("1. Se os gráficos não aparecem:")
        print("   - Verifique se há exames numéricos")
        print("   - Abra o console do navegador (F12) para ver erros")
        print("   - Certifique-se que Chart.js está instalado")
        
        print("\n2. Se as imagens não carregam:")
        print("   - Verifique se o diretório uploads/exames existe")
        print("   - Teste fazer upload de uma imagem primeiro")
        print("   - Verifique as permissões do diretório")
        
        print("\n3. Para testar no frontend:")
        print("   - Acesse: http://localhost:3000")
        print("   - Vá para detalhes de um paciente")
        print("   - Teste a seção de exames")
    else:
        print("\n⚠️ Nenhum exame encontrado. Crie alguns exames primeiro!")

if __name__ == "__main__":
    main()
