#!/usr/bin/env python3
"""
Script para testar o sistema de dosagens após as correções
"""

import requests
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5002/api"
TEST_USER = {
    "usuario": "admin",
    "senha": "Aracannabis@2025"
}

def test_dosagens_system():
    """Testa o sistema completo de dosagens"""
    
    print("🧪 Iniciando testes do sistema de dosagens...")
    
    # 1. Fazer login
    print("\n1. Fazendo login...")
    try:
        # Obter token CSRF
        csrf_response = requests.get(f"{BASE_URL}/csrf-token")
        csrf_token = csrf_response.json()["csrf_token"]
        
        # Fazer login
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json=TEST_USER,
            headers={"X-CSRF-Token": csrf_token}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            print("✅ Login realizado com sucesso")
        else:
            print(f"❌ Erro no login: {login_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erro na autenticação: {e}")
        return
    
    # 2. Listar pacientes para pegar um ID
    print("\n2. Listando pacientes...")
    try:
        pacientes_response = requests.get(f"{BASE_URL}/pacientes/", headers=headers)
        
        if pacientes_response.status_code == 200:
            pacientes = pacientes_response.json()["pacientes"]
            if pacientes:
                paciente_id = pacientes[0]["id"]
                print(f"✅ Paciente encontrado: ID {paciente_id}")
            else:
                print("❌ Nenhum paciente encontrado. Criando um paciente de teste...")
                # Criar paciente de teste
                novo_paciente = {
                    "nome": "Paciente Teste Dosagem",
                    "data_nascimento": "1990-01-01",
                    "cpf": "12345678901",
                    "genero": "Masculino",
                    "telefone": "(11) 99999-9999",
                    "email": "teste@dosagem.com",
                    "diagnostico": "Teste de dosagem",
                    "consentimento_lgpd": True
                }
                
                criar_response = requests.post(
                    f"{BASE_URL}/pacientes/",
                    json=novo_paciente,
                    headers=headers
                )
                
                if criar_response.status_code == 201:
                    paciente_id = criar_response.json()["paciente"]["id"]
                    print(f"✅ Paciente criado: ID {paciente_id}")
                else:
                    print(f"❌ Erro ao criar paciente: {criar_response.text}")
                    return
        else:
            print(f"❌ Erro ao listar pacientes: {pacientes_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erro ao listar pacientes: {e}")
        return
    
    # 3. Testar criação de dosagem
    print("\n3. Testando criação de dosagem...")
    try:
        nova_dosagem = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "dosagem": "Óleo Full Spectrum 10% - Teste",
            "gotas": 5,
            "frequencia_diaria": 2,
            "concentracao_cbd": 50.0,
            "concentracao_thc": 2.5,
            "concentracao_cbg": 1.0,
            "concentracao_cbn": 0.5,
            "gotas_por_ml": 30
        }
        
        criar_dosagem_response = requests.post(
            f"{BASE_URL}/dosagens/paciente/{paciente_id}",
            json=nova_dosagem,
            headers=headers
        )
        
        if criar_dosagem_response.status_code == 201:
            dosagem_criada = criar_dosagem_response.json()["dosagem"]
            dosagem_id = dosagem_criada["id"]
            print("✅ Dosagem criada com sucesso!")
            print(f"   ID: {dosagem_id}")
            print(f"   Gotas: {dosagem_criada['gotas']}")
            print(f"   Frequência: {dosagem_criada['frequencia_diaria']}x/dia")
            print(f"   Gotas por ml: {dosagem_criada['gotas_por_ml']}")
            
            # Verificar cálculo de dose diária
            if 'dose_diaria' in dosagem_criada:
                dose_diaria = dosagem_criada['dose_diaria']
                print(f"   Volume diário: {dose_diaria['ml_por_dia']} ml/dia")
                print(f"   CBD: {dose_diaria['cbd_mg']} mg/dia")
                print(f"   THC: {dose_diaria['thc_mg']} mg/dia")
                print(f"   Total canabinoides: {dose_diaria['canabinoides_totais']} mg/dia")
        else:
            print(f"❌ Erro ao criar dosagem: {criar_dosagem_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erro ao criar dosagem: {e}")
        return
    
    # 4. Testar listagem de dosagens
    print("\n4. Testando listagem de dosagens...")
    try:
        listar_response = requests.get(
            f"{BASE_URL}/dosagens/paciente/{paciente_id}",
            headers=headers
        )
        
        if listar_response.status_code == 200:
            dosagens = listar_response.json()["dosagens"]
            print(f"✅ {len(dosagens)} dosagem(ns) encontrada(s)")
            
            for dosagem in dosagens:
                print(f"   - {dosagem['dosagem']} ({dosagem['data']})")
                if 'dose_diaria' in dosagem:
                    print(f"     Volume: {dosagem['dose_diaria']['ml_por_dia']} ml/dia")
        else:
            print(f"❌ Erro ao listar dosagens: {listar_response.text}")
            return
            
    except Exception as e:
        print(f"❌ Erro ao listar dosagens: {e}")
        return
    
    # 5. Testar dados do gráfico
    print("\n5. Testando dados do gráfico...")
    try:
        grafico_response = requests.get(
            f"{BASE_URL}/dosagens/grafico/paciente/{paciente_id}",
            headers=headers
        )
        
        if grafico_response.status_code == 200:
            dados_grafico = grafico_response.json()
            print("✅ Dados do gráfico obtidos com sucesso!")
            
            if 'dados_grafico' in dados_grafico:
                dados = dados_grafico['dados_grafico']
                print(f"   Pontos no gráfico: {len(dados)}")
                
            if 'dados_canabinoides' in dados_grafico:
                canabinoides = dados_grafico['dados_canabinoides']
                print(f"   Gráficos de canabinoides disponíveis: {list(canabinoides.keys())}")
        else:
            print(f"❌ Erro ao obter dados do gráfico: {grafico_response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao obter dados do gráfico: {e}")
    
    # 6. Testar exclusão de dosagem
    print("\n6. Testando exclusão de dosagem...")
    try:
        excluir_response = requests.delete(
            f"{BASE_URL}/dosagens/{dosagem_id}",
            headers=headers
        )
        
        if excluir_response.status_code == 200:
            print("✅ Dosagem excluída com sucesso!")
        else:
            print(f"❌ Erro ao excluir dosagem: {excluir_response.text}")
            
    except Exception as e:
        print(f"❌ Erro ao excluir dosagem: {e}")
    
    print("\n🎉 Testes concluídos!")

if __name__ == "__main__":
    test_dosagens_system()
