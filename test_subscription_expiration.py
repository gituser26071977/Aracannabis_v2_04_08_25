"""
Script de teste para sistema de expiração de assinaturas

Testa:
1. Definir trial para profissional
2. Estender assinatura
3. Enviar avisos de expiração
4. Enviar propostas de assinatura
5. Revogar acesso
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_cors_livre import app
from services.subscription_expiration_service import SubscriptionExpirationService
from models import Profissional

def test_subscription_system():
    """Testa o sistema de expiração"""
    
    with app.app_context():
        print("\n" + "="*60)
        print("🧪 TESTE: Sistema de Expiração de Assinaturas")
        print("="*60 + "\n")
        
        # 1. Buscar profissional para teste
        prof = Profissional.query.first()
        if not prof:
            print("❌ Nenhum profissional encontrado no sistema!")
            return
        
        print(f"👤 Profissional de teste: {prof.nome} (ID: {prof.id})")
        print(f"   Email: {prof.email or 'Não cadastrado'}")
        print(f"   Expiração atual: {prof.data_expiracao or 'Sem data definida'}\n")
        
        # 2. Definir trial de 7 dias
        print("📅 [TESTE 1] Definindo trial de 7 dias...")
        result = SubscriptionExpirationService.set_trial_expiration(prof.id, trial_days=7)
        if result.get('success'):
            print(f"   ✅ Trial definido! Expira em: {result['expiration_date']}")
        else:
            print(f"   ⚠️  {result.get('warning') or result.get('error')}")
        
        # 3. Estender assinatura por 30 dias
        print("\n⏰ [TESTE 2] Estendendo assinatura por 30 dias...")
        result = SubscriptionExpirationService.extend_subscription(prof.id, days=30)
        if result.get('success'):
            print(f"   ✅ Assinatura estendida! Nova expiração: {result['new_expiration_date']}")
        else:
            print(f"   ❌ Erro: {result.get('error')}")
        
        # 4. Buscar profissionais expirando em breve
        print("\n🔍 [TESTE 3] Buscando profissionais expirando em 2 dias...")
        expiring = SubscriptionExpirationService.get_expiring_professionals(days_before=2)
        print(f"   📊 Encontrados: {len(expiring)} profissionais")
        
        # 5. Buscar profissionais expirados
        print("\n🔍 [TESTE 4] Buscando profissionais expirados...")
        expired = SubscriptionExpirationService.get_expired_professionals()
        print(f"   📊 Encontrados: {len(expired)} profissionais")
        
        # 6. Enviar aviso de expiração (apenas se tiver email)
        if prof.email:
            print(f"\n📧 [TESTE 5] Enviando aviso de expiração para {prof.email}...")
            result = SubscriptionExpirationService.send_expiration_warning(prof, days_remaining=2)
            if result.get('status') == 'sucesso':
                print("   ✅ Email enviado com sucesso!")
            else:
                print(f"   ❌ Erro: {result.get('error')}")
        else:
            print("\n⚠️  [TESTE 5] PULADO - Profissional sem email cadastrado")
        
        # 7. Enviar proposta de assinatura (apenas se tiver email)
        if prof.email:
            print(f"\n💼 [TESTE 6] Enviando proposta de assinatura para {prof.email}...")
            result = SubscriptionExpirationService.send_subscription_proposal(prof)
            if result.get('status') == 'sucesso':
                print("   ✅ Email enviado com sucesso!")
            else:
                print(f"   ❌ Erro: {result.get('error')}")
        else:
            print("\n⚠️  [TESTE 6] PULADO - Profissional sem email cadastrado")
        
        # 8. Processar todas as expirações
        print("\n🔄 [TESTE 7] Processando todas as expirações...")
        stats = SubscriptionExpirationService.process_expirations()
        print(f"   📊 Avisos enviados: {stats['warnings_sent']}")
        print(f"   📊 Propostas enviadas: {stats['proposals_sent']}")
        if stats['errors']:
            print(f"   ⚠️  Erros: {len(stats['errors'])}")
        
        print("\n" + "="*60)
        print("✅ Testes concluídos!")
        print("="*60 + "\n")


def test_revoke_access():
    """Testa revogação de acesso"""
    
    with app.app_context():
        prof = Profissional.query.first()
        if not prof:
            print("❌ Nenhum profissional encontrado!")
            return
        
        print(f"\n⚠️  TESTE: Revogando acesso de {prof.nome}...")
        result = SubscriptionExpirationService.revoke_access(prof.id)
        
        if result.get('success'):
            print("✅ Acesso revogado! Profissional não poderá mais fazer login.")
        else:
            print(f"❌ Erro: {result.get('error')}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--revoke':
        test_revoke_access()
    else:
        test_subscription_system()
        
        print("\n💡 Dica: Use --revoke para testar revogação de acesso")
