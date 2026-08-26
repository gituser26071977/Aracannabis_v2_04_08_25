"""
Exemplo de uso do agente validador de profissionais

Este script demonstra como usar o agente validador para aprovar/rejeitar
cadastros de profissionais automaticamente.
"""

from services.crew_agents import criar_validador_profissionais, validar_crm_profissional
from services.crew_agents import aprovar_cadastro_profissional, rejeitar_cadastro_profissional
from services.crew_agents import gerar_senha_temporaria, enviar_email_aprovacao_profissional

# Exemplo de validação automática
def validar_profissional_exemplo(profissional_id: int):
    """
    Fluxo completo de validação de um profissional
    
    Args:
        profissional_id: ID do profissional pendente
    """
    from models import Profissional
    
    # 1. Buscar profissional
    prof = Profissional.query.get(profissional_id)
    if not prof:
        print(f"❌ Profissional {profissional_id} não encontrado")
        return
    
    print(f"🔍 Validando: {prof.nome} (CRM {prof.crm}/{prof.uf_crm})")
    
    # 2. Validar CRM via API
    validation_result = validar_crm_profissional(prof.crm, prof.uf_crm)
    print(f"📡 Resultado da validação CRM: {validation_result.get('status')}")
    
    if validation_result.get('status') == 'validated':
        # CRM validado = APROVAR
        print("✅ CRM validado com sucesso!")
        
        # 3. Gerar senha temporária
        senha_result = gerar_senha_temporaria()
        senha_temp = senha_result.get('senha_temporaria')
        print("🔑 Senha temporária gerada")
        
        # 4. Aprovar cadastro
        approval = aprovar_cadastro_profissional(profissional_id, validation_result)
        print(f"✅ {approval.get('message')}")
        
        # 5. Enviar email com credenciais
        email_result = enviar_email_aprovacao_profissional(profissional_id, senha_temp)
        print(f"📧 Email de aprovação enviado: {email_result.get('status')}")
        
        return {
            'status': 'aprovado',
            'senha_temporaria': senha_temp,
            'email_enviado': email_result.get('status') == 'sucesso'
        }
        
    elif validation_result.get('status') == 'validation_failed':
        # CRM inválido = REJEITAR
        motivo = "CRM não encontrado nos sistemas oficiais (CFM/Regional). " + \
                 "Verifique se o número está correto e se o registro está ativo."
        print(f"❌ Rejeitando cadastro: {motivo}")
        
        # 6. Rejeitar cadastro
        rejection = rejeitar_cadastro_profissional(profissional_id, motivo, validation_result)
        print(f"❌ {rejection.get('message')}")
        
        return {
            'status': 'rejeitado',
            'motivo': motivo
        }
        
    else:
        # Dados inconclusivos = REVISÃO MANUAL
        print("⚠️ Validação inconclusiva - requer revisão manual")
        
        return {
            'status': 'manual_review_required',
            'validation_data': validation_result
        }


# Exemplo de uso com o agente de IA
def exemplo_com_agente_ia():
    """
    Demonstra como o agente de IA pode executar a validação automaticamente
    """
    print("\n" + "="*60)
    print("🤖 DEMONSTRAÇÃO: Agente Validador de Profissionais")
    print("="*60 + "\n")
    
    # Criar o agente
    agente = criar_validador_profissionais()
    
    if agente:
        print(f"✅ Agente criado: {agente.role}")
        print(f"📝 Goal: {agente.goal[:100]}...")
        print(f"🛠️  Tools disponíveis: {len(agente.tools)} ferramentas")
        print("\nFerramentas:")
        for tool in agente.tools:
            print(f"  - {tool.__name__}")
    else:
        print("❌ CrewAI não disponível - rodando em modo simulado")


if __name__ == '__main__':
    exemplo_com_agente_ia()
    
    # Para testar validação real, descomente abaixo e forneça um ID válido:
    # validar_profissional_exemplo(profissional_id=1)
