#!/usr/bin/env python3
"""
Teste para o sistema de email
"""

import requests

BASE_URL = "http://localhost:5010"

def test_email_connection():
    """Testar conexão SMTP"""
    print("🧪 Testando conexão SMTP...")
    
    url = f"{BASE_URL}/api/cadastro-profissionais/testar-email"
    
    try:
        response = requests.post(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Conexão SMTP funcionando!")
                print(f"   Mensagem: {data.get('message')}")
                return True
            else:
                print("❌ Erro na conexão SMTP")
                print(f"   Erro: {data.get('message')}")
                return False
        else:
            print("❌ Erro na requisição")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_approval_with_email():
    """Testar aprovação com envio de email"""
    print("\n🧪 Testando aprovação com envio de email...")
    
    # Primeiro, criar uma nova solicitação
    print("   Criando nova solicitação...")
    url_solicitar = f"{BASE_URL}/api/cadastro-profissionais/solicitar-cadastro"
    
    data_solicitacao = {
        "nome": "Dr. Teste Email",
        "email": "teste@agentesinteligentes.pro",  # Email do mesmo domínio
        "crm": "54321",
        "uf_crm": "RJ",
        "telefone": "(21) 99999-9999",
        "especialidade": "Medicina da Dor",
        "instituicao": "Clínica Teste"
    }
    
    try:
        response = requests.post(url_solicitar, json=data_solicitacao)
        
        if response.status_code == 200:
            solicitacao_data = response.json()
            solicitacao_id = solicitacao_data.get('solicitacao_id')
            print(f"   ✅ Solicitação criada: ID {solicitacao_id}")
            
            # Agora aprovar a solicitação
            print("   Aprovando solicitação...")
            url_aprovar = f"{BASE_URL}/api/cadastro-profissionais/aprovar-solicitacao/{solicitacao_id}"
            
            data_aprovacao = {
                "observacoes": "Aprovado para teste do sistema de email"
            }
            
            response_aprovacao = requests.post(url_aprovar, json=data_aprovacao)
            
            if response_aprovacao.status_code == 200:
                aprovacao_data = response_aprovacao.json()
                print("   ✅ Solicitação aprovada!")
                print(f"   Usuário: {aprovacao_data.get('usuario')}")
                print(f"   Email enviado: {aprovacao_data.get('email_enviado')}")
                
                if aprovacao_data.get('email_enviado'):
                    print("   🎉 EMAIL ENVIADO COM SUCESSO!")
                else:
                    print("   ⚠️ Falha no envio do email")
                
                return True
            else:
                print(f"   ❌ Erro na aprovação: {response_aprovacao.status_code}")
                return False
        else:
            print(f"   ❌ Erro na solicitação: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def main():
    """Executar todos os testes de email"""
    print("🚀 Iniciando testes do sistema de email...")
    
    # Teste 1: Conexão SMTP
    conexao_ok = test_email_connection()
    
    if conexao_ok:
        # Teste 2: Envio de email real
        test_approval_with_email()
    else:
        print("\n⚠️ Conexão SMTP falhou. Verifique as configurações no .env:")
        print("   - SMTP_PASSWORD deve conter a senha real")
        print("   - Verifique se as configurações da Hostinger estão corretas")
    
    print("\n📋 Configurações necessárias no .env:")
    print("   SMTP_SERVER=smtp.hostinger.com")
    print("   SMTP_PORT=587")
    print("   SMTP_USERNAME=suporte@agentesinteligentes.pro")
    print("   SMTP_PASSWORD=SUA_SENHA_REAL_AQUI")
    print("   SMTP_USE_TLS=True")
    print("   EMAIL_FROM=suporte.aracannabis@arapath.com.br")
    print("   EMAIL_FROM_NAME=Aracannabis Sistema")
    
    print("\n🎉 Testes concluídos!")

if __name__ == "__main__":
    main()
