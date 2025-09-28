#!/usr/bin/env python3
"""
Script para testar a API de produtos
"""

import requests
import json
from datetime import datetime

# Configurações
BASE_URL = 'http://localhost:5004/api'
HEADERS = {'Content-Type': 'application/json'}

def test_api_status():
    """Testar status da API"""
    print("🔍 Testando status da API...")
    try:
        response = requests.get(f'{BASE_URL}/status')
        if response.status_code == 200:
            print("✅ API está online")
            print(f"   Resposta: {response.json()}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return False

def test_listar_produtos():
    """Testar listagem de produtos"""
    print("\n📦 Testando listagem de produtos...")
    try:
        response = requests.get(f'{BASE_URL}/produtos', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            produtos = data.get('produtos', [])
            print(f"✅ Produtos listados com sucesso ({len(produtos)} produtos)")
            
            for i, produto in enumerate(produtos[:3], 1):  # Mostrar apenas os 3 primeiros
                print(f"   {i}. {produto['nome']} - CBD: {produto['concentracao_cbd']}mg/ml")
            
            if len(produtos) > 3:
                print(f"   ... e mais {len(produtos) - 3} produtos")
            
            return produtos
        else:
            print(f"❌ Erro ao listar produtos: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Erro ao listar produtos: {e}")
        return []

def test_criar_produto():
    """Testar criação de produto"""
    print("\n➕ Testando criação de produto...")
    
    novo_produto = {
        "nome": "Óleo CBD 25% - Teste API",
        "tipo": "oleo",
        "concentracao_cbd": 250.0,
        "concentracao_thc": 0.0,
        "concentracao_cbg": 5.0,
        "concentracao_cbn": 2.0,
        "gotas_por_ml": 30,
        "volume_ml": 30.0,
        "fabricante": "Teste Laboratório",
        "descricao": "Produto criado via teste de API"
    }
    
    try:
        response = requests.post(f'{BASE_URL}/produtos', 
                               headers=HEADERS, 
                               data=json.dumps(novo_produto))
        
        if response.status_code == 201:
            data = response.json()
            produto = data.get('produto', {})
            print("✅ Produto criado com sucesso")
            print(f"   ID: {produto.get('id')}")
            print(f"   Nome: {produto.get('nome')}")
            print(f"   CBD: {produto.get('concentracao_cbd')}mg/ml")
            return produto.get('id')
        else:
            print(f"❌ Erro ao criar produto: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao criar produto: {e}")
        return None

def test_obter_produto(produto_id):
    """Testar obtenção de produto específico"""
    print(f"\n🔍 Testando obtenção do produto ID {produto_id}...")
    try:
        response = requests.get(f'{BASE_URL}/produtos/{produto_id}', headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            produto = data.get('produto', {})
            print("✅ Produto obtido com sucesso")
            print(f"   Nome: {produto.get('nome')}")
            print(f"   Fabricante: {produto.get('fabricante')}")
            print(f"   CBD: {produto.get('concentracao_cbd')}mg/ml")
            return True
        else:
            print(f"❌ Erro ao obter produto: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao obter produto: {e}")
        return False

def test_atualizar_produto(produto_id):
    """Testar atualização de produto"""
    print(f"\n✏️ Testando atualização do produto ID {produto_id}...")
    
    dados_atualizacao = {
        "nome": "Óleo CBD 25% - Teste API (Atualizado)",
        "tipo": "oleo",
        "concentracao_cbd": 260.0,  # Aumentar concentração
        "concentracao_thc": 0.0,
        "concentracao_cbg": 5.0,
        "concentracao_cbn": 2.0,
        "gotas_por_ml": 30,
        "volume_ml": 30.0,
        "fabricante": "Teste Laboratório Atualizado",
        "descricao": "Produto atualizado via teste de API"
    }
    
    try:
        response = requests.put(f'{BASE_URL}/produtos/{produto_id}', 
                              headers=HEADERS, 
                              data=json.dumps(dados_atualizacao))
        
        if response.status_code == 200:
            data = response.json()
            produto = data.get('produto', {})
            print("✅ Produto atualizado com sucesso")
            print(f"   Nome: {produto.get('nome')}")
            print(f"   CBD: {produto.get('concentracao_cbd')}mg/ml")
            return True
        else:
            print(f"❌ Erro ao atualizar produto: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao atualizar produto: {e}")
        return False

def test_excluir_produto(produto_id):
    """Testar exclusão de produto"""
    print(f"\n🗑️ Testando exclusão do produto ID {produto_id}...")
    try:
        response = requests.delete(f'{BASE_URL}/produtos/{produto_id}', headers=HEADERS)
        if response.status_code == 200:
            print("✅ Produto excluído com sucesso")
            return True
        else:
            print(f"❌ Erro ao excluir produto: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao excluir produto: {e}")
        return False

def main():
    """Executar todos os testes"""
    print("🧪 TESTE COMPLETO DA API DE PRODUTOS")
    print("=" * 50)
    
    # Teste 1: Status da API
    if not test_api_status():
        print("\n❌ API não está funcionando. Verifique se o servidor está rodando.")
        return
    
    # Teste 2: Listar produtos
    produtos_existentes = test_listar_produtos()
    
    # Teste 3: Criar produto
    produto_id = test_criar_produto()
    if not produto_id:
        print("\n❌ Não foi possível criar produto para continuar os testes.")
        return
    
    # Teste 4: Obter produto específico
    test_obter_produto(produto_id)
    
    # Teste 5: Atualizar produto
    test_atualizar_produto(produto_id)
    
    # Teste 6: Excluir produto
    test_excluir_produto(produto_id)
    
    # Teste 7: Verificar se produto foi excluído
    print(f"\n🔍 Verificando se produto ID {produto_id} foi excluído...")
    response = requests.get(f'{BASE_URL}/produtos/{produto_id}', headers=HEADERS)
    if response.status_code == 404:
        print("✅ Produto foi excluído corretamente (404 Not Found)")
    else:
        print(f"⚠️ Produto ainda existe ou erro inesperado: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 TESTE COMPLETO FINALIZADO!")
    print(f"📊 Produtos existentes no sistema: {len(produtos_existentes)}")
    
    if len(produtos_existentes) > 0:
        print("\n📦 Produtos disponíveis:")
        for produto in produtos_existentes:
            print(f"   • {produto['nome']} (CBD: {produto['concentracao_cbd']}mg/ml)")

if __name__ == "__main__":
    main()
