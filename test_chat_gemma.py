#!/usr/bin/env python3
"""
Script de teste para o chat de IA com Gemma3:4b
Testa o chat com dados de paciente
"""

import requests
import json
import time
from pprint import pprint

BASE_URL = "http://localhost:5002/api"

def print_section(title):
    """Imprime uma seção formatada"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def login():
    """Faz login e retorna o token JWT"""
    print_section("1. FAZENDO LOGIN")

    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "admin@aracannabis.com",  # Ajuste conforme seu usuário de teste
        "password": "admin123"  # Ajuste conforme sua senha de teste
    }

    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            print(f"✓ Login bem-sucedido!")
            print(f"  Token: {token[:50]}...")
            return token
        else:
            print(f"✗ Erro no login: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Erro na requisição: {str(e)}")
        return None

def listar_pacientes(token):
    """Lista pacientes disponíveis"""
    print_section("2. LISTANDO PACIENTES")

    url = f"{BASE_URL}/pacientes"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            pacientes = result.get('pacientes', [])

            if not pacientes:
                print("⚠ Nenhum paciente encontrado")
                return None

            print(f"✓ Encontrados {len(pacientes)} paciente(s):")
            for p in pacientes[:5]:  # Mostrar apenas os 5 primeiros
                print(f"  - ID: {p['id']}, Nome: {p['nome']}")

            return pacientes[0]['id'] if pacientes else None
        else:
            print(f"✗ Erro ao listar pacientes: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Erro na requisição: {str(e)}")
        return None

def testar_chat_sem_paciente(token):
    """Testa chat sem contexto de paciente"""
    print_section("3. TESTANDO CHAT SEM PACIENTE")

    url = f"{BASE_URL}/crew-ai/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "mensagem": "Olá! Qual é o seu nome e qual sua função?",
        "contexto": {
            "source": "test_script"
        }
    }

    print(f"📤 Enviando mensagem: '{data['mensagem']}'")
    print("⏳ Aguardando resposta da IA...")

    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            resposta = result.get('resposta', {}).get('resultado', 'Sem resposta')

            print(f"✓ Resposta recebida em {elapsed_time:.2f}s:")
            print(f"\n  {resposta}\n")
            return True
        else:
            print(f"✗ Erro no chat: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Erro na requisição: {str(e)}")
        return False

def testar_chat_com_paciente(token, paciente_id):
    """Testa chat com contexto de paciente"""
    print_section("4. TESTANDO CHAT COM DADOS DE PACIENTE")

    url = f"{BASE_URL}/crew-ai/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "mensagem": "Me dê um resumo breve sobre este paciente: nome, condição e quantas evoluções ele tem registradas.",
        "paciente_id": paciente_id,
        "contexto": {
            "source": "test_script",
            "test_mode": True
        }
    }

    print(f"📤 Enviando mensagem para paciente ID {paciente_id}:")
    print(f"   '{data['mensagem']}'")
    print("⏳ Aguardando resposta da IA com dados do paciente...")

    try:
        start_time = time.time()
        response = requests.post(url, json=data, headers=headers)
        elapsed_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            resposta = result.get('resposta', {}).get('resultado', 'Sem resposta')

            print(f"✓ Resposta recebida em {elapsed_time:.2f}s:")
            print(f"\n{resposta}\n")
            return True
        else:
            print(f"✗ Erro no chat: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Erro na requisição: {str(e)}")
        return False

def verificar_config_ia(token):
    """Verifica configuração atual da IA"""
    print_section("5. VERIFICANDO CONFIGURAÇÃO DA IA")

    url = f"{BASE_URL}/ai-config/health"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Status: {result.get('status')}")
            print(f"  Provedor: {result.get('default_provider')}")
            print(f"  Modelo: {result.get('default_model')}")
            print(f"  Provedores disponíveis: {', '.join(result.get('available_providers', []))}")
            return True
        else:
            print(f"✗ Erro ao verificar configuração: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Erro na requisição: {str(e)}")
        return False

def main():
    """Função principal"""
    print("\n" + "🤖 " * 30)
    print("  TESTE DO CHAT DE IA COM GEMMA3:4B (OLLAMA LOCAL)")
    print("🤖 " * 30)

    # 1. Fazer login
    token = login()
    if not token:
        print("\n❌ Não foi possível fazer login. Verifique as credenciais.")
        return

    # 2. Verificar configuração da IA
    verificar_config_ia(token)

    # 3. Listar pacientes
    paciente_id = listar_pacientes(token)

    # 4. Testar chat sem paciente
    testar_chat_sem_paciente(token)

    # 5. Testar chat com paciente (se houver)
    if paciente_id:
        testar_chat_com_paciente(token, paciente_id)
    else:
        print("\n⚠ Pulando teste com paciente (nenhum paciente disponível)")

    print_section("RESUMO DOS TESTES")
    print("✓ Todos os testes concluídos!")
    print("\nO sistema está configurado para usar:")
    print("  - Provedor: ollama_local")
    print("  - Modelo: gemma3:4b")
    print("  - URL: http://127.0.0.1:11434")
    print("\nAcesse o frontend em: http://localhost:3000")
    print("E teste o chat interativo na interface!\n")

if __name__ == "__main__":
    main()
