#!/usr/bin/env python3
"""
Teste do Sistema de Anúncios - Aracannabis
Testa todas as funcionalidades do sistema de anúncios implementado.
"""

import requests
import time
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_anuncios_api():
    """Testa a API de anúncios"""
    print("🧪 TESTANDO SISTEMA DE ANÚNCIOS")
    print("=" * 50)
    
    # Teste 1: Listar anúncios
    print("\n1. Testando listagem de anúncios...")
    try:
        response = requests.get(f"{API_URL}/anuncios")
        if response.status_code == 200:
            anuncios = response.json()
            print(f"✅ Sucesso! Encontrados {len(anuncios)} anúncios")
            
            if anuncios:
                print("\n📋 Anúncios disponíveis:")
                for i, ad in enumerate(anuncios[:3], 1):
                    print(f"   {i}. {ad['title']} - {ad['company']}")
                    print(f"      Categoria: {ad['category']} | Preço: {ad['price']}")
                    print(f"      Visualizações: {ad.get('views', 0)} | Cliques: {ad.get('clicks', 0)}")
                    print()
        else:
            print(f"❌ Erro: {response.status_code}")
            print(f"Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    # Teste 2: Listar anúncios com limite
    print("\n2. Testando listagem com limite...")
    try:
        response = requests.get(f"{API_URL}/anuncios?limite=2")
        if response.status_code == 200:
            anuncios = response.json()
            print(f"✅ Sucesso! Retornados {len(anuncios)} anúncios (limite: 2)")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    # Teste 3: Filtrar por categoria
    print("\n3. Testando filtro por categoria...")
    try:
        response = requests.get(f"{API_URL}/anuncios?categoria=Produtos")
        if response.status_code == 200:
            anuncios = response.json()
            print(f"✅ Sucesso! Encontrados {len(anuncios)} anúncios de 'Produtos'")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    # Teste 4: Registrar visualização
    print("\n4. Testando registro de visualização...")
    try:
        response = requests.post(f"{API_URL}/anuncios/1/view")
        if response.status_code == 200:
            print("✅ Visualização registrada com sucesso!")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    # Teste 5: Registrar clique
    print("\n5. Testando registro de clique...")
    try:
        response = requests.post(f"{API_URL}/anuncios/1/click")
        if response.status_code == 200:
            print("✅ Clique registrado com sucesso!")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    # Teste 6: Estatísticas
    print("\n6. Testando estatísticas...")
    try:
        response = requests.get(f"{API_URL}/anuncios/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estatísticas obtidas com sucesso!")
            print("\n📊 Estatísticas Gerais:")
            print(f"   Total de anúncios: {stats['geral']['total_anuncios']}")
            print(f"   Total de visualizações: {stats['geral']['total_visualizacoes']}")
            print(f"   Total de cliques: {stats['geral']['total_cliques']}")
            print(f"   CTR médio: {stats['geral']['ctr_medio']:.2%}")
            
            if stats['top_anuncios']:
                print("\n🏆 Top Anúncios:")
                for i, ad in enumerate(stats['top_anuncios'][:3], 1):
                    print(f"   {i}. {ad['titulo']} - {ad['cliques']} cliques")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

def test_frontend_integration():
    """Testa a integração com o frontend"""
    print("\n\n🌐 TESTANDO INTEGRAÇÃO COM FRONTEND")
    print("=" * 50)
    
    print("\n1. Verificando se o frontend está acessível...")
    try:
        response = requests.get(f"{BASE_URL}")
        if response.status_code == 200:
            print("✅ Frontend acessível!")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
    
    print("\n2. Verificando CORS...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{API_URL}/anuncios", headers=headers)
        if response.status_code in [200, 204]:
            print("✅ CORS configurado corretamente!")
        else:
            print(f"❌ Problema com CORS: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro na verificação CORS: {e}")

def simulate_user_interaction():
    """Simula interação de usuário com anúncios"""
    print("\n\n👤 SIMULANDO INTERAÇÃO DE USUÁRIO")
    print("=" * 50)
    
    print("\n1. Simulando visualizações de anúncios...")
    for i in range(1, 4):
        try:
            response = requests.post(f"{API_URL}/anuncios/{i}/view")
            if response.status_code == 200:
                print(f"✅ Visualização registrada para anúncio {i}")
            time.sleep(0.5)  # Simular tempo entre visualizações
        except Exception as e:
            print(f"❌ Erro ao registrar visualização {i}: {e}")
    
    print("\n2. Simulando cliques em anúncios...")
    for i in range(1, 3):
        try:
            response = requests.post(f"{API_URL}/anuncios/{i}/click")
            if response.status_code == 200:
                print(f"✅ Clique registrado para anúncio {i}")
            time.sleep(1)  # Simular tempo entre cliques
        except Exception as e:
            print(f"❌ Erro ao registrar clique {i}: {e}")
    
    print("\n3. Verificando estatísticas atualizadas...")
    try:
        response = requests.get(f"{API_URL}/anuncios/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estatísticas atualizadas!")
            print(f"   Visualizações: {stats['geral']['total_visualizacoes']}")
            print(f"   Cliques: {stats['geral']['total_cliques']}")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")

def test_performance():
    """Testa performance da API de anúncios"""
    print("\n\n⚡ TESTANDO PERFORMANCE")
    print("=" * 50)
    
    print("\n1. Testando tempo de resposta...")
    start_time = time.time()
    try:
        response = requests.get(f"{API_URL}/anuncios")
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            print(f"✅ Tempo de resposta: {response_time:.2f}ms")
            if response_time < 500:
                print("🚀 Performance excelente!")
            elif response_time < 1000:
                print("👍 Performance boa!")
            else:
                print("⚠️ Performance pode ser melhorada")
        else:
            print(f"❌ Erro: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n2. Testando múltiplas requisições...")
    times = []
    for i in range(5):
        start_time = time.time()
        try:
            response = requests.get(f"{API_URL}/anuncios?limite=3")
            end_time = time.time()
            if response.status_code == 200:
                times.append((end_time - start_time) * 1000)
        except Exception as e:
            print(f"❌ Erro na requisição {i+1}: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"✅ Tempo médio de {len(times)} requisições: {avg_time:.2f}ms")

def main():
    """Função principal"""
    print("🌿 TESTE COMPLETO DO SISTEMA DE ANÚNCIOS ARACANNABIS")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"URL Base: {BASE_URL}")
    
    # Executar todos os testes
    test_anuncios_api()
    test_frontend_integration()
    simulate_user_interaction()
    test_performance()
    
    print("\n\n🎉 TESTE CONCLUÍDO!")
    print("=" * 60)
    print("\n📝 PRÓXIMOS PASSOS:")
    print("1. Verificar se o frontend está rodando em http://localhost:3000")
    print("2. Testar os anúncios na interface do usuário")
    print("3. Verificar se os anúncios aparecem na página inicial")
    print("4. Testar cliques nos anúncios")
    print("5. Verificar analytics no banco de dados")
    
    print("\n💡 DICAS:")
    print("- Os anúncios aparecem apenas para usuários não logados na página inicial")
    print("- O plano 'Free' com anúncios está disponível na página de planos")
    print("- Analytics são registrados automaticamente")
    print("- Anúncios são randomizados a cada carregamento")

if __name__ == "__main__":
    main()
